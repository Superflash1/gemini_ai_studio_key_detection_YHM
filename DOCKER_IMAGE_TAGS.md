# 🏷️ Docker镜像标签说明

本项目有两个不同的Docker构建流程，产生不同的镜像标签。以下是详细的标签区分说明：

## 📦 镜像仓库地址
```
ghcr.io/your-username/gemini_ai_studio_key_detection
```

## 🔖 标签分类说明

### 1. 🐳 标准版本（docker-build.yml）
**特点**：完整功能，支持AMD64架构，生产环境推荐

| 标签 | 说明 | 使用场景 | 构建时间 |
|------|------|----------|----------|
| `:latest` | 最新稳定版本 | **生产环境部署** | ~5-8分钟 |
| `:stable` | 稳定版本别名 | 明确指定稳定版本 | ~5-8分钟 |
| `:main-stable` | 主分支稳定版 | 主分支最新稳定构建 | ~5-8分钟 |
| `:v1.0.0` | 具体版本号 | 版本发布时自动生成 | ~5-8分钟 |

**使用方式**：
```bash
# 生产环境推荐（最稳定）
docker pull ghcr.io/username/repo:latest
docker run -d -p 5000:5000 ghcr.io/username/repo:latest

# 明确指定稳定版本
docker pull ghcr.io/username/repo:stable
docker run -d -p 5000:5000 ghcr.io/username/repo:stable
```

### 2. ⚡ 快速版本（docker-build-fast.yml）
**特点**：快速构建，仅AMD64架构，开发测试推荐

| 标签 | 说明 | 使用场景 | 构建时间 |
|------|------|----------|----------|
| `:fast` | 快速构建版本 | **开发测试环境** | ~3-5分钟 |
| `:dev` | 开发版本别名 | 开发环境快速部署 | ~3-5分钟 |
| `:main-fast` | 主分支快速版 | 主分支最新快速构建 | ~3-5分钟 |

**使用方式**：
```bash
# 开发测试推荐（构建最快）
docker pull ghcr.io/username/repo:fast
docker run -d -p 5000:5000 ghcr.io/username/repo:fast

# 开发环境部署
docker pull ghcr.io/username/repo:dev
docker run -d -p 5000:5000 ghcr.io/username/repo:dev
```

## 🎯 选择建议

### 生产环境 🏢
```bash
# 推荐：使用latest或stable标签
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/data:/app/instance \
  --name gemini-checker \
  ghcr.io/username/repo:latest
```

### 开发测试 💻
```bash
# 推荐：使用fast或dev标签（构建更快）
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/data:/app/instance \
  --name gemini-checker-dev \
  ghcr.io/username/repo:fast
```

### 特定版本 📌
```bash
# 使用具体版本号（最可控）
docker run -d \
  -p 5000:5000 \
  --name gemini-checker \
  ghcr.io/username/repo:v1.0.0
```

## 🔍 如何查看可用标签

### 方法1：GitHub Packages页面
1. 访问您的GitHub仓库
2. 点击右侧的"Packages"
3. 选择对应的包，查看所有标签

### 方法2：命令行查询
```bash
# 使用GitHub CLI（需要安装gh命令）
gh api /user/packages/container/gemini_ai_studio_key_detection/versions

# 或使用Docker命令（需要登录）
docker search ghcr.io/username/repo
```

### 方法3：通过镜像拉取测试
```bash
# 测试不同标签是否存在
docker pull ghcr.io/username/repo:latest  # 稳定版
docker pull ghcr.io/username/repo:fast    # 快速版
docker pull ghcr.io/username/repo:dev     # 开发版
```

## 📊 构建触发条件

| 工作流 | 触发条件 | 生成标签 |
|--------|----------|----------|
| **docker-build.yml** | 推送到main分支 | `:latest`, `:stable`, `:main-stable` |
| **docker-build-fast.yml** | 推送到任意分支 | `:fast`, `:dev`, `:分支名-fast` |
| **两者** | 推送标签（如v1.0.0） | 版本号标签 |

## 🚀 实际使用示例

### Docker Compose配置
```yaml
# docker-compose.prod.yml（生产环境）
version: '3.8'
services:
  app:
    image: ghcr.io/username/repo:latest  # 使用稳定版

# docker-compose.dev.yml（开发环境）
version: '3.8'
services:
  app:
    image: ghcr.io/username/repo:fast   # 使用快速版
```

### 部署脚本示例
```bash
#!/bin/bash
# deploy.sh

ENV=${1:-prod}  # 默认生产环境

if [ "$ENV" = "dev" ]; then
    echo "部署开发环境..."
    docker run -d -p 5000:5000 ghcr.io/username/repo:fast
else
    echo "部署生产环境..."
    docker run -d -p 5000:5000 ghcr.io/username/repo:latest
fi
```

## 🎉 总结

通过不同的标签策略，您可以：
- ✅ **清楚区分**：每个镜像的用途一目了然
- ⚡ **快速开发**：使用`:fast`标签获得更快的构建速度
- 🔒 **稳定部署**：使用`:latest`标签获得最稳定的版本
- 📌 **版本控制**：使用具体版本号标签进行精确控制

选择适合您需求的标签，享受高效的Docker化部署体验！ 