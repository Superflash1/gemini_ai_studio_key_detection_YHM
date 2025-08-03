# Gemini API Key Checker

一个高效、免费的 Python 命令行工具，用于批量验证 Google Gemini API 密钥的有效性。

本工具通过调用一个不消耗 token 的元数据 API 端点 (`list_models`) 来进行验证，确保您可以在不产生任何费用的情况下检查大量密钥。

## ✨ 功能特性

- **无消耗验证**: 不会使用您的 Gemini API 配额或产生费用。
- **高并发**: 使用多线程并发检测，速度快，效率高。
- **多种输入方式**: 支持从文件或直接从命令行参数读取密钥。
- **清晰的结果输出**:
    - 在控制台实时显示带有进度条的检测过程。
    - 自动将有效和无效的密钥分类保存到 `valid_keys.txt` 和 `invalid_keys.txt`。
- **安全**: 在控制台输出中，仅显示密钥的头尾部分，保护您的密钥不被完全暴露。

## 🚀 安装

1.  确保您已安装 Python 3.7+。
2.  克隆或下载本仓库。
3.  进入项目根目录，并安装所需的依赖：

    ```bash
    pip install -r requirements.txt
    ```

## 📖 使用方法

您可以通过两种方式提供要检测的 API 密钥。

### 1. 从文件加载

创建一个文本文件（例如 `keys.txt`），将您所有的 API 密钥粘贴进去，每行一个。

```
# keys.txt
AIzaSyC...examplekey1
AIzaSyC...examplekey2
AIzaSyC...examplekey3
```

然后运行以下命令：

```bash
python run.py --file keys.txt
```

#### 代理设置

由于访问 Google API 需要翻墙，本工具默认使用 Clash 的代理地址 `http://127.0.0.1:7890`。

- **使用默认代理**（推荐）：
```bash
python run.py -f keys.txt
```

- **自定义代理地址**：
```bash
python run.py -f keys.txt --proxy http://127.0.0.1:7890
```

- **禁用代理**（如果您有其他翻墙方式）：
```bash
python run.py -f keys.txt --no-proxy
```

#### 指定并发数

您可以使用 `-c` 或 `--concurrency` 参数来控制并发检测的线程数（默认为10）。

```bash
python run.py -f keys.txt -c 50
```

### 2. 从命令行直接输入

直接将密钥作为参数传递给脚本。

```bash
python run.py AIzaSyC...key1 AIzaSyC...key2
```

### 结合使用

您也可以同时从文件和命令行加载密钥。

```bash
python run.py --file keys.txt AIzaSyC...anotherkey
```

## 🌐 Web版本 (推荐)

我们提供了功能更强大的Web版本，支持持续运行和定时检测：

### 启动Web服务

```bash
python start_web.py
```

### Web功能特性

- **🎯 持续运行**: 服务持续运行，无需每次手动执行
- **⏰ 定时检测**: 可配置自动检测间隔（分钟级别）
- **🖥️ Web界面**: 现代化的Web管理界面
- **📊 实时显示**: 
  - 实时检测日志
  - 密钥状态统计
  - 检测历史记录
- **🔧 在线管理**: 
  - 添加/删除密钥
  - 手动检测单个密钥
  - 批量检测所有密钥
  - 代理设置

### 访问地址

启动后在浏览器中访问: **http://localhost:5000**

## 📝 命令行版本

如果您只需要一次性检测，可以使用命令行版本：

### 基本用法

检测完成后，您将在项目根目录下找到两个文件：

- `valid_keys.txt`: 包含所有验证通过的 API 密钥。
- `invalid_keys.txt`: 包含所有无效或检测出错的密钥，并附带错误原因。

同时，控制台会显示详细的执行过程和最终的总结报告。 