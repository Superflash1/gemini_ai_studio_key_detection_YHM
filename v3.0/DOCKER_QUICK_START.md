# 🚀 Docker 快速开始指南

## 一键部署

### 方式一：使用脚本（推荐）

```bash
# 克隆项目
git clone <your-repo-url>
cd gemini_ai_studio_key_detection/v3.0

# 一键部署
./scripts/deploy.sh --logs
```

### 方式二：使用 Docker Compose

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 方式三：使用预构建镜像

```bash
# 直接运行
docker run -d \
  --name gemini-key-checker \
  --restart unless-stopped \
  -p 5000:5000 \
  -v gemini_data:/app/instance \
  ghcr.io/your-username/gemini_ai_studio_key_detection/gemini-key-checker:latest
```

## 🌐 访问应用

部署成功后，在浏览器中访问：http://localhost:5000

## 📋 常用命令

```bash
# 查看容器状态
docker ps | grep gemini-key-checker

# 查看实时日志
docker logs -f gemini-key-checker

# 停止服务
docker stop gemini-key-checker

# 重启服务
docker restart gemini-key-checker

# 备份数据
docker run --rm -v gemini_data:/data -v $(pwd):/backup alpine tar czf /backup/backup-$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
```

## 🛠️ 自定义配置

### 修改端口

```bash
# 使用 8080 端口
./scripts/deploy.sh --port 8080
```

### 构建自定义镜像

```bash
# 构建镜像
./scripts/build.sh

# 部署自定义镜像
./scripts/deploy.sh --rebuild
```

## 🔧 故障排除

### 端口被占用

```bash
# 查看端口占用
netstat -tulpn | grep :5000

# 使用其他端口
./scripts/deploy.sh --port 8080
```

### 容器启动失败

```bash
# 查看详细日志
docker logs gemini-key-checker

# 重新构建
./scripts/deploy.sh --rebuild
```

## 📞 获取帮助

```bash
# 查看部署脚本帮助
./scripts/deploy.sh --help

# 查看构建脚本帮助
./scripts/build.sh --help
``` 