# 使用官方Python运行时作为基础镜像
FROM python:3.11-slim

# 设置维护者信息
LABEL maintainer="Gemini Key Checker"
LABEL description="Gemini API Key检测系统 - 批量检测Google Gemini API密钥有效性的Web应用"

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 设置工作目录
WORKDIR /app

# 安装系统依赖（修复版本）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 复制requirements.txt并安装Python依赖（修复版本）
COPY v4.0/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制v4.0目录的所有应用代码
COPY v4.0/ .

# 创建必要的目录
RUN mkdir -p instance static/uploads logs

# 设置权限
RUN chmod +x start_web.py

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# 设置启动命令
CMD ["python", "start_web.py"] 