# 🔧 GitHub Actions 错误修复

## 🚨 问题描述

用户在GitHub Actions中遇到以下错误：

```
FATAL Fatal error run error: image scan error: scan error: unable to initialize a scan service: unable to initialize an image scan service: failed to parse the image name: could not parse reference: ghcr.io/Superflash1/gemini_ai_studio_key_detection_YHM/gemini-key-checker:latest
Error: Process completed with exit code 1.
```

## 🔍 问题分析

### 根本原因
GitHub Container Registry (GHCR) 的镜像命名规范问题：

❌ **错误的命名格式**:
```
ghcr.io/Superflash1/gemini_ai_studio_key_detection_YHM/gemini-key-checker:latest
```

✅ **正确的命名格式**:
```
ghcr.io/Superflash1/gemini-key-checker:latest
```

### 技术细节
- GHCR支持的格式：`ghcr.io/OWNER/IMAGE_NAME:TAG`
- 不支持嵌套路径：`ghcr.io/OWNER/REPO_NAME/IMAGE_NAME:TAG`
- 原配置使用了 `${{ github.repository }}/gemini-key-checker`，导致了嵌套路径

## ✅ 修复方案

### 1. 修改环境变量配置

**修改前:**
```yaml
env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}/gemini-key-checker
```

**修改后:**
```yaml
env:
  REGISTRY: ghcr.io
  IMAGE_NAME: gemini-key-checker
```

### 2. 更新镜像引用

**修改前:**
```yaml
images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
```

**修改后:**
```yaml
images: ${{ env.REGISTRY }}/${{ github.repository_owner }}/${{ env.IMAGE_NAME }}
```

### 3. 修复Trivy扫描配置

**修改前:**
```yaml
image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
```

**修改后:**
```yaml
image-ref: ${{ env.REGISTRY }}/${{ github.repository_owner }}/${{ env.IMAGE_NAME }}:latest
```

## 📝 修改的文件

1. **`.github/workflows/docker-build.yml`**
   - 简化镜像名称配置
   - 修复metadata action配置
   - 修复Trivy扫描配置

2. **`v3.0/DOCKER_DEPLOYMENT.md`**
   - 更新示例镜像名称

3. **`v3.0/DOCKER_QUICK_START.md`**
   - 更新快速部署命令

## 🎯 修复结果

### 修复前的镜像名称:
```
ghcr.io/Superflash1/gemini_ai_studio_key_detection_YHM/gemini-key-checker:latest
```

### 修复后的镜像名称:
```
ghcr.io/Superflash1/gemini-key-checker:latest
```

## 🧪 验证方法

1. **推送代码触发构建**
   ```bash
   git add .
   git commit -m "fix: GitHub Actions镜像命名问题"
   git push
   ```

2. **检查Actions执行状态**
   - 访问GitHub仓库的Actions标签页
   - 查看最新的workflow运行状态
   - 确认构建和扫描步骤都成功完成

3. **验证镜像发布**
   ```bash
   docker pull ghcr.io/Superflash1/gemini-key-checker:latest
   ```

## 📋 相关链接

- [GitHub Container Registry文档](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker镜像命名最佳实践](https://docs.docker.com/engine/reference/commandline/tag/#extended-description)
- [Trivy漏洞扫描器](https://github.com/aquasecurity/trivy)

## 💡 预防措施

1. **使用简洁的镜像命名**
2. **遵循容器注册表的命名规范**
3. **在本地测试GitHub Actions配置**
4. **定期检查依赖工具的更新和变化**

---

✅ **修复完成**: GitHub Actions现在应该能够正常构建、推送和扫描Docker镜像。 