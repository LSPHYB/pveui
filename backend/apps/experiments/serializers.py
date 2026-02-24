"""实验课程模块序列化器。"""

from django.utils import timezone
from rest_framework import serializers

from apps.common.serializers import BaseModelSerializer

from .models import CourseAttachment, CourseExperiment, CourseGuidebook, CourseSubmission


# ─────────────────────── 内嵌用户简要序列化 ───────────────────────

class _UserBriefSerializer(serializers.Serializer):
    """内嵌的用户简要信息（只读）。"""
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    # first_name 用作"姓名"字段，与项目其他地方保持一致
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.get_full_name() or obj.username


# ─────────────────────── CourseAttachment ───────────────────────

class CourseAttachmentSerializer(BaseModelSerializer):
    """附件序列化器（读写通用）。"""

    uploaded_by_id = serializers.IntegerField(read_only=True)
    thumbnail_url = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = CourseAttachment
        fields = [
            'id', 'submission', 'file_name', 'file_path', 'file_size',
            'file_type', 'file_category', 'description', 'step_number',
            'thumbnail_path', 'thumbnail_url', 'file_url',
            'uploaded_by_id', 'created_at', 'is_deleted',
        ]
        read_only_fields = ['id', 'created_at', 'uploaded_by_id', 'file_path', 'thumbnail_path']

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail_path and request:
            path = str(obj.thumbnail_path).replace('\\', '/')
            return request.build_absolute_uri(f'/media/{path}')
        return None

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file_path and request:
            path = str(obj.file_path).replace('\\', '/')
            return request.build_absolute_uri(f'/media/{path}')
        return f'/api/v1/attachments/{obj.id}/download/'


# ─────────────────────── CourseGuidebook ───────────────────────

class CourseGuidebookListSerializer(BaseModelSerializer):
    """指导文档列表序列化器（精简字段）。"""

    download_url = serializers.SerializerMethodField()

    class Meta:
        model = CourseGuidebook
        fields = [
            'id', 'experiment', 'title', 'doc_type', 'description',
            'file_name', 'file_size', 'file_type',
            'is_indexed', 'index_status', 'is_public',
            'view_count', 'download_count', 'download_url',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'view_count', 'download_count', 'is_indexed', 'index_status']

    def get_download_url(self, obj):
        return f'/api/v1/guidebooks/{obj.id}/download/'


class CourseGuidebookDetailSerializer(BaseModelSerializer):
    """指导文档详情序列化器（含章节/关键词）。"""

    download_url = serializers.SerializerMethodField()

    class Meta:
        model = CourseGuidebook
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'created_by', 'updated_by',
            'view_count', 'download_count', 'is_indexed', 'index_status',
            'text_content', 'file_hash', 'file_path', 'file_name', 'file_size', 'file_type',
        ]

    def get_download_url(self, obj):
        return f'/api/v1/guidebooks/{obj.id}/download/'


class CourseGuidebookUploadSerializer(serializers.Serializer):
    """上传指导文档序列化器（multipart/form-data）。"""

    file = serializers.FileField(help_text='上传的文件')
    title = serializers.CharField(max_length=200, help_text='文档标题')
    doc_type = serializers.ChoiceField(
        choices=['guide', 'reference', 'video'],
        help_text='文档类型：guide-指导书, reference-参考资料, video-视频教程'
    )
    description = serializers.CharField(
        required=False, allow_blank=True, help_text='文档描述'
    )
    is_public = serializers.BooleanField(default=True, help_text='是否对学生公开')


# ─────────────────────── CourseExperiment ───────────────────────

class CourseExperimentStatsSerializer(serializers.Serializer):
    """实验提交统计（只读，内嵌在列表/详情中）。"""
    total_students = serializers.IntegerField()
    submitted_count = serializers.IntegerField()
    graded_count = serializers.IntegerField()


class CourseExperimentListSerializer(BaseModelSerializer):
    """实验列表序列化器。"""

    teacher = _UserBriefSerializer(read_only=True)
    stats = serializers.SerializerMethodField()
    my_submission = serializers.SerializerMethodField()

    class Meta:
        model = CourseExperiment
        fields = [
            'id', 'title', 'course_code', 'category', 'difficulty',
            'estimated_hours', 'start_time', 'end_time', 'total_score',
            'status', 'is_active', 'late_submission_allowed',
            'teacher', 'stats', 'my_submission', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_stats(self, obj):
        submissions = obj.submissions.filter(is_deleted=False)
        return {
            'total_students': submissions.count(),
            'submitted_count': submissions.filter(
                submission_status__in=['submitted', 'graded']
            ).count(),
            'graded_count': submissions.filter(grade_status='completed').count(),
        }

    def get_my_submission(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        try:
            from .models import CourseSubmission
            sub = obj.submissions.get(student=request.user, is_deleted=False)
            return {
                'id': sub.id,
                'submission_status': sub.submission_status,
                'submit_time': sub.submit_time,
                'is_late': sub.is_late,
                'score': sub.score,
                'grade_status': sub.grade_status,
            }
        except Exception:
            return None


class CourseExperimentDetailSerializer(BaseModelSerializer):
    """实验详情序列化器（含指导书列表和当前用户提交摘要）。"""

    teacher = _UserBriefSerializer(read_only=True)
    guidebooks = serializers.SerializerMethodField()
    my_submission = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()

    class Meta:
        model = CourseExperiment
        fields = [
            'id', 'title', 'course_code', 'description', 'objectives',
            'category', 'difficulty', 'estimated_hours',
            'start_time', 'end_time', 'late_submission_allowed', 'late_penalty_rate',
            'required_resources', 'pve_template_id',
            'total_score', 'scoring_criteria',
            'status', 'is_active',
            'teacher', 'guidebooks', 'my_submission', 'stats',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_guidebooks(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        qs = obj.guidebooks.filter(is_deleted=False)
        # 学生只看公开文档
        if user and not self._is_teacher_or_admin(user):
            qs = qs.filter(is_public=True)
        return CourseGuidebookListSerializer(qs, many=True, context=self.context).data

    def get_my_submission(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        try:
            sub = obj.submissions.get(student=request.user, is_deleted=False)
            return {
                'id': sub.id,
                'submission_status': sub.submission_status,
                'submit_time': sub.submit_time,
                'is_late': sub.is_late,
                'score': sub.score,
                'grade_status': sub.grade_status,
            }
        except CourseSubmission.DoesNotExist:
            return None

    def get_stats(self, obj):
        submissions = obj.submissions.filter(is_deleted=False)
        return {
            'total_students': submissions.count(),
            'submitted_count': submissions.filter(
                submission_status__in=['submitted', 'graded']
            ).count(),
            'graded_count': submissions.filter(grade_status='completed').count(),
        }

    @staticmethod
    def _is_teacher_or_admin(user):
        return user.is_staff or user.is_superuser


class CourseExperimentCreateSerializer(BaseModelSerializer):
    """创建实验序列化器（教师）。"""

    class Meta:
        model = CourseExperiment
        fields = [
            'title', 'course_code', 'description', 'objectives',
            'category', 'difficulty', 'estimated_hours',
            'start_time', 'end_time',
            'late_submission_allowed', 'late_penalty_rate',
            'required_resources', 'pve_template_id',
            'total_score', 'scoring_criteria',
            'status', 'is_active', 'remark',
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        start = attrs.get('start_time')
        end = attrs.get('end_time')
        if start and end and end <= start:
            raise serializers.ValidationError({'end_time': '截止时间必须晚于开始时间'})
        rate = attrs.get('late_penalty_rate', 0)
        if not (0 <= rate <= 1):
            raise serializers.ValidationError({'late_penalty_rate': '扣分比例必须在 0.00~1.00 之间'})
        return attrs


class CourseExperimentUpdateSerializer(CourseExperimentCreateSerializer):
    """更新实验序列化器（PUT/PATCH，与创建相同字段）。"""
    pass


class CourseExperimentPublishSerializer(serializers.Serializer):
    """发布实验（无请求体，仅触发业务逻辑）。"""
    pass


class CourseExperimentArchiveSerializer(serializers.Serializer):
    """归档实验（无请求体，仅触发业务逻辑）。"""
    pass


# ─────────────────────── CourseSubmission ───────────────────────

class CourseSubmissionListSerializer(BaseModelSerializer):
    """提交列表序列化器（教师批改视角）。"""

    student = _UserBriefSerializer(read_only=True)

    class Meta:
        model = CourseSubmission
        fields = [
            'id', 'experiment', 'student',
            'submission_status', 'submit_time', 'is_late',
            'grade_status', 'score', 'report_title',
            'created_at',
        ]
        read_only_fields = fields


class CourseSubmissionDetailSerializer(BaseModelSerializer):
    """提交详情序列化器（学生/教师均使用）。"""

    student = _UserBriefSerializer(read_only=True)
    graded_by = _UserBriefSerializer(read_only=True)
    attachments = serializers.SerializerMethodField()
    experiment_info = serializers.SerializerMethodField()

    class Meta:
        model = CourseSubmission
        fields = [
            'id', 'experiment', 'experiment_info', 'student',
            'submission_status', 'submit_time', 'is_late',
            'report_title', 'report_content', 'vm_info', 'operation_logs',
            'score', 'grade_status', 'graded_at', 'graded_by',
            'feedback', 'scoring_details', 'revision_count', 'last_auto_save',
            'attachments',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'student', 'submission_status', 'submit_time', 'is_late',
            'score', 'grade_status', 'graded_at', 'graded_by',
            'feedback', 'scoring_details', 'revision_count',
            'created_at', 'updated_at',
        ]

    def get_experiment_info(self, obj):
        return {'id': obj.experiment_id, 'title': obj.experiment.title}

    def get_attachments(self, obj):
        qs = obj.attachments.filter(is_deleted=False)
        return CourseAttachmentSerializer(qs, many=True, context=self.context).data


class CourseSubmissionDraftSerializer(BaseModelSerializer):
    """保存草稿序列化器（PATCH，限制可写字段）。"""

    class Meta:
        model = CourseSubmission
        fields = ['report_title', 'report_content', 'vm_info', 'operation_logs']


class CourseSubmissionSubmitSerializer(serializers.Serializer):
    """提交报告序列化器。"""
    confirm_submission = serializers.BooleanField(
        help_text='必须为 true，确认提交操作'
    )

    def validate_confirm_submission(self, value):
        if not value:
            raise serializers.ValidationError('请确认提交（confirm_submission 必须为 true）')
        return value


class CourseSubmissionGradeSerializer(serializers.Serializer):
    """批改提交序列化器（教师）。"""
    score = serializers.DecimalField(max_digits=5, decimal_places=2, help_text='总得分')
    feedback = serializers.CharField(
        required=False, allow_blank=True, help_text='教师评语'
    )
    scoring_details = serializers.DictField(
        required=False, default=dict,
        help_text='各项得分明细，格式：{"基础操作": {"score": 38, "total": 40, "comment": "good"}}'
    )

    def validate_score(self, value):
        if value < 0:
            raise serializers.ValidationError('得分不能为负数')
        return value


class CourseSubmissionReturnSerializer(serializers.Serializer):
    """退回修改序列化器（教师）。"""
    reason = serializers.CharField(help_text='退回原因，发送给学生')
