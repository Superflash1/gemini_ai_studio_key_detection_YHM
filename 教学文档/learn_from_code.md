# Flask SQLite数据库自动创建机制

在Flask应用中使用SQLAlchemy时，数据库文件的创建是自动完成的。让我们通过代码来理解这个过程：

## 1. 数据库配置

首先在Flask应用中配置SQLite数据库：

```python
# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gemini_keys.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'
```

这里的配置告诉Flask：
- 使用SQLite数据库
- 数据库文件名为`gemini_keys.db`
- 数据库文件将存储在应用的`instance`目录中

## 2. 创建数据库目录

确保存放数据库的目录存在：

```python
# 确保数据库目录存在
os.makedirs('instance', exist_ok=True)
```

- `exist_ok=True`参数确保即使目录已存在也不会报错
- `instance`是Flask的约定目录，用于存储实例相关文件

## 3. 初始化数据库

通过调用初始化函数创建数据库：

```python
def create_tables():
    """创建数据库表并初始化默认设置"""
    with app.app_context():
        db.create_all()
```

## 4. 自动创建机制说明

1. **SQLAlchemy自动创建**
   - 当配置`SQLALCHEMY_DATABASE_URI`指向SQLite文件时
   - SQLAlchemy会自动在指定位置创建数据库文件

2. **`db.create_all()`作用**
   - 根据models.py中定义的模型类
   - 自动创建所有数据库表
   - 如果表已存在则跳过

3. **Flask的instance目录**
   - Flask应用默认使用instance目录存储实例文件
   - 数据库文件通常放在这个目录下
   - 这是Flask的最佳实践约定

4. **目录确保机制**
   - 使用`os.makedirs()`确保目录存在
   - `exist_ok=True`参数防止目录已存在时报错

## 5. 执行顺序

1. 应用启动时首先确保instance目录存在
2. 然后执行create_tables()函数
3. SQLAlchemy检查数据库文件是否存在，不存在则创建
4. 最后创建所有定义的数据库表

这种自动创建机制使得开发者不需要手动创建数据库文件，简化了应用的部署和初始化过程。

---

# Docker容器化部署与CI/CD配置

在现代软件开发中，Docker容器化和自动化CI/CD是必不可少的技能。让我们通过代码来理解Docker部署的完整流程：

## 1. Docker配置文件的作用和关系

### 1.1 Dockerfile - 镜像构建蓝图

Dockerfile定义了如何构建Docker镜像：

```dockerfile
# 选择基础镜像
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 复制代码
COPY v4.0/ .

# 安装依赖
RUN pip install -r requirements.txt

# 启动命令
CMD ["python", "start_web.py"]
```

**作用**：
- 📋 定义镜像构建的每一步操作
- 🎯 类似于"制作说明书"，告诉Docker如何制作您的应用镜像
- 🔧 使用场景：`docker build -t my-app .`

### 1.2 docker-compose.yml - 本地部署编排

docker-compose.yml简化了本地Docker部署：

```yaml
version: '3.8'
services:
  gemini-key-checker:
    build: .              # 使用当前目录的Dockerfile
    ports:
      - "5000:5000"       # 端口映射
    volumes:
      - ./data:/app/instance  # 数据持久化
    restart: unless-stopped   # 自动重启
```

**作用**：
- 🎼 编排多个服务的配置
- 🚀 一条命令启动完整应用：`docker-compose up -d`
- 📁 管理数据持久化和网络配置
- 🔧 使用场景：本地开发、测试、简单部署

### 1.3 GitHub Actions - 自动化CI/CD

GitHub Actions工作流文件实现自动化构建：

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [main]    # 当推送到main分支时触发

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
```

**作用**：
- 🤖 自动化构建和发布流程
- 🔄 每次代码更新时自动构建新镜像
- 📦 发布到镜像仓库供他人使用
- 🔧 使用场景：持续集成/部署，团队协作

## 2. 两种镜像仓库方案对比

### 2.1 GitHub Container Registry (GHCR) - 推荐方案

```yaml
env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

# 自动认证，无需额外配置
username: ${{ github.actor }}
password: ${{ secrets.GITHUB_TOKEN }}
```

**优势**：
- ✅ **零配置**：GitHub自动提供认证token
- ✅ **免费无限制**：对公开仓库完全免费
- ✅ **深度集成**：与GitHub仓库权限系统完美结合
- ✅ **安全性高**：基于GitHub的安全体系

**使用方式**：
```bash
# 直接拉取GitHub构建的镜像
docker pull ghcr.io/username/repo:latest
docker run -d -p 5000:5000 ghcr.io/username/repo:latest
```

### 2.2 Docker Hub - 传统方案

```yaml
env:
  IMAGE_NAME: username/app-name

# 需要手动配置secrets
username: ${{ secrets.DOCKERHUB_USERNAME }}
password: ${{ secrets.DOCKERHUB_TOKEN }}
```

**配置步骤**：
1. 在Docker Hub创建账号和仓库
2. 在GitHub项目Settings → Secrets中添加：
   - `DOCKERHUB_USERNAME`：您的Docker Hub用户名
   - `DOCKERHUB_TOKEN`：Docker Hub访问令牌

**使用方式**：
```bash
# 从Docker Hub拉取镜像
docker pull username/app-name:latest
docker run -d -p 5000:5000 username/app-name:latest
```

## 3. 构建性能优化策略

### 3.1 构建速度优化

**多架构构建影响**：
```yaml
# 慢速构建（10-20分钟）
platforms: linux/amd64,linux/arm64

# 快速构建（3-5分钟）
platforms: linux/amd64
```

**Dockerfile优化技巧**：
```dockerfile
# 优化前：每次都重新安装依赖
COPY . .
RUN pip install -r requirements.txt

# 优化后：利用Docker缓存层
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

### 3.2 多阶段构建优化

```dockerfile
# 构建阶段 - 包含编译工具
FROM python:3.11-slim as builder
RUN apt-get update && apt-get install -y gcc
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# 生产阶段 - 只包含运行时文件
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
COPY . .
CMD ["python", "app.py"]
```

**优势**：
- 🚀 减少最终镜像大小
- ⚡ 提高构建速度
- 🔒 提升安全性（移除构建工具）

## 4. 数据持久化最佳实践

### 4.1 Volume映射配置

```yaml
# docker-compose.yml
volumes:
  - ./data:/app/instance      # 数据库文件持久化
  - ./logs:/app/logs          # 日志文件持久化
```

### 4.2 数据备份策略

```bash
# 备份数据库文件
docker cp container-name:/app/instance/gemini_keys.db ./backup/

# 备份整个数据目录
cp -r ./data ./backup/data-$(date +%Y%m%d)
```

## 5. 实践经验总结

### 5.1 文件作用对比表

| 文件 | 主要作用 | 使用场景 | 构建时间 |
|------|----------|----------|----------|
| **Dockerfile** | 定义镜像构建步骤 | `docker build` | 3-5分钟 |
| **docker-compose.yml** | 本地部署编排 | `docker-compose up` | 使用Dockerfile |
| **GitHub Actions** | 自动化CI/CD | 代码推送触发 | 5-15分钟 |

### 5.2 选择建议

**开发阶段**：
```bash
# 本地快速测试
docker-compose up -d
```

**生产部署**：
```bash
# 使用GitHub自动构建的镜像
docker run -d -p 5000:5000 ghcr.io/username/repo:latest
```

**团队协作**：
- 推荐使用GitHub Container Registry
- 设置自动化CI/CD流程
- 建立代码推送→自动构建→自动部署的工作流

## 6. 故障排除常见问题

### 6.1 构建速度慢
```yaml
# 解决方案：仅构建AMD64架构
platforms: linux/amd64
```

### 6.2 权限问题
```bash
# 确保数据目录权限
chmod 755 data logs
```

### 6.3 端口冲突
```yaml
# 修改端口映射
ports:
  - "8080:5000"  # 改用8080端口
```

这种容器化部署方式实现了"一次构建，到处运行"的理念，大大简化了应用的部署和分发过程。
