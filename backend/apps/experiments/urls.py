"""实验课程模块 URL 路由。

设计文档对应路由（21个 method+path）：

  # 1.3.1 实验课程（ExperimentViewSet，ModelViewSet 走 router 自动注册）
  GET    /api/v1/experiments/                              实验列表
  POST   /api/v1/experiments/                              创建实验（教师）
  GET    /api/v1/experiments/{id}/                         实验详情
  PUT    /api/v1/experiments/{id}/                         全量更新（教师）
  PATCH  /api/v1/experiments/{id}/                         部分更新（教师）
  DELETE /api/v1/experiments/{id}/                         删除实验（软删除）
  GET    /api/v1/experiments/{id}/guidebooks/              获取指导文档列表
  POST   /api/v1/experiments/{id}/guidebooks/              上传指导文档（教师）
  POST   /api/v1/experiments/{id}/publish/                 发布实验（教师）
  POST   /api/v1/experiments/{id}/archive/                 归档实验（教师）
  GET    /api/v1/experiments/{id}/export_grades/           导出成绩Excel（教师）

  # 1.3.2 指导文档（GuidebookViewSet，显式注册）
  DELETE /api/v1/guidebooks/{id}/                          删除文档（软删除，教师）
  GET    /api/v1/guidebooks/{id}/download/                 下载文档
  GET    /api/v1/guidebooks/{id}/preview/                  预览文档

  # 1.3.3 + 1.3.4 提交（SubmissionViewSet，显式注册）
  GET    /api/v1/submissions/                              提交列表（教师查全部/学生查自己）
  GET    /api/v1/submissions/my/?experiment_id=X           我的提交，不存在则自动创建草稿
  GET    /api/v1/submissions/{id}/                         提交详情
  PATCH  /api/v1/submissions/{id}/                         保存草稿（自动保存）
  POST   /api/v1/submissions/{id}/submit/                  提交报告（draft→submitted）
  POST   /api/v1/submissions/{id}/grade/                   批改（教师）
  POST   /api/v1/submissions/{id}/return/                  退回修改（教师）
  POST   /api/v1/submissions/{id}/attachments/             上传附件（学生）

  # 附件（AttachmentViewSet，显式注册）
  DELETE /api/v1/attachments/{id}/                         删除附件（学生只删自己的）
  GET    /api/v1/attachments/{id}/download/                下载附件
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AttachmentViewSet, ExperimentViewSet, GuidebookViewSet, SubmissionViewSet

# ExperimentViewSet 是 ModelViewSet，交给 router 自动生成标准 CRUD + @action 路由
router = DefaultRouter()
router.register(r'experiments', ExperimentViewSet, basename='experiment')

urlpatterns = [
    # ── ExperimentViewSet（router 自动注册）──────────────────────────────
    path('', include(router.urls)),

    # ── GuidebookViewSet（显式注册，只暴露设计文档要求的 3 个端点）────────
    path(
        'guidebooks/<int:pk>/',
        GuidebookViewSet.as_view({'delete': 'destroy'}),
        name='guidebook-detail',
    ),
    path(
        'guidebooks/<int:pk>/download/',
        GuidebookViewSet.as_view({'get': 'download'}),
        name='guidebook-download',
    ),
    path(
        'guidebooks/<int:pk>/preview/',
        GuidebookViewSet.as_view({'get': 'preview'}),
        name='guidebook-preview',
    ),

    # ── SubmissionViewSet（显式注册，共 8 个端点）────────────────────────
    # 注意：submissions/my/ 必须放在 submissions/<int:pk>/ 之前，
    # 否则 DRF 会尝试把 "my" 解析为 int pk 并抛出 404。
    path(
        'submissions/',
        SubmissionViewSet.as_view({'get': 'list'}),
        name='submission-list',
    ),
    path(
        'submissions/my/',
        SubmissionViewSet.as_view({'get': 'my'}),
        name='submission-my',
    ),
    path(
        'submissions/<int:pk>/',
        SubmissionViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update'}),
        name='submission-detail',
    ),
    path(
        'submissions/<int:pk>/submit/',
        SubmissionViewSet.as_view({'post': 'submit_report'}),
        name='submission-submit',
    ),
    path(
        'submissions/<int:pk>/grade/',
        SubmissionViewSet.as_view({'post': 'grade'}),
        name='submission-grade',
    ),
    path(
        'submissions/<int:pk>/return/',
        SubmissionViewSet.as_view({'post': 'return_submission'}),
        name='submission-return',
    ),
    path(
        'submissions/<int:pk>/attachments/',
        SubmissionViewSet.as_view({'post': 'upload_attachment'}),
        name='submission-attachments',
    ),

    # ── AttachmentViewSet（显式注册，共 2 个端点）────────────────────────
    path(
        'attachments/<int:pk>/',
        AttachmentViewSet.as_view({'delete': 'destroy'}),
        name='attachment-detail',
    ),
    path(
        'attachments/<int:pk>/download/',
        AttachmentViewSet.as_view({'get': 'download'}),
        name='attachment-download',
    ),
]
