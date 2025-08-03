# 🔒 安全扫描解决方案

## 📋 问题解决策略

由于GitHub Actions中的Trivy扫描出现问题，我们采用了**分离策略**：

1. **主构建流程** (`.github/workflows/docker-build.yml`) - 专注于构建和推送
2. **安全扫描流程** (`.github/workflows/security-scan.yml`) - 独立的安全扫描

## 🚀 当前状态

### ✅ 主构建流程 (已修复)
- 构建Docker镜像
- 推送到GitHub Container Registry
- 支持多架构 (amd64/arm64)
- 自动版本标签管理

### 🔒 安全扫描流程 (独立运行)
- 手动触发扫描
- 定期自动扫描 (每周一次)
- 生成安全报告
- 上传到GitHub Security标签页

## 📖 使用方法

### 1. 构建和推送镜像
```bash
# 推送代码自动触发构建
git push origin main
```

### 2. 手动运行安全扫描
1. 进入GitHub仓库的Actions标签页
2. 选择"Security Scan"工作流
3. 点击"Run workflow"
4. 选择要扫描的镜像标签 (默认: latest)
5. 运行扫描

### 3. 查看扫描结果
- 在Actions运行日志中查看详细报告
- 在Security标签页查看SARIF报告
- 检查工作流摘要中的安全报告

## 🔧 故障排除指南

### 如果构建失败：
1. 检查Dockerfile语法
2. 验证依赖项配置
3. 查看构建日志错误信息

### 如果安全扫描失败：
1. 确认镜像已成功推送
2. 检查镜像名称是否正确
3. 验证权限设置
4. 手动运行Trivy命令测试

## 📊 镜像信息

### 当前镜像位置
```
ghcr.io/Superflash1/gemini-key-checker:latest
```

### 支持的标签
- `latest` - 最新主分支代码
- `v3.0` - v3.0分支代码
- `vX.Y.Z` - 具体版本标签

## 🛠️ 本地测试

### 拉取并运行镜像
```bash
# 拉取镜像
docker pull ghcr.io/Superflash1/gemini-key-checker:latest

# 运行容器
docker run -d \
  --name gemini-key-checker \
  -p 5000:5000 \
  -v gemini_data:/app/instance \
  ghcr.io/Superflash1/gemini-key-checker:latest

# 访问应用
open http://localhost:5000
```

### 本地安全扫描
```bash
# 使用Trivy扫描本地镜像
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:latest image ghcr.io/Superflash1/gemini-key-checker:latest
```

## 🔄 后续优化计划

1. **完善扫描配置**
   - 调整扫描参数
   - 添加更多安全检查
   - 优化报告格式

2. **集成回主流程**
   - 修复时间同步问题
   - 重新集成到主构建流程
   - 添加条件控制

3. **增强安全性**
   - 添加代码扫描 (CodeQL)
   - 依赖项漏洞检查
   - 容器配置最佳实践验证

## 📞 支持

如果遇到问题：
1. 查看GitHub Actions运行日志
2. 检查本文档的故障排除部分
3. 手动验证镜像可访问性
4. 确认权限配置正确

---

✅ **当前方案**: 主构建功能正常，安全扫描独立运行，确保系统稳定性。 