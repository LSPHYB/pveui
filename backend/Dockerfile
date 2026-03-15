# Django 后端 Dockerfile
FROM python:3.12-slim


# 设置工作目录
WORKDIR /app

# 复制 requirements 文件（从 backend 目录）
COPY ./ /app/

# 安装系统依赖（MySQL 客户端库和编译工具）
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt 

# 收集静态文件（如果需要）
# RUN python manage.py makemigrations && python manage.py migrate && python manage.py init_rbac --create-superuser && python manage.py init_rbac

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "django_vue_adminx.wsgi:application"]

