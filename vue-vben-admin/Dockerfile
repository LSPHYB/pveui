FROM nginx:alpine

WORKDIR /usr/share/nginx/html
RUN rm -rf ./*
COPY apps/web-antd/dist/ .

# 关键修复点：
# 1. 增加针对 /api 的转发配置
# 2. 显式传递 $http_host 给 Django
RUN printf "server {\n\
    listen 80;\n\
    server_name _;\n\
    absolute_redirect off;\n\
    port_in_redirect off;\n\
\n\
    location / {\n\
        root /usr/share/nginx/html;\n\
        index index.html;\n\
        try_files \$uri \$uri/ /index.html;\n\
    }\n\
\n\
    # 转发后端接口\n\
    location /api/ {\n\
        proxy_pass http://pve_backend:8000/api/; # 确保这里的容器名和端口正确\n\
        proxy_set_header Host \$http_host;\n\
        proxy_set_header X-Real-IP \$remote_addr;\n\
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\n\
        proxy_set_header X-Forwarded-Proto \$scheme;\n\
    }\n\
}\n" > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]