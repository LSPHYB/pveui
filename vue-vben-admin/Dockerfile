# 阶段 1：构建阶段
FROM node:20-alpine AS builder

# 安装 pnpm
RUN npm install -g pnpm

# 设置工作目录
WORKDIR /app

# 复制 package.json 和 pnpm-lock.yaml (如果有)
COPY package.json pnpm-lock.yaml* ./

# 安装项目依赖 (根据锁文件)
RUN pnpm install --frozen-lockfile || pnpm install

# 复制项目所有文件
COPY . .

# 执行构建命令，构建生产环境产物
RUN pnpm build

# 阶段 2：运行阶段
FROM nginx:alpine

# 将构建阶段的产物复制到 nginx 的默认静态文件目录
# 注意：vben 默认构建产物在 apps/web-antd/dist 目录下
COPY --from=builder /app/apps/web-antd/dist /usr/share/nginx/html

# 复制自定义 nginx 配置文件 (如果有需要，可选)
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露 80 端口
EXPOSE 80

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]
