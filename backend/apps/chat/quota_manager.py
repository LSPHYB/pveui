"""配额与计费管理服务。"""

from decimal import Decimal
from django.utils import timezone
from .models import AIUserQuota, AIApiKey, AIUsageLog


class QuotaManager:
    """处理用户 API 调用配额以及提供商 API Key 生命周期管理。"""

    @staticmethod
    def check_user_quota(user) -> bool:
        """检查用户是否有足够的配额发起对话。
        
        策略：获取用户的配额限制，如果有 daily、monthly、total，逐一判断
        只要有一项超额即拒绝（返回 False）。
        如果在 reset_at 之内没被重置，应当判断刷新。
        """
        now = timezone.now()
        quotas = AIUserQuota.objects.filter(user=user, is_active=True)
        
        for q in quotas:
            # 配额如果是按周期的，如果已经过了重置时间，则重置已用量并更新下次重置时间
            if q.reset_at and now >= q.reset_at:
                q.tokens_used = 0
                if q.quota_type == 'daily':
                    q.reset_at = now + timezone.timedelta(days=1)
                elif q.quota_type == 'monthly':
                    q.reset_at = now + timezone.timedelta(days=30) # 简单基于 30 天
                q.save(update_fields=['tokens_used', 'reset_at'])
            
            if q.tokens_used >= q.token_limit:
                return False

        return True

    @staticmethod
    def deduct_user_quota(user, tokens: int):
        """扣减用户的 token 配额。"""
        if tokens <= 0:
            return
            
        quotas = AIUserQuota.objects.filter(user=user, is_active=True)
        for q in quotas:
            q.tokens_used += tokens
            q.save(update_fields=['tokens_used', 'updated_at'])

    @staticmethod
    def get_available_api_key(provider: str) -> AIApiKey:
        """获取当前最高优先级的有效 API Key。"""
        # 注意：这里可扩展基于 token_limit / error_count 策略的熔断或轮询轮换
        key = AIApiKey.objects.filter(
            provider=provider,
            is_active=True,
            error_count__lt=5  # 当连续错误大于5次时暂不调度
        ).order_by('-priority').first()
        
        if not key:
            raise Exception(f"没有可用的 {provider} API Key")
        return key

    @staticmethod
    def record_usage(
        user, 
        conversation, 
        message, 
        model_key: str, 
        api_key: AIApiKey, 
        prompt_tokens: int, 
        completion_tokens: int,
        latency_ms: int = None,
        cost: Decimal = Decimal('0.0'),
        status: str = 'success',
        error_msg: str = ''
    ):
        """记录具体的 Token 消耗并在 API Key 上累加上这笔花费和用量。"""
        total_tokens = prompt_tokens + completion_tokens
        
        AIUsageLog.objects.create(
            user=user,
            conversation=conversation,
            message=message,
            model_key=model_key,
            api_key=api_key,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
            latency_ms=latency_ms,
            status=status,
            error_message=error_msg
        )

        if api_key and status == 'success':
            api_key.daily_tokens_used += total_tokens
            api_key.monthly_tokens_used += total_tokens
            api_key.total_tokens_used += total_tokens
            api_key.total_cost += cost
            api_key.last_used_at = timezone.now()
            api_key.error_count = 0 
            api_key.save()
        elif api_key and status == 'error':
            api_key.error_count += 1
            api_key.last_error = error_msg
            api_key.save(update_fields=['error_count', 'last_error', 'updated_at'])

        # 同步扣减该用户的配额
        if total_tokens > 0:
            QuotaManager.deduct_user_quota(user, total_tokens)
