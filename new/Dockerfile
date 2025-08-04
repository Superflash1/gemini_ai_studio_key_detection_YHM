# 多阶段构建的Dockerfile用于Gemini API Key Checker
# Stage 1: 构建阶段
FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖到临时目录
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: 运行阶段
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 设置工作目录
WORKDIR /app

# 从构建阶段复制Python包
COPY --from=builder /root/.local /home/appuser/.local

# 复制应用代码
COPY . .

# 创建数据目录并设置权限（在切换用户前设置）
RUN mkdir -p /app/instance && \
    chmod 755 /app && \
    chmod 775 /app/instance && \
    chown -R appuser:appuser /app && \
    chmod g+s /app/instance

# 切换到非root用户
USER appuser

# 更新PATH以包含用户安装的包
ENV PATH=/home/appuser/.local/bin:$PATH

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/stats')" || exit 1

# 启动命令
CMD ["python", "start_web.py"] 