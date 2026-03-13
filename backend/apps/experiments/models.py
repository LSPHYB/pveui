"""实验课程模块模型：实验课程、指导文档、学生提交、附件管理。"""

from django.conf import settings
from django.db import models

from apps.common.models import BaseAuditModel


class CourseExperiment(BaseAuditModel):
    """实验课程实体：代表一次完整的实验任务。"""

    CATEGORY_CHOICES = [
        ('linux', 'Linux'),
        ('network', '网络'),
        ('virtualization', '虚拟化'),
        ('security', '安全'),
        ('other', '其他'),
    ]

    DIFFICULTY_CHOICES = [
        ('easy', '简单'),
        ('medium', '中等'),
        ('hard', '困难'),
    ]

    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('published', '已发布'),
        ('archived', '已归档'),
    ]

    title = models.CharField(max_length=200, verbose_name='实验标题')
    course_code = models.CharField(
        max_length=50, blank=True, default='', verbose_name='课程代码',
        help_text='如 CS101-EXP02'
    )
    description = models.TextField(blank=True, default='', verbose_name='实验描述')
    objectives = models.JSONField(
        default=list, blank=True, verbose_name='实验目标',
        help_text='列表格式，如 ["掌握useradd命令", "理解文件权限"]'
    )
    category = models.CharField(
        max_length=50, choices=CATEGORY_CHOICES, verbose_name='分类'
    )
    difficulty = models.CharField(
        max_length=20, choices=DIFFICULTY_CHOICES, blank=True, default='',
        verbose_name='难度'
    )
    estimated_hours = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True,
        verbose_name='预计完成时长（小时）'
    )
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(verbose_name='截止时间')
    late_submission_allowed = models.BooleanField(
        default=False, verbose_name='允许迟交'
    )
    late_penalty_rate = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.00,
        verbose_name='迟交扣分比例', help_text='范围 0.00~1.00，如 0.10 表示扣10%'
    )
    required_resources = models.JSONField(
        default=dict, blank=True, verbose_name='所需资源配置',
        help_text='如 {"cpu": 2, "memory": 2048, "disk": 20}'
    )
    pve_template_id = models.CharField(
        max_length=100, blank=True, default='', verbose_name='推荐PVE模板ID'
    )
    total_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='总分'
    )
    scoring_criteria = models.JSONField(
        default=dict, blank=True, verbose_name='评分标准',
        help_text='如 {"基础操作": 40, "权限设置": 30}'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态'
    )
    is_active = models.BooleanField(default=True, verbose_name='是否上架')
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='teaching_experiments',
        verbose_name='任课教师',
    )

    class Meta:
        verbose_name = '实验课程'
        verbose_name_plural = '实验课程'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'start_time'], name='idx_exp_status_time'),
            models.Index(fields=['category', 'is_active'], name='idx_exp_category'),
            models.Index(fields=['teacher', 'created_at'], name='idx_exp_teacher'),
        ]

    def __str__(self) -> str:
        return f"[{self.get_status_display()}] {self.title}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.end_time and self.start_time and self.end_time <= self.start_time:
            raise ValidationError('截止时间必须晚于开始时间')
        if self.late_penalty_rate is not None:
            if not (0.00 <= self.late_penalty_rate <= 1.00):
                raise ValidationError('迟交扣分比例必须在 0.00~1.00 之间')


class CourseGuidebook(BaseAuditModel):
    """实验指导文档实体：教师上传的指导书、参考资料、视频教程等。"""

    DOC_TYPE_CHOICES = [
        ('guide', '实验指导书'),
        ('reference', '参考资料'),
        ('video', '视频教程'),
    ]

    INDEX_STATUS_CHOICES = [
        ('pending', '等待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]

    experiment = models.ForeignKey(
        CourseExperiment,
        on_delete=models.CASCADE,
        related_name='guidebooks',
        verbose_name='所属实验',
    )
    title = models.CharField(max_length=200, verbose_name='文档标题')
    doc_type = models.CharField(
        max_length=20, choices=DOC_TYPE_CHOICES, verbose_name='文档类型'
    )
    description = models.TextField(blank=True, default='', verbose_name='文档描述')
    file_name = models.CharField(max_length=255, verbose_name='原始文件名')
    file_path = models.CharField(max_length=500, verbose_name='文件存储路径')
    file_size = models.BigIntegerField(verbose_name='文件大小（字节）')
    file_type = models.CharField(
        max_length=50, verbose_name='文件类型', help_text='如 pdf / docx / md / mp4'
    )
    file_hash = models.CharField(
        max_length=64, blank=True, default='', verbose_name='文件SHA256哈希'
    )
    text_content = models.TextField(
        blank=True, default='', verbose_name='提取的文本内容（AI检索用）'
    )
    is_indexed = models.BooleanField(default=False, verbose_name='是否已建立AI索引')
    index_status = models.CharField(
        max_length=20, choices=INDEX_STATUS_CHOICES, default='pending',
        verbose_name='索引状态'
    )
    sections = models.JSONField(
        default=list, blank=True, verbose_name='章节结构',
        help_text='如 [{"title": "实验目的", "page": 1}]'
    )
    keywords = models.JSONField(
        default=list, blank=True, verbose_name='关键词列表'
    )
    is_public = models.BooleanField(default=True, verbose_name='是否对学生公开')
    view_count = models.IntegerField(default=0, verbose_name='查看次数')
    download_count = models.IntegerField(default=0, verbose_name='下载次数')

    class Meta:
        verbose_name = '实验指导文档'
        verbose_name_plural = '实验指导文档'
        ordering = ['doc_type', 'created_at']
        indexes = [
            models.Index(fields=['experiment', 'doc_type'], name='idx_guidebook_exp'),
            models.Index(fields=['is_indexed', 'index_status'], name='idx_guidebook_indexed'),
        ]

    def __str__(self) -> str:
        return f"{self.experiment.title} - {self.title}"


class CourseSubmission(BaseAuditModel):
    """学生实验提交实体：学生提交的实验报告及评分信息。"""

    SUBMISSION_STATUS_CHOICES = [
        ('draft', '草稿'),
        ('submitted', '已提交'),
        ('graded', '已批改'),
    ]

    GRADE_STATUS_CHOICES = [
        ('pending', '待批改'),
        ('completed', '已批改'),
    ]

    experiment = models.ForeignKey(
        CourseExperiment,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='所属实验',
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='experiment_submissions',
        verbose_name='学生',
    )
    submission_status = models.CharField(
        max_length=20, choices=SUBMISSION_STATUS_CHOICES,
        default='draft', verbose_name='提交状态'
    )
    submit_time = models.DateTimeField(null=True, blank=True, verbose_name='提交时间')
    is_late = models.BooleanField(default=False, verbose_name='是否迟交')
    report_title = models.CharField(
        max_length=255, blank=True, default='', verbose_name='报告标题'
    )
    report_content = models.TextField(
        blank=True, default='', verbose_name='报告正文（Markdown/HTML）'
    )
    vm_info = models.JSONField(
        default=dict, blank=True, verbose_name='使用的虚拟机信息',
        help_text='如 {"vmid": 1001, "vm_name": "ubuntu", "ip": "192.168.1.100"}'
    )
    operation_logs = models.JSONField(
        default=list, blank=True, verbose_name='关键操作记录',
        help_text='前端/PVE采集的操作历史'
    )
    score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='得分'
    )
    grade_status = models.CharField(
        max_length=20, choices=GRADE_STATUS_CHOICES,
        default='pending', verbose_name='批改状态'
    )
    graded_at = models.DateTimeField(null=True, blank=True, verbose_name='批改时间')
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='graded_submissions',
        verbose_name='批改教师',
    )
    feedback = models.TextField(blank=True, default='', verbose_name='教师评语')
    scoring_details = models.JSONField(
        default=dict, blank=True, verbose_name='各项得分明细',
        help_text='如 {"基础操作": {"score": 38, "total": 40, "comment": "good"}}'
    )
    revision_count = models.IntegerField(default=0, verbose_name='修订次数')
    last_auto_save = models.DateTimeField(
        null=True, blank=True, verbose_name='最后自动保存时间'
    )

    class Meta:
        verbose_name = '实验提交'
        verbose_name_plural = '实验提交'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['experiment', 'student'],
                name='unique_experiment_student'
            )
        ]
        indexes = [
            models.Index(fields=['student', 'submission_status'], name='idx_sub_student_status'),
            models.Index(fields=['experiment', 'grade_status'], name='idx_sub_exp_grade'),
            models.Index(fields=['submit_time'], name='idx_sub_submit_time'),
        ]

    def __str__(self) -> str:
        return f"{self.student} - {self.experiment.title} [{self.get_submission_status_display()}]"


class CourseAttachment(models.Model):
    """实验附件实体：学生上传的截图、录屏等附件。"""

    FILE_CATEGORY_CHOICES = [
        ('screenshot', '操作截图'),
        ('video', '操作录屏'),
        ('document', '补充文档'),
        ('other', '其他'),
    ]

    submission = models.ForeignKey(
        CourseSubmission,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='所属提交',
    )
    file_name = models.CharField(max_length=255, verbose_name='文件名')
    file_path = models.CharField(max_length=500, verbose_name='存储路径')
    file_size = models.BigIntegerField(verbose_name='文件大小（字节）')
    file_type = models.CharField(
        max_length=50, verbose_name='文件类型', help_text='如 png / jpg / mp4 / pdf'
    )
    file_category = models.CharField(
        max_length=20, choices=FILE_CATEGORY_CHOICES, verbose_name='文件分类'
    )
    description = models.CharField(
        max_length=500, blank=True, default='', verbose_name='附件说明'
    )
    step_number = models.IntegerField(
        null=True, blank=True, verbose_name='对应实验步骤号'
    )
    thumbnail_path = models.CharField(
        max_length=500, blank=True, default='', verbose_name='缩略图路径'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_attachments',
        verbose_name='上传者',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_deleted = models.BooleanField(default=False, verbose_name='已删除')

    class Meta:
        verbose_name = '实验附件'
        verbose_name_plural = '实验附件'
        ordering = ['step_number', 'created_at']
        indexes = [
            models.Index(fields=['submission', 'file_category'], name='idx_attach_submission'),
        ]

    def __str__(self) -> str:
        return f"{self.submission_id} / {self.file_name}"
