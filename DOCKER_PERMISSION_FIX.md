# 🔧 Docker 数据库权限问题修复

## 🚨 问题描述

在Docker部署环境中遇到SQLite数据库写权限错误：

```
sqlite3.OperationalError: attempt to write a readonly database
```

## 🔍 问题分析

### 根本原因
- Docker容器内的用户权限不足
- SQLite数据库文件/目录没有写权限
- 数据卷挂载时权限映射问题

### 技术细节
- 容器使用非root用户 `appuser` 运行
- 数据库目录 `/app/instance` 权限不足
- 本地运行正常，Docker部署失败

## ✅ 修复方案

### 1. Dockerfile权限设置修复

**修改前:**
```dockerfile
RUN mkdir -p /app/instance && \
    chown -R appuser:appuser /app
```

**修改后:**
```dockerfile
RUN mkdir -p /app/instance && \
    chmod 755 /app && \
    chmod 775 /app/instance && \
    chown -R appuser:appuser /app && \
    chmod g+s /app/instance
```

### 2. Docker Compose卷权限修复

**修改前:**
```yaml
volumes:
  - gemini_data:/app/instance
```

**修改后:**
```yaml
volumes:
  - gemini_data:/app/instance:rw
```

## 🔧 权限说明

### 目录权限设置
- `/app` - 755 (rwxr-xr-x): 用户读写执行，组和其他用户读执行
- `/app/instance` - 775 (rwxrwxr-x): 用户和组读写执行，其他用户读执行
- `chmod g+s` - 设置setgid位，确保新文件继承组权限

### 用户权限
- 所有者: `appuser`
- 组: `appuser`
- 运行用户: `appuser`

## 🧪 验证修复

### 1. 重新构建镜像
```bash
cd v3.0
docker build -t gemini-key-checker .
```

### 2. 运行容器测试
```bash
# 删除旧容器和数据卷（注意：会丢失数据）
docker stop gemini-key-checker 2>/dev/null || true
docker rm gemini-key-checker 2>/dev/null || true
docker volume rm gemini_data 2>/dev/null || true

# 使用新镜像启动
docker run -d \
  --name gemini-key-checker \
  -p 5000:5000 \
  -v gemini_data:/app/instance \
  gemini-key-checker

# 检查日志
docker logs -f gemini-key-checker
```

### 3. 验证权限
```bash
# 检查容器内权限
docker exec gemini-key-checker ls -la /app/
docker exec gemini-key-checker ls -la /app/instance/

# 检查用户身份
docker exec gemini-key-checker whoami
docker exec gemini-key-checker id
```

### 4. 测试数据库操作
访问 http://your-server:5000 并尝试添加API密钥

## 🚀 部署到服务器

### 使用修复后的镜像
```bash
# 在服务器上拉取最新镜像
docker pull ghcr.io/Superflash1/gemini-key-checker:latest

# 停止旧容器
docker stop gemini-key-checker
docker rm gemini-key-checker

# 启动新容器
docker run -d \
  --name gemini-key-checker \
  --restart unless-stopped \
  -p 5000:5000 \
  -v gemini_data:/app/instance \
  ghcr.io/Superflash1/gemini-key-checker:latest
```

## 🔧 故障排除

### 如果权限问题仍然存在

1. **检查Docker版本兼容性**
   ```bash
   docker --version
   ```

2. **检查SELinux/AppArmor限制**
   ```bash
   # CentOS/RHEL
   getenforce
   
   # Ubuntu
   aa-status
   ```

3. **手动修复权限**
   ```bash
   # 进入容器修复权限
   docker exec -u root gemini-key-checker chown -R appuser:appuser /app/instance
   docker exec -u root gemini-key-checker chmod 775 /app/instance
   ```

4. **检查磁盘空间**
   ```bash
   df -h
   docker system df
   ```

### 如果数据卷问题持续

```bash
# 创建具有正确权限的新数据卷
docker volume create --driver local \
  --opt type=none \
  --opt o=bind \
  --opt device=/path/to/data \
  gemini_data_new

# 使用新数据卷启动容器
docker run -d \
  --name gemini-key-checker \
  -p 5000:5000 \
  -v gemini_data_new:/app/instance \
  gemini-key-checker
```

## 📋 修改文件清单

- ✅ `v3.0/Dockerfile` - 添加了详细的权限设置
- ✅ `v3.0/docker-compose.yml` - 明确了卷权限

## 🎯 预期结果

修复后应该能够：
- ✅ 正常启动Docker容器
- ✅ 成功创建SQLite数据库
- ✅ 正常添加和管理API密钥
- ✅ 数据持久化正常工作

---

✅ **修复完成**: SQLite数据库权限问题已解决，可以正常添加密钥。 