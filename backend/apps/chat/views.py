"""聊天模块视图集与 API。"""

import json
from django.utils import timezone
from django.http import StreamingHttpResponse
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import (
    AIAgentConfig,
    AIApiKey,
    AIKnowledgeIndexStatus,
    AIModelConfig,
    AIUsageLog,
    AIUserQuota,
    ChatConversation,
    ChatConversationSummary,
    ChatExperimentContext,
    ChatMessage,
)
from .serializers import (
    AIAgentConfigSerializer,
    AIAgentTestSerializer,
    AIApiKeyCreateSerializer,
    AIApiKeyListSerializer,
    AIApiKeyRotateSerializer,
    AIKnowledgeIndexStatusSerializer,
    AIKnowledgeRebuildSerializer,
    AIModelConfigSerializer,
    AIModelConfigToggleSerializer,
    AIUsageLogSerializer,
    AIUserQuotaBatchSerializer,
    AIUserQuotaSerializer,
    ChatConversationCreateSerializer,
    ChatConversationDetailSerializer,
    ChatConversationListSerializer,
    ChatMessageCreateSerializer,
    ChatMessageSerializer,
)


# ---------------------------------------------------------------------------
# 学生端 API 视图
# ---------------------------------------------------------------------------

class ChatConversationViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    用户对话会话视图集。
    提供：创建、获取详情、软删除。
    通过 action 提供 my (我的会话)、archive (归档)、messages (发送消息)。
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 用户只能查看自己未被删除的会话
        return ChatConversation.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).order_by('-updated_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return ChatConversationCreateSerializer
        elif self.action in ['retrieve', 'my']:
            return ChatConversationDetailSerializer
        return ChatConversationListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        import uuid

        conversation = ChatConversation.objects.create(
            session_id=str(uuid.uuid4()),
            title="新对话",
            user=request.user,
            context_type=data.get('context_type', 'general'),
            context_id=data.get('context_id', ''),
            context_data=data.get('context_data', {}),
            model_name=data.get('model_key', ''),
            temperature=data.get('temperature', None),
            created_by=request.user,
            updated_by=request.user
        )

        res_serializer = ChatConversationListSerializer(conversation)
        return Response({
            "code": status.HTTP_201_CREATED,
            "message": "会话创建成功",
            "data": res_serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def my(self, request):
        """获取我的会话列表。"""
        # 为了应对前端可能不带分页参数想要拿全部的诡异情况，可以加上可选的不分页处理
        page_size_str = request.query_params.get('page_size', None)
        if page_size_str and int(page_size_str) > 0:
            page = self.paginate_queryset(self.get_queryset())
            serializer = ChatConversationListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        # 默认返回所有历史会话（为了侧边栏完全展示）
        queryset = self.get_queryset()
        serializer = ChatConversationListSerializer(queryset, many=True)
        return Response({
            "count": queryset.count(),
            "results": serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        """软删除会话。"""
        instance = self.get_object()
        instance.is_deleted = True
        instance.save(update_fields=['is_deleted'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """归档会话。"""
        instance = self.get_object()
        instance.is_archived = True
        instance.save(update_fields=['is_archived'])
        return Response({"code": 200, "message": "会话已归档"})

    @action(detail=True, methods=['post'])
    def messages(self, request, pk=None):
        """
        发送消息给对话，并接收 AI 流式返回 (Server-Sent Events)。
        """
        conversation = self.get_object()
        if conversation.is_archived:
            return Response({"error": "会话已归档，无法继续发送"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ChatMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        content = serializer.validated_data['content']

        # 判断配额是否超限
        # 虽然流式没发出去，但我们可以通过返回错误事件或者HTTP错误来阻止
        from .models import AIUserQuota
        user_quota = AIUserQuota.objects.filter(user=request.user, is_active=True).first()
        is_quota_exceeded = False
        if user_quota:
            if user_quota.quota_type != 'total' and user_quota.reset_at and timezone.now() > user_quota.reset_at:
                # 配额需要重置（延迟重置逻辑，或者在此处简单放行让后续定时任务去重置）
                pass
            elif user_quota.tokens_used >= user_quota.token_limit:
                is_quota_exceeded = True

        if is_quota_exceeded:
            # 放行用户消息存储（也可以选择不存），但 AI 回复必须报错阻止
            seq = conversation.messages.count() + 1
            user_msg = ChatMessage.objects.create(
                conversation=conversation,
                role='human',
                content=content,
                sequence=seq,
                created_by=request.user,
                updated_by=request.user
            )
            conversation.message_count += 1
            conversation.last_message_at = timezone.now()
            conversation.save(update_fields=['message_count', 'last_message_at', 'updated_at'])

            def event_stream_quota_exceeded():
                yield f"event: user_message\ndata: {json.dumps({'id': user_msg.id, 'role': 'human', 'content': content, 'sequence': seq})}\n\n"
                chunk = "\n您的 AI 额度已耗尽，请联系管理员充值或等待周期重置。"
                yield f"event: content_chunk\ndata: {json.dumps({'chunk': chunk})}\n\n"
                
                # 创建一个系统的错误回复记录
                seq_ai = conversation.messages.count() + 1
                ChatMessage.objects.create(
                    conversation=conversation,
                    role='ai',
                    content=chunk,
                    sequence=seq_ai,
                    created_by=request.user,
                    updated_by=request.user
                )
                conversation.message_count += 1
                conversation.save(update_fields=['message_count'])

            response = StreamingHttpResponse(event_stream_quota_exceeded(), content_type='text/event-stream')
            response['Cache-Control'] = 'no-cache'
            return response

        # 1. 保存用户提问
        seq = conversation.messages.count() + 1
        user_msg = ChatMessage.objects.create(
            conversation=conversation,
            role='human',
            content=content,
            sequence=seq,
            created_by=request.user,
            updated_by=request.user
        )
        # 更新会话消息统计
        conversation.message_count += 1
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=['message_count', 'last_message_at', 'updated_at'])

        # TODO: 这里应该异步触发或者同步调用 LangChain 等获取生成器
        # 以下是简单的 SSE 伪代码样例
        def event_stream():
            # 推送用户消息确认
            yield f"event: user_message\ndata: {json.dumps({'id': user_msg.id, 'role': 'human', 'content': content, 'sequence': seq})}\n\n"

            # 获取关联的模型配置与 API Key
            ai_content = ""
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            messages = []
            
            try:
                model_config = AIModelConfig.objects.select_related('api_key').get(model_key=conversation.model_name)
                api_key_obj = model_config.api_key
                if not api_key_obj:
                    raise Exception("Model is missing API Key configuration.")
                
                # 提示：实际生产中应当解密 api_key_encrypted，目前的实现中是明文存的
                api_key = api_key_obj.api_key_encrypted.strip()
                base_url = api_key_obj.base_url.strip().rstrip('/') if api_key_obj.base_url else 'https://api.openai.com/v1'

                import requests
                
                # 获取匹配的 Agent 配置 (优先级查找)
                # 1. 获取当前用户的主组织
                user_org_id = None
                if hasattr(request.user, 'organization') and request.user.organization:
                    user_org_id = request.user.organization.id
                    
                if not user_org_id and hasattr(request.user, 'user_organizations'):
                    org_mgr = request.user.user_organizations
                    org_rel = org_mgr.filter(is_primary=True).first() or org_mgr.first()
                    if org_rel:
                        user_org_id = org_rel.organization_id
                
                # 确保 context_type 兜底为 'general'
                conv_context = conversation.context_type if conversation.context_type else 'general'

                # 2. 获取当前会话关联的实验ID（假设从 context_type 中提取，这里因为之前 context_type='experiment'，可能缺少具体 ID？）
                # 由于原架构没有在会话上直接绑实验ID，暂且使用前端如果能把 context_type = 'experiment_123' 传过来的话。但后端可能没存。
                # 暂时用简单的 context_type 匹配，待前端对接完善。
                # 由于用户要求的是：特定组织-特定实验，我们需要在 AI 查找上支持这2个参数
                
                # 优先级1：特定组织 + 特定实验
                # 优先级2：全局通用的组织 + 特定实验
                # 优先级3：特定组织 + 通用场景
                # 优先级4：全局通用组织 + 通用场景
                
                # 由于当前 conversation 数据模型中没有直接存储 experiment_id，我们需要查询相关的 ChatExperimentContext
                curr_exp_id = None
                latest_ctx = getattr(conversation, 'experiment_context', None)
                if latest_ctx and latest_ctx.experiment_id:
                     curr_exp_id = latest_ctx.experiment_id
                elif conversation.context_type == 'experiment' and conversation.context_id:
                     try:
                         curr_exp_id = int(conversation.context_id)
                     except ValueError:
                         pass
                     
                # 获取用户所在组织的祖先链（含自身，顺序：自身→父→祖父...）
                from apps.rbac.models import Organization
                user_org_chain = []  # 顺序：从最深子组织到根
                if user_org_id:
                    try:
                        _org = Organization.objects.get(id=user_org_id)
                        while _org:
                            user_org_chain.append(_org.id)
                            _org = Organization.objects.get(id=_org.parent_id) if _org.parent_id else None
                    except Organization.DoesNotExist:
                        if user_org_id not in user_org_chain:
                            user_org_chain.append(user_org_id)

                def pick_closest_org_agent(qs):
                    """在查询集中，按 user_org_chain 顺序取最近组织的 Agent。"""
                    agents_by_org = {a.owner_organization_id: a for a in qs}
                    for org_id in user_org_chain:
                        if org_id in agents_by_org:
                            return agents_by_org[org_id]
                    return None

                print(f"[RAG DEBUG] user_org_id={user_org_id!r}, org_chain={user_org_chain}")

                agent_config = None

                # Priority 1: 用户组织链（含父级）+ 同实验 — 精确到实验的匹配，子组织优先
                if user_org_chain and curr_exp_id:
                     agent_config = pick_closest_org_agent(
                         AIAgentConfig.objects.filter(
                             owner_organization_id__in=user_org_chain,
                             bounded_experiment_id=curr_exp_id,
                             is_active=True
                         )
                     )

                # Priority 2: 任意组织 + 同实验
                if not agent_config and curr_exp_id:
                     agent_config = AIAgentConfig.objects.filter(
                         bounded_experiment_id=curr_exp_id, is_active=True
                     ).first()

                # Priority 3: 用户组织链 + 不限实验（按 context_type 优先）
                if not agent_config and user_org_chain:
                     agent_config = (
                         pick_closest_org_agent(
                             AIAgentConfig.objects.filter(
                                 owner_organization_id__in=user_org_chain,
                                 context_type=conv_context,
                                 is_active=True
                             )
                         )
                         or pick_closest_org_agent(
                             AIAgentConfig.objects.filter(
                                 owner_organization_id__in=user_org_chain,
                                 is_active=True
                             )
                         )
                     )

                # Priority 4: 全局通用 Agent（无组织绑定、context_type 匹配）
                if not agent_config:
                     agent_config = AIAgentConfig.objects.filter(
                         owner_organization__isnull=True,
                         bounded_experiment__isnull=True,
                         context_type=conv_context,
                         is_active=True
                     ).first()

                # Priority 5: 全局 general 兜底
                if not agent_config:
                     agent_config = AIAgentConfig.objects.filter(
                         owner_organization__isnull=True,
                         bounded_experiment__isnull=True,
                         context_type='general',
                         is_active=True
                     ).first()

                # Priority 6: 最终兜底 — 忽略所有限制，取任意活跃 Agent
                if not agent_config:
                     agent_config = AIAgentConfig.objects.filter(is_active=True).first()

                print(f"[RAG DEBUG] resolved agent_config={agent_config!r}")

                # 构建上文
                sys_prompt = agent_config.system_prompt if (agent_config and agent_config.system_prompt) else ""


                
                # ======= 简易 RAG 上下文注入 =======
                # Step 1: 确定要检索哪个实验的文档
                exp_to_search = None
                agent_has_rag = agent_config and getattr(agent_config, 'enable_rag', True)

                # === DEBUG ===
                print(f"[RAG DEBUG] conv.context_type={conversation.context_type!r}, conv.context_id={conversation.context_id!r}")
                print(f"[RAG DEBUG] curr_exp_id={curr_exp_id!r}, agent={agent_config!r}, agent_has_rag={agent_has_rag}")
                # === END DEBUG ===

                if agent_has_rag:
                    exp_to_search = curr_exp_id or (agent_config.bounded_experiment_id if agent_config else None)
                elif curr_exp_id:
                    exp_to_search = curr_exp_id

                print(f"[RAG DEBUG] exp_to_search={exp_to_search!r}")

                # Step 2: 读取文档并注入 sys_prompt
                if agent_has_rag or curr_exp_id:
                    from apps.experiments.models import CourseGuidebook
                    import os
                    from django.conf import settings
                    if exp_to_search:
                        completed_guidebooks = list(CourseGuidebook.objects.filter(
                            experiment_id=exp_to_search,
                            is_deleted=False,
                            knowledge_index_status__status='completed'
                        ))
                    else:
                        completed_guidebooks = list(CourseGuidebook.objects.filter(
                            is_deleted=False,
                            knowledge_index_status__status='completed'
                        ).order_by('-updated_at')[:3])

                    print(f"[RAG DEBUG] found {len(completed_guidebooks)} guidebooks: {[gb.id for gb in completed_guidebooks]}")

                    rag_context_text = ""
                    rag_meta_lines = []
                    for gb in completed_guidebooks:
                        file_type = (gb.file_type or '').lower()
                        # 所有格式都注入元数据，让 AI 知道有哪些资料
                        rag_meta_lines.append(f"- 《{gb.title}》（类型: {gb.doc_type}，格式: {file_type}）")
                        # 对文本格式读取全文
                        if file_type in ('md', 'markdown', 'txt'):
                            full_path = os.path.join(settings.MEDIA_ROOT, gb.file_path)
                            try:
                                with open(full_path, 'r', encoding='utf-8') as f:
                                    doc_content = f.read()
                                    if len(doc_content) > 12000:
                                        doc_content = doc_content[:12000] + "\n...[内容已截断]"
                                    rag_context_text += f"\n--- 实验文档《{gb.title}》全文 ---\n{doc_content}\n"
                            except Exception as rag_err:
                                import logging as _rl
                                _rl.getLogger('django').warning(f"[RAG] Failed to read guidebook {full_path!r}: {rag_err}")

                    if rag_meta_lines or rag_context_text.strip():
                        rag_injection = "\n\n本次对话绑定的实验包含以下指导书（请依据这些内容回答实验相关问题）：\n"
                        rag_injection += "\n".join(rag_meta_lines)
                        if rag_context_text.strip():
                            rag_injection += f"\n\n以下为可读文档全文：{rag_context_text}"
                        sys_prompt += rag_injection


                # 注入系统提示词
                if sys_prompt:
                    messages.append({'role': 'system', 'content': sys_prompt})
                    
                for m in conversation.messages.order_by('sequence'):
                    messages.append({'role': 'user' if m.role == 'human' else 'assistant', 'content': m.content})

                
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                    'Accept': 'text/event-stream'
                }
                payload = {
                    "model": model_config.model_key.strip(),
                    "messages": messages,
                    "stream": True,
                    "stream_options": {"include_usage": True},
                    "temperature": float(conversation.temperature) if conversation.temperature else float(model_config.temperature_default),
                }

                # 发起真实流式请求
                resp = requests.post(f"{base_url}/chat/completions", json=payload, headers=headers, stream=True, timeout=120)

                if resp.status_code != 200:
                    try:
                        err_content = resp.json()
                        err_str = json.dumps(err_content, ensure_ascii=False)
                    except Exception:
                        err_str = resp.text
                    chunk = f"\n[后台调用模型失败: {resp.status_code} {resp.reason}] 详细信息: {err_str}"
                    ai_content += chunk
                    yield f"event: content_chunk\ndata: {json.dumps({'chunk': chunk})}\n\n"
                else:
                    # 解析 SSE 流
                    for line in resp.iter_lines():
                        if line:
                            line = line.decode('utf-8')
                            if line.startswith('data: '):
                                data_str = line[6:]
                                if data_str.strip() == '[DONE]':
                                    break
                                try:
                                    data_obj = json.loads(data_str)
                                    if 'choices' in data_obj and len(data_obj['choices']) > 0:
                                        delta = data_obj['choices'][0].get('delta', {})
                                        if 'content' in delta and delta['content']:
                                            chunk = delta['content']
                                            ai_content += chunk
                                            yield f"event: content_chunk\ndata: {json.dumps({'chunk': chunk})}\n\n"
                                    
                                    # 提取 Token 消耗（通常在流的最后几个 chunk 中传来）
                                    if 'usage' in data_obj and data_obj['usage']:
                                        usage_data = data_obj['usage']
                                        prompt_tokens = usage_data.get('prompt_tokens', 0)
                                        completion_tokens = usage_data.get('completion_tokens', 0)
                                        total_tokens = usage_data.get('total_tokens', 0)
                                except json.JSONDecodeError:
                                    pass

            except Exception as e:
                chunk = f"\n[后台调用模型失败: {str(e)}]"
                ai_content += chunk
                yield f"event: content_chunk\ndata: {json.dumps({'chunk': chunk})}\n\n"

            # 记录并推送 AI 最终完整回复
            seq_ai = conversation.messages.count() + 1
            ai_msg = ChatMessage.objects.create(
                conversation=conversation,
                role='ai',
                content=ai_content,
                sequence=seq_ai,
                created_by=request.user,
                updated_by=request.user
            )
            conversation.message_count += 1
            conversation.last_message_at = timezone.now()
            conversation.save(update_fields=['message_count', 'last_message_at', 'updated_at'])

            # 粗略估算 Token (适用于部分不返回 usage 数据的模型)
            if total_tokens <= 0:
                estimated_prompt_len = sum(len(m.get('content', '')) for m in messages)
                estimated_comp_len = len(ai_content)
                prompt_tokens = int(estimated_prompt_len * 1.2)
                completion_tokens = int(estimated_comp_len * 1.25)
                total_tokens = prompt_tokens + completion_tokens

            # 始终记录 Token 消耗到日志与配额管理
            try:
                from django.db import transaction
                with transaction.atomic():
                    # 记录日志
                    AIUsageLog.objects.create(
                        user=request.user,
                        conversation=conversation,
                        message=ai_msg,
                        model_key=model_config.model_key,
                        api_key=api_key_obj,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        status='success'
                    )
                    # 扣减用户配额
                    user_quotas = AIUserQuota.objects.filter(user=request.user, is_active=True)
                    for quota in user_quotas:
                        quota.tokens_used += total_tokens
                        quota.save(update_fields=['tokens_used'])
                    # 增加通道全局统计
                    if api_key_obj:
                        api_key_obj.total_tokens_used += total_tokens
                        api_key_obj.save(update_fields=['total_tokens_used'])
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"Failed to record token usage: {e}")

            yield f"event: assistant_message\ndata: {json.dumps({'id': ai_msg.id, 'role': 'ai', 'content': ai_content, 'sequence': seq_ai})}\n\n"

        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        return response


# ---------------------------------------------------------------------------
# 管理端 API 视图集
# 注意：生产环境中需要添加 IsAdminUser 权限，此处简化为 IsAuthenticated
# ---------------------------------------------------------------------------

class AdminAIModelConfigViewSet(viewsets.ModelViewSet):
    """
    管理端：AI模型配置管理。
    """
    queryset = AIModelConfig.objects.all().order_by('-created_at')
    serializer_class = AIModelConfigSerializer
    permission_classes = [IsAuthenticated] # 建议替换为 IsAdminUser

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        instance = self.get_object()
        serializer = AIModelConfigToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.is_enabled = serializer.validated_data['is_enabled']
        instance.save(update_fields=['is_enabled', 'updated_at'])
        return Response({"code": 200, "message": "状态切换成功"})

    @action(detail=True, methods=['post'], url_path='test-connection')
    def test_connection(self, request, pk=None):
        """测试模型连通性"""
        instance = self.get_object()
        api_key_obj = instance.api_key
        if not api_key_obj:
            return Response({"code": 400, "message": "该模型未绑定 API Key"})
            
        api_key = api_key_obj.api_key_encrypted.strip()
        base_url = api_key_obj.base_url.strip().rstrip('/') if api_key_obj.base_url else 'https://api.openai.com/v1'
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            "model": instance.model_key.strip(),
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 5
        }
        
        try:
            import requests
            resp = requests.post(f"{base_url}/chat/completions", json=payload, headers=headers, timeout=15)
            if resp.status_code == 200:
                return Response({"code": 200, "message": "连通性测试成功 (HTTP 200)"})
            else:
                return Response({"code": 400, "message": f"连接失败: HTTP {resp.status_code} - {resp.text}"})
        except Exception as e:
            return Response({"code": 400, "message": f"连接异常: {str(e)}"})


class AdminAIApiKeyViewSet(viewsets.ModelViewSet):
    """
    管理端：API Key 管理。
    """
    queryset = AIApiKey.objects.all().order_by('-priority', 'provider')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return AIApiKeyCreateSerializer
        return AIApiKeyListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        # 服务层加密存储逻辑
        # encrypted_key = encrypt(data['api_key'])
        encrypted_key = data['api_key'] # 暂存明文演示
        
        AIApiKey.objects.create(
            provider=data['provider'],
            key_name=data['key_name'],
            base_url=data.get('base_url', ''),
            api_key_encrypted=encrypted_key,
            priority=data.get('priority', 0),
            daily_token_limit=data.get('daily_token_limit'),
            monthly_token_limit=data.get('monthly_token_limit'),
            created_by=request.user,
            updated_by=request.user
        )
        return Response({"code": 200, "message": "API Key 保存成功"}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def usage(self, request, pk=None):
        # instance = self.get_object()
        # TODO: 从 AIUsageLog 查询真实用量，简单 MOCK
        return Response({
            "code": 200,
            "data": {
                "daily_usage": [{"date": timezone.now().date(), "tokens": 0}],
                "monthly_total": 0
            }
        })

    @action(detail=True, methods=['post'])
    def rotate(self, request, pk=None):
        instance = self.get_object()
        serializer = AIApiKeyRotateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_key = serializer.validated_data['new_api_key']
        # 1. 禁用旧 Key
        instance.is_active = False
        instance.save(update_fields=['is_active', 'updated_at'])
        # 2. 创建新 Key
        AIApiKey.objects.create(
            provider=instance.provider,
            key_name=instance.key_name + " (Rotated)",
            api_key_encrypted=new_key,  # 需加密
            priority=instance.priority,
            created_by=request.user,
            updated_by=request.user
        )
        return Response({"code": 200, "message": "API Key 轮换成功"})

    @action(detail=True, methods=['post'])
    def disable(self, request, pk=None):
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=['is_active', 'updated_at'])
        return Response({"code": 200, "message": "已禁用"})


class AdminAIUserQuotaViewSet(viewsets.ModelViewSet):
    """
    管理端：用户配额管理。
    """
    queryset = AIUserQuota.objects.all().order_by('-created_at')
    serializer_class = AIUserQuotaSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(
            created_by=user,
            updated_by=user,
            owner_organization=getattr(user, 'organization', None)
        )

    def perform_update(self, serializer):
        user = self.request.user
        serializer.save(
            updated_by=user
        )

    @action(detail=False, methods=['post'], url_path='batch-set')
    def batch_set(self, request):
        serializer = AIUserQuotaBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        user = request.user
        org = getattr(user, 'organization', None)
        
        for u_id in data['user_ids']:
            defaults = {
                'token_limit': data['token_limit'],
                'reset_at': data.get('reset_at'),
                'updated_by': user
            }
            # 如果是新建的，update_or_create 的 defaults 里面如果有 created_by 会影响更新逻辑
            # 但是因为 defaults 主要是用来 update 的，我们可以手动提取
            obj = AIUserQuota.objects.filter(user_id=u_id, quota_type=data['quota_type']).first()
            if obj:
                for k, v in defaults.items():
                    setattr(obj, k, v)
                obj.save()
            else:
                defaults['created_by'] = user
                defaults['owner_organization'] = org
                AIUserQuota.objects.create(
                    user_id=u_id, 
                    quota_type=data['quota_type'], 
                    **defaults
                )
        return Response({"code": 200, "message": f"成功批量下发配额给 {len(data['user_ids'])} 名用户"})

    @action(detail=True, methods=['post'])
    def reset(self, request, pk=None):
        instance = self.get_object()
        instance.tokens_used = 0
        instance.save(update_fields=['tokens_used', 'updated_at'])
        return Response({"code": 200, "message": "成功重置限额"})


class AdminAIAgentConfigViewSet(viewsets.ModelViewSet):
    """
    管理端：智能体配置。
    """
    queryset = AIAgentConfig.objects.all().order_by('-created_at')
    serializer_class = AIAgentConfigSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        # instance = self.get_object()
        serializer = AIAgentTestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # TODO: 调研 LangChain / OpenAI 测试
        return Response({
            "code": 200,
            "data": {
                "answer": "这是沙盒测试自动生成的回复示例。",
                "latency_ms": 1200
            }
        })


class AdminAIKnowledgeIndexViewSet(viewsets.ModelViewSet):
    """
    管理端：知识库状态。
    """
    queryset = AIKnowledgeIndexStatus.objects.all().order_by('-created_at')
    serializer_class = AIKnowledgeIndexStatusSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def rebuild(self, request):
        serializer = AIKnowledgeRebuildSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        import threading
        from apps.chat.tasks import rebuild_knowledge_indexes
        
        guidebook_ids = serializer.validated_data.get('guidebook_ids', [])
        if guidebook_ids:
            threading.Thread(target=rebuild_knowledge_indexes, args=(guidebook_ids,)).start()
        return Response({
            "code": 200,
            "message": "已触发重建任务",
            "data": serializer.validated_data
        })


# ---------------------------------------------------------------------------
# 用户端 - 单独 APIView（非 ViewSet）
# ---------------------------------------------------------------------------

from rest_framework.views import APIView


class AvailableModelsView(APIView):
    """
    用户端：获取当前用户可用的 AI 模型列表。
    GET /api/v1/chat/models/available/
    只返回 is_enabled=True 且用户角色在 allowed_roles 内的模型。
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # 获取用户角色列表（与 RBAC 系统一致）
        from apps.rbac.models import Role
        user_roles = list(
            Role.objects.filter(user_roles__user=user).values_list('code', flat=True)
        )

        qs = AIModelConfig.objects.filter(is_enabled=True, is_deleted=False).order_by('-is_default', 'model_name')
        result = []
        for model in qs:
            # allowed_roles 为 None / [] 时视为全体可用
            allowed = model.allowed_roles
            if allowed and not any(r in allowed for r in user_roles):
                if not user.is_superuser:
                    continue
            result.append({
                "model_key": model.model_key,
                "model_name": model.model_name,
                "provider": model.api_key.provider if model.api_key else 'custom',
                "model_type": model.model_type,
                "max_tokens": model.max_tokens,
                "temperature_default": float(model.temperature_default) if model.temperature_default else 0.7,
                "is_default": model.is_default,
                "requires_permission": bool(allowed),
            })

        return Response(result)


class MyQuotaView(APIView):
    """
    用户端：查看当前用户的配额使用情况。
    GET /api/v1/chat/my-quota/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        quotas = AIUserQuota.objects.filter(user=user, is_active=True)
        result = {}
        for q in quotas:
            result[q.quota_type] = {
                "limit": q.token_limit,
                "used": q.tokens_used,
                "reset_at": q.reset_at.isoformat() if q.reset_at else None,
            }

        # 如果没有配额记录，返回无限制标识
        if not result:
            result = {
                "daily": {"limit": None, "used": 0, "reset_at": None},
                "monthly": {"limit": None, "used": 0, "reset_at": None},
            }

        return Response({"code": 200, "data": result})

# ---------------------------------------------------------------------------
# 管理端分析数据图表 API (Dashboard Stats)
# ---------------------------------------------------------------------------

from django.db.models import Sum, Count
from datetime import timedelta
from django.db.models.functions import TruncDate

class AdminAIStatsOverviewView(APIView):
    """
    管理端：AI 模块概览统计数据。
    GET /api/v1/chat/admin/ai/stats/overview/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # 1. Total tokens (all time)
        total_tokens = AIUsageLog.objects.aggregate(total=Sum('total_tokens'))['total'] or 0

        # 2. Total requests (all time)
        total_requests = AIUsageLog.objects.count()

        # 3. Total cost (all time) USD
        total_cost = AIUsageLog.objects.aggregate(total=Sum('cost'))['total'] or 0.00

        # 4. Active users this month
        active_users = AIUsageLog.objects.filter(created_at__gte=start_of_month).values('user_id').distinct().count()

        # 5. API Key status
        total_keys = AIApiKey.objects.count()
        active_keys = AIApiKey.objects.filter(is_active=True, error_count=0).count()
        error_keys = AIApiKey.objects.filter(error_count__gt=0).count()
        if error_keys == 0:
            error_keys = AIApiKey.objects.filter(is_active=False).count()
            
        # 6. Model distribution (all time)
        distribution = []
        model_stats = AIUsageLog.objects.values('model_key').annotate(
            used=Sum('total_tokens'), 
            cost=Sum('cost')
        ).order_by('-used')
        
        for stat in model_stats:
            percent = round((stat['used'] / total_tokens) * 100, 1) if total_tokens > 0 else 0
            distribution.append({
                "model_key": stat['model_key'],
                "usage_percent": percent,
                "total_cost": float(stat['cost'] or 0)
            })

        return Response({
            "code": 200,
            "data": {
                "total_tokens": total_tokens,
                "total_requests": total_requests,
                "total_cost_usd": float(total_cost),
                "active_users": active_users,
                "api_key_status": {
                    "total": total_keys,
                    "active": active_keys,
                    "error": error_keys
                },
                "model_distribution": distribution
            }
        })

class AdminAIUsageTrendView(APIView):
    """
    管理端：AI 使用趋势数据（近30天）。
    GET /api/v1/chat/admin/ai/stats/usage-trend/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        
        logs = AIUsageLog.objects.filter(created_at__gte=thirty_days_ago)
        
        daily_stats = logs.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            tokens=Sum('total_tokens'),
            requests=Count('id'),
            cost=Sum('cost')
        ).order_by('date')
        
        stats_dict = {item['date'].strftime('%Y-%m-%d'): item for item in daily_stats if item['date']}
        
        data_points = []
        for i in range(29, -1, -1):
            d = (now - timedelta(days=i)).strftime('%Y-%m-%d')
            if d in stats_dict:
                data_points.append({
                    "date": d,
                    "tokens": stats_dict[d]['tokens'] or 0,
                    "requests": stats_dict[d]['requests'] or 0,
                    "cost": float(stats_dict[d]['cost'] or 0)
                })
            else:
                data_points.append({
                    "date": d,
                    "tokens": 0,
                    "requests": 0,
                    "cost": 0.0
                })
                
        return Response({
            "code": 200,
            "data": {
                "data_points": data_points
            }
        })

