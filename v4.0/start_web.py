#!/usr/bin/env python3
"""
Gemini API Key Checker Web应用启动脚本
"""

import sys
import os
from app import app, create_tables

def main():
    """启动Web应用"""
    print("=" * 50)
    print("🚀 Gemini API Key Checker Web服务")
    print("=" * 50)
    print()
    print("功能特性:")
    print("  ✅ 持续运行的Web服务")
    print("  ✅ 实时日志显示")
    print("  ✅ 可配置的定时检测")
    print("  ✅ 现代化Web界面")
    print("  ✅ 密钥管理功能")
    print()
    print("启动信息:")
    print(f"  📡 服务地址: http://localhost:5000")
    print(f"  📡 局域网访问: http://0.0.0.0:5000")
    print(f"  🗂️  数据库: SQLite (自动创建)")
    print(f"  ⏰ 定时检测: 可在Web界面配置")
    print()
    print("使用说明:")
    print("  1. 在浏览器中访问 http://localhost:5000")
    print("  2. 在左侧面板添加API密钥")
    print("  3. 设置定时检测间隔")
    print("  4. 实时查看检测日志和结果")
    print()
    print("按 Ctrl+C 停止服务...")
    print("=" * 50)
    
    try:
        # 初始化数据库和调度器
        create_tables()
        
        # 启动Flask应用
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True,
            use_reloader=False  # 避免重复启动调度器
        )
    except KeyboardInterrupt:
        print("\n\n正在停止服务...")
        print("服务已停止。")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 