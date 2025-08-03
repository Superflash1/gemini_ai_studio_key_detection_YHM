# 🐳 Docker部署指南

本文档说明如何使用Docker部署Gemini API密钥检测系统（基于v4.0版本）。

## 📋 前置要求

- Docker 20.0+
- Docker Compose 2.0+（可选，用于简化部署）

## 🚀 快速开始

### 方法1: 使用Docker Compose（推荐）

```bash
# 1. 克隆项目（如果还没有）
git clone <your-repo-url>
cd gemini_ai_studio_key_detection

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 访问应用
# 打开浏览器访问: http://localhost:5000
```

### 方法2: 直接使用Docker

```bash
# 1. 构建镜像
docker build -t gemini-key-checker .

# 2. 运行容器
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/data:/app/instance \
  -v $(pwd)/logs:/app/logs \
  --name gemini-checker \
  gemini-key-checker

# 3. 查看日志
docker logs -f gemini-checker

# 4. 访问应用
# 打开浏览器访问: http://localhost:5000
```

### 方法3: 使用GitHub Container Registry

如果项目配置了GitHub Actions，可以直接使用预构建的镜像：

```bash
# 使用GitHub构建的镜像
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/data:/app/instance \
  -v $(pwd)/logs:/app/logs \
  --name gemini-checker \
  ghcr.io/your-username/gemini_ai_studio_key_detection:latest
```

## 📁 数据持久化

### 重要文件位置

- **数据库文件**: 容器内 `/app/instance/` → 主机 `./data/`
- **日志文件**: 容器内 `/app/logs/` → 主机 `./logs/`

### 备份数据

```bash
# 备份数据库
docker cp gemini-checker:/app/instance/gemini_keys.db ./backup/

# 或者直接备份data目录
cp -r ./data ./backup/data-$(date +%Y%m%d)
```

## 🔧 配置选项

### 环境变量

可以通过环境变量配置应用：

```yaml
# docker-compose.yml
environment:
  - FLASK_ENV=production
  - PYTHONUNBUFFERED=1
  # 添加其他配置...
```

### 端口映射

如果5000端口被占用，可以修改端口映射：

```yaml
# docker-compose.yml
ports:
  - "8080:5000"  # 将应用映射到8080端口
```

## 🛠️ 管理命令

### 常用Docker命令

```bash
# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f gemini-key-checker

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 重新构建并启动
docker-compose up -d --build

# 进入容器
docker-compose exec gemini-key-checker bash
```

### 更新应用

```bash
# 1. 停止服务
docker-compose down

# 2. 拉取最新代码
git pull

# 3. 重新构建并启动
docker-compose up -d --build
```

## 🏥 健康检查

容器包含自动健康检查，可以查看容器健康状态：

```bash
# 查看健康状态
docker inspect --format='{{.State.Health.Status}}' gemini-checker

# 查看健康检查日志
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' gemini-checker
```

## 🐛 故障排除

### 常见问题

1. **端口占用**
   ```bash
   # 检查端口占用
   netstat -tlnp | grep 5000
   # 或者修改docker-compose.yml中的端口映射
   ```

2. **权限问题**
   ```bash
   # 确保data和logs目录有写权限
   chmod 755 data logs
   ```

3. **容器无法启动**
   ```bash
   # 查看详细错误日志
   docker-compose logs gemini-key-checker
   ```

4. **数据库文件损坏**
   ```bash
   # 删除数据库文件重新初始化
   rm -f data/gemini_keys.db
   docker-compose restart
   ```

### 调试模式

如果需要调试，可以临时启用调试模式：

```bash
# 停止正常服务
docker-compose down

# 以调试模式运行
docker run -it --rm \
  -p 5000:5000 \
  -v $(pwd)/data:/app/instance \
  -v $(pwd)/logs:/app/logs \
  gemini-key-checker \
  python app.py
```

## 📊 监控和日志

### 日志查看

```bash
# 实时查看应用日志
docker-compose logs -f

# 查看特定时间的日志
docker-compose logs --since "2024-01-01T00:00:00" --until "2024-01-02T00:00:00"

# 查看最近N行日志
docker-compose logs --tail 100
```

### 性能监控

```bash
# 查看容器资源使用情况
docker stats gemini-checker

# 查看容器详细信息
docker inspect gemini-checker
```

## 🔒 安全建议

1. **不要在生产环境中暴露敏感端口**
2. **定期备份数据库文件**
3. **使用强密码和安全的代理配置**
4. **定期更新Docker镜像**
5. **限制容器的网络访问权限**

## 📝 注意事项

- 首次启动会自动创建数据库和必要的目录
- API密钥等敏感信息会存储在SQLite数据库中，请妥善保管数据文件
- 建议在生产环境中使用反向代理（如Nginx）
- 容器默认以root用户运行，生产环境建议配置非root用户

## 🤝 支持

如有问题，请查看：
1. 应用日志：`docker-compose logs`
2. 健康检查状态：`docker inspect`
3. 项目文档：`v4.0/README.md` 