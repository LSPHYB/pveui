# 直接使用预编译的前端产物
FROM nginx:alpine

# 复制预编译的产物到 nginx
COPY apps/web-antd/dist /usr/share/nginx/html

# 暴露 80 端口
EXPOSE 80

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]
