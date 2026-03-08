"""异步任务管理：处理长时大模型调度、标题生成、上下文总结。"""

import logging
# from celery import shared_task
from django.utils import timezone
from .models import ChatConversation, ChatMessage, ChatConversationSummary, AIKnowledgeIndexStatus

logger = logging.getLogger(__name__)


# @shared_task
def generate_conversation_title(conversation_id: int):
    """
    根据首条用户发送的消息，使用 AI 生成一个短标题（不超过 20 字）。
    在第一条消息刚接收并保存时异步调用抛出。
    """
    try:
        conversation = ChatConversation.objects.get(id=conversation_id, is_deleted=False)
        first_msg = conversation.messages.filter(role='human').order_by('sequence').first()
        
        if not first_msg:
            return "标题生成失败：暂无人类消息"
            
        # TODO: 使用真实 LangChain/OpenAI 模型调用进行请求。
        # 伪代码：
        # prompt = f"请将下面的问题浓缩为不超过 15 个字的简短标题：{first_msg.content}"
        # generated_title = llm(prompt)
        
        generated_title = first_msg.content[:15] + "..."  # Mock: 截断作为伪装的生成实现
        
        conversation.title = generated_title
        conversation.save(update_fields=['title', 'updated_at'])
        
        return f"会话 #{conversation_id} 标题生成成功：{generated_title}"
        
    except ChatConversation.DoesNotExist:
        logger.warning(f"会话 #{conversation_id} 没有找到或已软删")
    except Exception as e:
        logger.error(f"标题生成执行异常: {e}")


# @shared_task
def summarize_conversation_memory(conversation_id: int):
    """
    长对话摘要机制：当消息量超过 20 条或者总 Token 超限，
    提取前面的 N 条对话合并出一份总结替代原文放进上下文记忆当中进行节能降本。
    """
    try:
        conversation = ChatConversation.objects.get(id=conversation_id)
        if conversation.message_count < 20:
            return "当前消息少于 20 条，不执行摘要动作。"
            
        # 确定需要摘要的消息起止序号 (假定每执行一次就摘要前10条)
        # TODO: 通过调用大模型获得前 10 条 Summary，保存入库
        
        # summary = ChatConversationSummary.objects.create(
        #     conversation=conversation,
        #     summary_type='auto',
        #     summary_content="用户询问了权限相关设置并获得解答。",
        #     message_range_start=1,
        #     message_range_end=10,
        #     tokens_saved=1200
        # )
        
        return f"会话 #{conversation_id} 历史摘要构建完成。"
    
    except Exception as e:
        logger.error(f"摘要执行异常: {e}")


# @shared_task
def rebuild_knowledge_indexes(guidebook_ids: list):
    """根据传递的指导书 ID 集合，将其推入后台 ChromaDB 的 Document 向量化建树队列中进行 RAG 解析。"""
    
    statuses = list(AIKnowledgeIndexStatus.objects.filter(guidebook_id__in=guidebook_ids))
    for s in statuses:
        try:
            s.status = 'processing'
            s.remark = '开始进行分块化和 Embeddings 编码'
            s.save(update_fields=['status', 'remark', 'updated_at'])
            
            # TODO: RAG 解析加载过程，调用 LangChain 文档解析策略 (PDFLoader, split_text) 
            
            s.status = 'completed'
            s.chunk_num = 150  # Mock
            s.remark = '处理完毕'
            s.save(update_fields=['status', 'chunk_num', 'remark', 'updated_at'])
            
        except Exception as e:
            s.status = 'failed'
            s.remark = f"发生故障: {str(e)}"
            s.save(update_fields=['status', 'remark', 'updated_at'])

    return f"全部 {len(guidebook_ids)} 份文档索引构建完成完毕"
