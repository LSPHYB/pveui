"""实验课程模块 ViewSet。

路由结构：
  /api/v1/experiments/                                   → ExperimentViewSet
  /api/v1/experiments/{id}/guidebooks/                   → GuidebookViewSet (nested)
  /api/v1/experiments/{id}/publish/                      → ExperimentViewSet.publish
  /api/v1/experiments/{id}/archive/                      → ExperimentViewSet.archive
  /api/v1/experiments/{id}/export_grades/                → ExperimentViewSet.export_grades
  /api/v1/guidebooks/{id}/download/                      → GuidebookViewSet.download
  /api/v1/guidebooks/{id}/preview/                       → GuidebookViewSet.preview
  /api/v1/submissions/                                   → SubmissionViewSet
  /api/v1/submissions/my/                                → SubmissionViewSet.my
  /api/v1/submissions/{id}/submit/                       → SubmissionViewSet.submit
  /api/v1/submissions/{id}/grade/                        → SubmissionViewSet.grade
  /api/v1/submissions/{id}/return/                       → SubmissionViewSet.return_submission
  /api/v1/submissions/{id}/attachments/                  → SubmissionViewSet.upload_attachment
  /api/v1/attachments/{id}/download/                     → AttachmentViewSet.download
  /api/v1/attachments/{id}/                              → AttachmentViewSet (DELETE)
"""

import hashlib
import mimetypes
import os

from django.http import FileResponse, Http404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .models import CourseAttachment, CourseExperiment, CourseGuidebook, CourseSubmission
from apps.chat.models import AIKnowledgeIndexStatus
from .serializers import (
    CourseAttachmentSerializer,
    CourseExperimentArchiveSerializer,
    CourseExperimentCreateSerializer,
    CourseExperimentDetailSerializer,
    CourseExperimentListSerializer,
    CourseExperimentPublishSerializer,
    CourseExperimentUpdateSerializer,
    CourseGuidebookDetailSerializer,
    CourseGuidebookListSerializer,
    CourseGuidebookUploadSerializer,
    CourseSubmissionDetailSerializer,
    CourseSubmissionDraftSerializer,
    CourseSubmissionGradeSerializer,
    CourseSubmissionListSerializer,
    CourseSubmissionReturnSerializer,
    CourseSubmissionSubmitSerializer,
)


def _ok(data=None, message='success', status_code=status.HTTP_200_OK):
    """统一成功响应格式。"""
    return Response({'code': status_code, 'message': message, 'data': data}, status=status_code)


def _err(message, status_code=status.HTTP_400_BAD_REQUEST, errors=None):
    """统一错误响应格式。"""
    body = {'code': status_code, 'message': message}
    if errors:
        body['errors'] = errors
    return Response(body, status=status_code)


# ─────────────────────── ExperimentViewSet ───────────────────────

class ExperimentViewSet(viewsets.ModelViewSet):
    """实验课程 CRUD + 发布/归档/导出。

    - 教师：完整操作（创建、编辑、删除、发布、归档、导出成绩）
    - 学生：只读（只能查看 published + is_active 的实验）
    """

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'category', 'is_active', 'teacher']
    search_fields = ['title', 'course_code', 'description']
    ordering_fields = ['created_at', 'start_time', 'end_time', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = CourseExperiment.objects.filter(is_deleted=False).select_related('teacher')
        user = self.request.user
        # 学生只能看已发布且上架的实验
        if not (user.is_staff or user.is_superuser):
            qs = qs.filter(status='published', is_active=True)
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return CourseExperimentListSerializer
        if self.action in ('create',):
            return CourseExperimentCreateSerializer
        if self.action in ('update', 'partial_update'):
            return CourseExperimentUpdateSerializer
        if self.action == 'publish':
            return CourseExperimentPublishSerializer
        if self.action == 'archive':
            return CourseExperimentArchiveSerializer
        return CourseExperimentDetailSerializer

    # ── 标准 CRUD 覆盖 ──────────────────────────────────────────

    def perform_create(self, serializer):
        serializer.save(
            teacher=self.request.user,
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        """软删除。"""
        instance.is_deleted = True
        instance.updated_by = self.request.user
        instance.save(update_fields=['is_deleted', 'updated_by', 'updated_at'])

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated = self.get_paginated_response(serializer.data)
            return _ok(paginated.data)
        serializer = self.get_serializer(qs, many=True)
        return _ok(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return _ok(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # 使用 DetailSerializer 返回响应，确保包含 id 等完整字段
        detail = CourseExperimentDetailSerializer(serializer.instance, context={'request': request})
        return _ok(detail.data, message='实验创建成功', status_code=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return _ok(serializer.data, message='更新成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return _ok(message='删除成功')

    # ── 自定义 action ───────────────────────────────────────────

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        """发布实验（draft → published）。"""
        experiment = self.get_object()
        if experiment.status != 'draft':
            return _err('只有草稿状态的实验才能发布')

        # 业务校验
        if not experiment.guidebooks.filter(is_deleted=False).exists():
            return _err('发布前请至少上传一个指导书')
        if not experiment.scoring_criteria:
            return _err('发布前请设置评分标准')
        if experiment.end_time <= timezone.now():
            return _err('实验截止时间必须晚于当前时间')

        experiment.status = 'published'
        experiment.updated_by = request.user
        experiment.save(update_fields=['status', 'updated_by', 'updated_at'])
        return _ok({'id': experiment.id, 'status': experiment.status}, message='实验已发布')

    @action(detail=True, methods=['post'], url_path='archive')
    def archive(self, request, pk=None):
        """归档实验（published → archived）。"""
        experiment = self.get_object()
        if experiment.status != 'published':
            return _err('只有已发布的实验才能归档')

        experiment.status = 'archived'
        experiment.updated_by = request.user
        experiment.save(update_fields=['status', 'updated_by', 'updated_at'])
        return _ok({'id': experiment.id, 'status': experiment.status}, message='实验已归档')

    @action(detail=True, methods=['get'], url_path='export_grades')
    def export_grades(self, request, pk=None):
        """导出成绩表（Excel）。"""
        experiment = self.get_object()
        try:
            import openpyxl
        except ImportError:
            return _err('服务器未安装 openpyxl，无法导出 Excel')

        from io import BytesIO
        from django.http import HttpResponse

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = '成绩表'
        headers = ['学号', '姓名', '用户名', '提交时间', '是否迟交', '得分', '提交状态', '批改状态']
        ws.append(headers)

        submissions = experiment.submissions.filter(is_deleted=False).select_related(
            'student'
        ).order_by('student__username')

        for sub in submissions:
            student = sub.student
            ws.append([
                getattr(student, 'student_number', ''),
                student.get_full_name() or student.username,
                student.username,
                sub.submit_time.strftime('%Y-%m-%d %H:%M') if sub.submit_time else '',
                '是' if sub.is_late else '否',
                float(sub.score) if sub.score is not None else '',
                sub.get_submission_status_display(),
                sub.get_grade_status_display(),
            ])

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        filename = f"grades_{experiment.id}_{timezone.now().strftime('%Y%m%d')}.xlsx"
        response = HttpResponse(
            buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @action(detail=True, methods=['get', 'post'], url_path='guidebooks',
            parser_classes=[MultiPartParser, FormParser])
    def guidebooks(self, request, pk=None):
        """子路由：实验指导文档列表 & 上传。"""
        experiment = self.get_object()

        if request.method == 'GET':
            qs = experiment.guidebooks.filter(is_deleted=False)
            serializer = CourseGuidebookListSerializer(qs, many=True, context={'request': request})
            return _ok(serializer.data)

        # POST：上传文档
        serializer = CourseGuidebookUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        uploaded_file = data['file']

        # 文件存储路径
        upload_dir = os.path.join('experiments', str(experiment.id), 'guidebooks')
        full_dir = os.path.join('media', upload_dir)
        os.makedirs(full_dir, exist_ok=True)
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        file_name_stored = f"{timezone.now().strftime('%Y%m%d%H%M%S')}_{uploaded_file.name}"
        file_path_rel = os.path.join(upload_dir, file_name_stored)
        full_path = os.path.join('media', file_path_rel)

        # 保存文件并计算哈希
        sha256 = hashlib.sha256()
        with open(full_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
                sha256.update(chunk)

        file_type = file_ext.lstrip('.') or 'bin'
        guidebook = CourseGuidebook.objects.create(
            experiment=experiment,
            title=data['title'],
            doc_type=data['doc_type'],
            description=data.get('description', ''),
            file_name=uploaded_file.name,
            file_path=file_path_rel,
            file_size=uploaded_file.size,
            file_type=file_type,
            file_hash=sha256.hexdigest(),
            is_public=data.get('is_public', True),
            index_status='pending',
            created_by=request.user,
            updated_by=request.user,
        )

        # 初始化知识库向量化状态追踪记录
        AIKnowledgeIndexStatus.objects.create(
            guidebook=guidebook,
            experiment=experiment,
            status='pending',
            chunk_num=0,
            remark='',
        )

        # 触发异步重建任务
        import threading
        from apps.chat.tasks import rebuild_knowledge_indexes
        threading.Thread(target=rebuild_knowledge_indexes, args=([guidebook.id],)).start()

        return _ok(
            CourseGuidebookListSerializer(guidebook, context={'request': request}).data,
            message='文档上传成功，正在处理...',
            status_code=status.HTTP_201_CREATED,
        )


# ─────────────────────── GuidebookViewSet ───────────────────────

class GuidebookViewSet(viewsets.GenericViewSet):
    """指导文档独立操作：下载、预览、删除。"""

    def get_queryset(self):
        return CourseGuidebook.objects.filter(is_deleted=False)

    def get_object(self):
        try:
            return self.get_queryset().get(pk=self.kwargs['pk'])
        except CourseGuidebook.DoesNotExist:
            raise Http404

    def destroy(self, request, pk=None):
        """软删除文档（教师）。"""
        guidebook = self.get_object()
        guidebook.is_deleted = True
        guidebook.updated_by = request.user
        guidebook.save(update_fields=['is_deleted', 'updated_by', 'updated_at'])
        return _ok(message='文档已删除')

    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        """下载文档，记录下载次数。"""
        guidebook = self.get_object()
        user = request.user

        # 学生只能下载公开文档
        if not (user.is_staff or user.is_superuser) and not guidebook.is_public:
            return _err('无权下载此文档', status_code=status.HTTP_403_FORBIDDEN)

        full_path = os.path.join('media', guidebook.file_path)
        if not os.path.exists(full_path):
            return _err('文件不存在，请联系管理员', status_code=status.HTTP_404_NOT_FOUND)

        # 增加下载计数
        CourseGuidebook.objects.filter(pk=guidebook.pk).update(
            download_count=guidebook.download_count + 1
        )

        mime_type, _ = mimetypes.guess_type(guidebook.file_name)
        response = FileResponse(
            open(full_path, 'rb'),
            content_type=mime_type or 'application/octet-stream'
        )
        response['Content-Disposition'] = (
            f'attachment; filename="{guidebook.file_name}"'
        )
        return response

    @action(detail=True, methods=['get'], url_path='preview')
    def preview(self, request, pk=None):
        """预览文档（Markdown 返回文本，PDF 返回 URL，视频返回 URL）。"""
        guidebook = self.get_object()

        # 增加查看计数
        CourseGuidebook.objects.filter(pk=guidebook.pk).update(
            view_count=guidebook.view_count + 1
        )

        file_type = guidebook.file_type.lower()

        if file_type in ('md', 'markdown'):
            full_path = os.path.join('media', guidebook.file_path)
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                try:
                    import markdown
                    html = markdown.markdown(content, extensions=['extra', 'codehilite'])
                except ImportError:
                    html = f'<pre>{content}</pre>'
                return _ok({'file_type': 'md', 'content': content, 'html': html})
            except FileNotFoundError:
                return _err('文件不存在', status_code=status.HTTP_404_NOT_FOUND)

        if file_type == 'pdf':
            preview_url = f"/media/{guidebook.file_path}".replace('\\', '/')
            return _ok({'file_type': 'pdf', 'preview_url': preview_url, 'page_count': None})

        # 视频或其他直接返回媒体 URL
        media_url = f"/media/{guidebook.file_path}".replace('\\', '/')
        return _ok({'file_type': file_type, 'media_url': media_url})


# ─────────────────────── SubmissionViewSet ───────────────────────

class SubmissionViewSet(viewsets.GenericViewSet):
    """学生提交操作：查看我的提交、保存草稿、提交、附件上传。
       教师批改操作：列表、批改、退回。
    """

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['experiment', 'submission_status', 'grade_status', 'is_late']
    ordering_fields = ['submit_time', 'created_at', 'score']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = CourseSubmission.objects.filter(is_deleted=False).select_related(
            'experiment', 'student', 'graded_by'
        )
        user = self.request.user
        # 学生只能看自己的提交
        if not (user.is_staff or user.is_superuser):
            qs = qs.filter(student=user)
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return CourseSubmissionListSerializer
        if self.action == 'partial_update':
            return CourseSubmissionDraftSerializer
        if self.action == 'submit_report':
            return CourseSubmissionSubmitSerializer
        if self.action == 'grade':
            return CourseSubmissionGradeSerializer
        if self.action == 'return_submission':
            return CourseSubmissionReturnSerializer
        return CourseSubmissionDetailSerializer

    def list(self, request, *args, **kwargs):
        """获取提交列表（教师：所有实验 / 学生：自己的）。"""
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated = self.get_paginated_response(serializer.data)
            return _ok(paginated.data)
        serializer = self.get_serializer(qs, many=True)
        return _ok(serializer.data)

    def retrieve(self, request, pk=None):
        """获取提交详情。"""
        try:
            instance = self.get_queryset().get(pk=pk)
        except CourseSubmission.DoesNotExist:
            return _err('提交记录不存在', status_code=status.HTTP_404_NOT_FOUND)
        serializer = CourseSubmissionDetailSerializer(instance, context={'request': request})
        return _ok(serializer.data)

    def partial_update(self, request, pk=None):
        """保存草稿（自动保存）。"""
        try:
            instance = self.get_queryset().get(pk=pk, student=request.user)
        except CourseSubmission.DoesNotExist:
            return _err('提交记录不存在', status_code=status.HTTP_404_NOT_FOUND)

        if instance.submission_status != 'draft':
            return _err('只有草稿状态才能保存')

        serializer = CourseSubmissionDraftSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(
            last_auto_save=timezone.now(),
            updated_by=request.user,
        )
        return _ok({'last_auto_save': instance.last_auto_save}, message='保存成功')

    @action(detail=False, methods=['get'], url_path='my')
    def my(self, request):
        """获取当前用户对某实验的提交详情，不存在则自动创建草稿。"""
        experiment_id = request.query_params.get('experiment_id')
        if not experiment_id:
            return _err('请提供 experiment_id 参数')

        try:
            experiment = CourseExperiment.objects.get(
                pk=experiment_id, is_deleted=False, status='published', is_active=True
            )
        except CourseExperiment.DoesNotExist:
            return _err('实验不存在或未发布', status_code=status.HTTP_404_NOT_FOUND)

        submission, created = CourseSubmission.objects.get_or_create(
            experiment=experiment,
            student=request.user,
            is_deleted=False,
            defaults={
                'submission_status': 'draft',
                'created_by': request.user,
                'updated_by': request.user,
            }
        )
        serializer = CourseSubmissionDetailSerializer(submission, context={'request': request})
        return _ok(serializer.data)

    @action(detail=True, methods=['post'], url_path='submit')
    def submit_report(self, request, pk=None):
        """提交报告（draft → submitted）。"""
        try:
            instance = self.get_queryset().get(pk=pk, student=request.user)
        except CourseSubmission.DoesNotExist:
            return _err('提交记录不存在', status_code=status.HTTP_404_NOT_FOUND)

        if instance.submission_status != 'draft':
            return _err('只有草稿状态才能提交')

        serializer = CourseSubmissionSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not instance.report_content.strip():
            return _err('报告内容不能为空')

        now = timezone.now()
        is_late = now > instance.experiment.end_time

        instance.submission_status = 'submitted'
        instance.submit_time = now
        instance.is_late = is_late
        instance.updated_by = request.user
        instance.save(update_fields=[
            'submission_status', 'submit_time', 'is_late', 'updated_by', 'updated_at'
        ])

        return _ok({
            'id': instance.id,
            'submission_status': instance.submission_status,
            'submit_time': instance.submit_time,
            'is_late': instance.is_late,
        }, message='提交成功')

    @action(detail=True, methods=['post'], url_path='grade')
    def grade(self, request, pk=None):
        """批改提交（教师）。"""
        if not (request.user.is_staff or request.user.is_superuser):
            return _err('无权操作', status_code=status.HTTP_403_FORBIDDEN)

        try:
            instance = CourseSubmission.objects.get(pk=pk, is_deleted=False)
        except CourseSubmission.DoesNotExist:
            return _err('提交记录不存在', status_code=status.HTTP_404_NOT_FOUND)

        if instance.submission_status != 'submitted':
            return _err('只有已提交状态才能批改')

        serializer = CourseSubmissionGradeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        now = timezone.now()
        instance.score = data['score']
        instance.feedback = data.get('feedback', '')
        instance.scoring_details = data.get('scoring_details', {})
        instance.grade_status = 'completed'
        instance.submission_status = 'graded'
        instance.graded_at = now
        instance.graded_by = request.user
        instance.updated_by = request.user
        instance.save(update_fields=[
            'score', 'feedback', 'scoring_details',
            'grade_status', 'submission_status', 'graded_at', 'graded_by',
            'updated_by', 'updated_at',
        ])

        return _ok({
            'id': instance.id,
            'score': instance.score,
            'grade_status': instance.grade_status,
            'submission_status': instance.submission_status,
            'graded_at': instance.graded_at,
        }, message='批改成功')

    @action(detail=True, methods=['post'], url_path='return')
    def return_submission(self, request, pk=None):
        """退回修改（教师，submitted → draft）。"""
        if not (request.user.is_staff or request.user.is_superuser):
            return _err('无权操作', status_code=status.HTTP_403_FORBIDDEN)

        try:
            instance = CourseSubmission.objects.get(pk=pk, is_deleted=False)
        except CourseSubmission.DoesNotExist:
            return _err('提交记录不存在', status_code=status.HTTP_404_NOT_FOUND)

        if instance.submission_status != 'submitted':
            return _err('只有已提交状态才能退回')

        serializer = CourseSubmissionReturnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reason = serializer.validated_data['reason']
        # 将退回原因追加到 feedback
        instance.feedback = f'[退回原因] {reason}'
        instance.submission_status = 'draft'
        instance.submit_time = None
        instance.revision_count += 1
        instance.updated_by = request.user
        instance.save(update_fields=[
            'feedback', 'submission_status', 'submit_time', 'revision_count',
            'updated_by', 'updated_at',
        ])

        return _ok({'id': instance.id, 'submission_status': 'draft'}, message='已退回，等待学生修改')

    @action(detail=True, methods=['post'], url_path='attachments',
            parser_classes=[MultiPartParser, FormParser])
    def upload_attachment(self, request, pk=None):
        """上传附件（学生，仅草稿状态可上传）。"""
        try:
            instance = self.get_queryset().get(pk=pk, student=request.user)
        except CourseSubmission.DoesNotExist:
            return _err('提交记录不存在', status_code=status.HTTP_404_NOT_FOUND)

        if instance.submission_status != 'draft':
            return _err('只有草稿状态才能上传附件')

        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return _err('请选择要上传的文件')

        file_category = request.data.get('file_category', 'other')
        description = request.data.get('description', '')
        step_number = request.data.get('step_number')

        # 文件大小校验
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        is_video = file_ext in ('.mp4', '.avi', '.mov', '.mkv', '.webm')
        max_size = 100 * 1024 * 1024 if is_video else 10 * 1024 * 1024
        if uploaded_file.size > max_size:
            limit = '100MB' if is_video else '10MB'
            return _err(f'文件大小超过限制（{limit}）')

        # 保存文件
        upload_dir = os.path.join('submissions', str(instance.id), 'attachments')
        full_dir = os.path.join('media', upload_dir)
        os.makedirs(full_dir, exist_ok=True)
        file_name_stored = f"{timezone.now().strftime('%Y%m%d%H%M%S')}_{uploaded_file.name}"
        file_path_rel = os.path.join(upload_dir, file_name_stored)
        full_path = os.path.join('media', file_path_rel)

        with open(full_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        file_type = file_ext.lstrip('.') or 'bin'
        attachment = CourseAttachment.objects.create(
            submission=instance,
            file_name=uploaded_file.name,
            file_path=file_path_rel,
            file_size=uploaded_file.size,
            file_type=file_type,
            file_category=file_category,
            description=description,
            step_number=int(step_number) if step_number else None,
            uploaded_by=request.user,
        )

        return _ok(
            CourseAttachmentSerializer(attachment, context={'request': request}).data,
            message='附件上传成功',
            status_code=status.HTTP_201_CREATED,
        )


# ─────────────────────── AttachmentViewSet ───────────────────────

class AttachmentViewSet(viewsets.GenericViewSet):
    """附件独立操作：下载、删除。"""

    def get_queryset(self):
        return CourseAttachment.objects.filter(is_deleted=False)

    def destroy(self, request, pk=None):
        """软删除附件（只能删除自己上传的）。"""
        try:
            attachment = self.get_queryset().get(pk=pk)
        except CourseAttachment.DoesNotExist:
            return _err('附件不存在', status_code=status.HTTP_404_NOT_FOUND)

        if attachment.uploaded_by != request.user and not request.user.is_staff:
            return _err('无权删除此附件', status_code=status.HTTP_403_FORBIDDEN)

        attachment.is_deleted = True
        attachment.save(update_fields=['is_deleted'])
        return _ok(message='附件已删除')

    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        """下载附件。"""
        try:
            attachment = self.get_queryset().get(pk=pk)
        except CourseAttachment.DoesNotExist:
            return _err('附件不存在', status_code=status.HTTP_404_NOT_FOUND)

        # 只能下载自己的附件，或教师可以下载学生附件
        if (attachment.uploaded_by != request.user and
                not (request.user.is_staff or request.user.is_superuser)):
            return _err('无权下载此附件', status_code=status.HTTP_403_FORBIDDEN)

        full_path = os.path.join('media', attachment.file_path)
        if not os.path.exists(full_path):
            return _err('文件不存在', status_code=status.HTTP_404_NOT_FOUND)

        mime_type, _ = mimetypes.guess_type(attachment.file_name)
        response = FileResponse(
            open(full_path, 'rb'),
            content_type=mime_type or 'application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{attachment.file_name}"'
        return response
