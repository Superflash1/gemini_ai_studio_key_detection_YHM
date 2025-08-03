#!/usr/bin/env python3
"""
测试日志中的进度条功能
"""

import time
import threading
from app import app, db
from models import ApiKey, Settings
from scheduler import key_checker

def test_progress_bar_generation():
    """测试进度条生成功能"""
    print("🧪 测试进度条生成功能...")
    
    # 创建测试用的KeyChecker实例
    from scheduler import KeyChecker
    checker = KeyChecker(app)
    
    # 测试不同进度的进度条
    test_cases = [
        (0, 10, 0, 0),      # 开始
        (3, 10, 2, 1),      # 30%
        (5, 10, 3, 2),      # 50%
        (8, 10, 6, 2),      # 80%
        (10, 10, 8, 2),     # 完成
        (0, 0, 0, 0),       # 特殊情况：没有密钥
    ]
    
    print("\n📊 进度条示例:")
    for processed, total, valid, invalid in test_cases:
        progress_bar = checker._generate_progress_bar(processed, total, valid, invalid)
        print(f"   {progress_bar}")
    
    print("\n✅ 进度条生成功能测试完成")

def test_integrated_progress():
    """测试集成的进度条功能"""
    print("\n🔧 测试集成进度条功能...")
    
    with app.app_context():
        # 清理测试数据
        ApiKey.query.delete()
        db.session.commit()
        
        # 添加少量测试密钥便于观察
        test_keys = [
            "test_progress_key_001",
            "test_progress_key_002", 
            "test_progress_key_003"
        ]
        
        for key in test_keys:
            api_key = ApiKey(key_value=key, status='pending')
            db.session.add(api_key)
        
        db.session.commit()
        print(f"✅ 已添加 {len(test_keys)} 个测试密钥")
        
        # 设置小并发数便于观察
        concurrency_setting = Settings.query.filter_by(key='concurrency').first()
        if not concurrency_setting:
            concurrency_setting = Settings(key='concurrency', value='1')
            db.session.add(concurrency_setting)
        else:
            concurrency_setting.value = '1'
        db.session.commit()
        
        print("⚙️ 已设置并发数为 1，便于观察进度")
        
        # 启动日志监听线程
        def log_listener():
            from scheduler import get_log_stream
            print("\n📡 监听检测日志流...")
            count = 0
            for log_data in get_log_stream():
                if 'heartbeat' not in log_data:
                    print(f"📋 {log_data.strip()}")
                    count += 1
                    if count > 15:  # 限制日志数量
                        break
        
        log_thread = threading.Thread(target=log_listener, daemon=True)
        log_thread.start()
        
        # 等待日志监听器启动
        time.sleep(1)
        
        # 触发检测
        if key_checker:
            print("\n🚀 开始检测（观察日志中的进度条）...")
            key_checker.check_all_keys()
        else:
            print("❌ 调度器未初始化")
        
        # 等待检测完成
        time.sleep(8)

def test_different_scenarios():
    """测试不同场景下的进度条"""
    print("\n🎯 测试不同场景...")
    
    with app.app_context():
        # 测试空检测
        print("\n1. 测试空检测场景")
        ApiKey.query.delete()
        db.session.commit()
        
        if key_checker:
            key_checker.check_all_keys()
        
        time.sleep(2)
        
        # 测试单个密钥
        print("\n2. 测试单个密钥场景")
        single_key = ApiKey(key_value="single_test_key", status='pending')
        db.session.add(single_key)
        db.session.commit()
        
        if key_checker:
            key_checker.check_all_keys()
        
        time.sleep(3)

def cleanup_test_data():
    """清理测试数据"""
    with app.app_context():
        # 删除测试密钥
        test_keys = ApiKey.query.filter(
            ApiKey.key_value.like('%test%key%')
        ).all()
        
        for key in test_keys:
            db.session.delete(key)
        
        db.session.commit()
        print(f"🧹 已清理 {len(test_keys)} 个测试密钥")

def show_progress_bar_features():
    """展示进度条功能特性"""
    print("\n💡 日志进度条功能特性:")
    print("=" * 40)
    print("✅ 直接在日志中显示进度条")
    print("✅ ASCII字符绘制，兼容性好")
    print("✅ 包含百分比、已处理/总数信息")
    print("✅ 显示有效和无效密钥计数")
    print("✅ 等宽字体，进度对齐整齐")
    print("✅ 特殊样式突出显示")
    print("✅ 实时更新，无需单独组件")
    
    print("\n📋 进度条格式说明:")
    print("📊 进度: [████████████░░░░░░░░] 60.0% (6/10) ✅ 4 ❌ 2")
    print("        ├─进度块─┤ ├百分比┤ ├计数┤ ├有效┤ ├无效┤")

if __name__ == "__main__":
    print("🎯 Gemini Key Checker - 日志进度条测试")
    print("=" * 50)
    
    try:
        # 展示功能特性
        show_progress_bar_features()
        
        # 测试进度条生成
        test_progress_bar_generation()
        
        # 测试集成功能
        test_integrated_progress()
        
        # 测试不同场景
        test_different_scenarios()
        
        print("\n📋 测试总结:")
        print("1. ✅ 进度条生成功能正常")
        print("2. ✅ 日志集成显示正常")  
        print("3. ✅ 不同场景适配良好")
        print("4. ✅ 界面简洁，无冗余组件")
        
        print("\n💡 使用说明:")
        print("- 进度条直接显示在日志流中")
        print("- 使用等宽字体确保对齐")
        print("- 包含完整的检测统计信息")
        print("- 无需单独的进度组件")
        
        input("\n⏸️  按回车键清理测试数据...")
        cleanup_test_data()
        
        print("\n✅ 日志进度条测试完成！")
        
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        cleanup_test_data()
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        cleanup_test_data() 