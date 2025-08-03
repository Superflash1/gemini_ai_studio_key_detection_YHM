# 🐳 Gemini Key Checker Docker 部署指南

本指南将帮助您使用 Docker 快速部署 Gemini API Key Checker v3.0。

## 📋 系统要求

- Docker Engine 20.10+
- Docker Compose 2.0+
- 至少 512MB 可用内存
- 至少 1GB 可用磁盘空间

## 🚀 快速启动

### 方法一：使用 Docker Compose（推荐）

```bash
# 克隆项目（如果还没有）
git clone <your-repo-url>
cd gemini_ai_studio_key_detection/v3.0

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 方法二：使用预构建镜像

```bash
# 拉取最新镜像
docker pull ghcr.io/your-username/gemini-key-checker:latest

# 创建数据卷
docker volume create gemini_data

# 运行容器
docker run -d \
  --name gemini-key-checker \
  --restart unless-stopped \
  -p 5000:5000 \
  -v gemini_data:/app/instance \
  ghcr.io/your-username/gemini-key-checker:latest
```

### 方法三：本地构建

```bash
# 进入 v3.0 目录
cd v3.0

# 构建镜像
docker build -t gemini-key-checker .

# 运行容器
docker run -d \
  --name gemini-key-checker \
  --restart unless-stopped \
  -p 5000:5000 \
  -v gemini_data:/app/instance \
  gemini-key-checker
```

## 🌐 访问应用

部署成功后，您可以通过以下地址访问应用：

- **本地访问**: http://localhost:5000
- **局域网访问**: http://your-server-ip:5000

## 📂 数据持久化

应用使用 SQLite 数据库存储密钥和检测记录。数据库文件位于容器内的 `/app/instance/` 目录，通过 Docker Volume 持久化。

### 数据卷管理

```bash
# 查看数据卷
docker volume ls | grep gemini

# 备份数据
docker run --rm -v gemini_data:/data -v $(pwd):/backup alpine tar czf /backup/gemini-backup-$(date +%Y%m%d_%H%M%S).tar.gz -C /data .

# 恢复数据
docker run --rm -v gemini_data:/data -v $(pwd):/backup alpine tar xzf /backup/your-backup-file.tar.gz -C /data
```

## ⚙️ 环境变量配置

您可以通过环境变量自定义应用行为：

```yaml
# docker-compose.yml 中的环境变量示例
environment:
  - FLASK_ENV=production           # Flask 环境
  - PYTHONUNBUFFERED=1            # Python 输出缓冲
  # 添加其他需要的环境变量
```

## 📊 监控和日志

### 健康检查

容器内置健康检查，您可以查看容器健康状态：

```bash
# 查看容器状态
docker ps

# 查看健康检查详情
docker inspect gemini-key-checker | grep -A 10 Health
```

### 日志管理

```bash
# 查看实时日志
docker-compose logs -f gemini-key-checker

# 查看最近 100 行日志
docker-compose logs --tail 100 gemini-key-checker

# 查看特定时间段的日志
docker-compose logs --since 2024-01-01T00:00:00 gemini-key-checker
```

## 🔧 故障排除

### 常见问题

1. **端口冲突**
   ```bash
   # 修改端口映射
   ports:
     - "8080:5000"  # 使用 8080 端口
   ```

2. **权限问题**
   ```bash
   # 检查数据卷权限
   docker exec -it gemini-key-checker ls -la /app/instance/
   ```

3. **内存不足**
   ```bash
   # 增加内存限制
   deploy:
     resources:
       limits:
         memory: 1G
   ```

### 调试模式

```bash
# 以调试模式运行
docker run -it --rm \
  -p 5000:5000 \
  -v gemini_data:/app/instance \
  gemini-key-checker \
  bash
```

## 🔄 更新应用

### 使用 Docker Compose

```bash
# 拉取最新镜像
docker-compose pull

# 重启服务
docker-compose up -d --force-recreate
```

### 使用预构建镜像

```bash
# 停止当前容器
docker stop gemini-key-checker
docker rm gemini-key-checker

# 拉取最新镜像
docker pull ghcr.io/your-username/gemini-key-checker:latest

# 重新运行
docker run -d \
  --name gemini-key-checker \
  --restart unless-stopped \
  -p 5000:5000 \
  -v gemini_data:/app/instance \
  ghcr.io/your-username/gemini-key-checker:latest
```

## 🛡️ 安全考虑

1. **网络安全**: 如果在公网部署，建议使用反向代理（如 Nginx）并配置 HTTPS
2. **访问控制**: 考虑添加认证机制保护应用
3. **定期备份**: 定期备份数据卷中的数据库文件
4. **镜像更新**: 定期更新基础镜像以获取安全补丁

## 📞 支持

如果您在部署过程中遇到问题，请：

1. 检查 Docker 和 Docker Compose 版本
2. 查看容器日志获取错误信息
3. 确认端口和网络配置
4. 检查系统资源使用情况

---

**注意**: 首次启动可能需要几分钟时间来初始化数据库和安装依赖。 