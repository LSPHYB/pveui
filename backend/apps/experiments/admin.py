from django.contrib import admin

from .models import CourseAttachment, CourseExperiment, CourseGuidebook, CourseSubmission


@admin.register(CourseExperiment)
class CourseExperimentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course_code', 'category', 'difficulty', 'status', 'is_active', 'teacher', 'start_time', 'end_time')
    list_filter = ('status', 'category', 'difficulty', 'is_active', 'is_deleted')
    search_fields = ('title', 'course_code', 'description')
    raw_id_fields = ('teacher', 'created_by', 'updated_by', 'owner_organization')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'start_time'


@admin.register(CourseGuidebook)
class CourseGuidebookAdmin(admin.ModelAdmin):
    list_display = ('title', 'experiment', 'doc_type', 'file_type', 'is_public', 'is_indexed', 'index_status', 'view_count', 'download_count')
    list_filter = ('doc_type', 'file_type', 'is_public', 'is_indexed', 'index_status', 'is_deleted')
    search_fields = ('title', 'file_name', 'experiment__title')
    raw_id_fields = ('experiment', 'created_by', 'updated_by')
    readonly_fields = ('created_at', 'updated_at', 'view_count', 'download_count')


@admin.register(CourseSubmission)
class CourseSubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'experiment', 'submission_status', 'is_late', 'score', 'grade_status', 'submit_time', 'graded_at')
    list_filter = ('submission_status', 'grade_status', 'is_late', 'is_deleted')
    search_fields = ('student__username', 'experiment__title', 'report_title')
    raw_id_fields = ('experiment', 'student', 'graded_by', 'created_by', 'updated_by')
    readonly_fields = ('created_at', 'updated_at', 'last_auto_save')
    date_hierarchy = 'submit_time'


@admin.register(CourseAttachment)
class CourseAttachmentAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'submission', 'file_category', 'file_type', 'file_size', 'step_number', 'uploaded_by', 'created_at')
    list_filter = ('file_category', 'file_type', 'is_deleted')
    search_fields = ('file_name', 'description', 'submission__student__username')
    raw_id_fields = ('submission', 'uploaded_by')
    readonly_fields = ('created_at', 'updated_at')
