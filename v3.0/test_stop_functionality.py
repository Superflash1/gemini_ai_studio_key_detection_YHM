#!/usr/bin/env python3
"""
测试停止检测功能

这个脚本将测试停止检测功能的各个方面：
1. 测试在检测进行中停止
2. 测试在空闲状态停止
3. 测试停止后的状态恢复
4. 测试停止后重新开始检测
"""

import threading
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, scheduler_instance
from models import db, ApiKey

def test_stop_during_check():
    """测试在检测进行中停止"""
    print("🧪 测试1: 在检测进行中停止")
    
    with app.app_context():
        # 确保有测试数据
        if ApiKey.query.count() < 5:
            print("  创建更多测试数据...")
            for i in range(5):
                api_key = ApiKey(key_value=f"AIzaSyStopTest{i:03d}_InvalidKey", status='pending')
                db.session.add(api_key)
            db.session.commit()
        
        print("  启动后台检测...")
        
        # 在后台启动检测
        def background_check():
            scheduler_instance.check_all_keys()
        
        thread = threading.Thread(target=background_check)
        thread.start()
        
        # 等待检测开始
        time.sleep(1)
        
        # 检查状态
        status = scheduler_instance.get_check_status()
        print(f"  检测状态: is_checking={status['is_checking']}, stop_requested={status['stop_requested']}")
        
        if status['is_checking']:
            print("  发送停止请求...")
            success, message = scheduler_instance.stop_checking()
            print(f"  停止结果: success={success}, message={message}")
            
            # 检查停止状态
            time.sleep(0.5)
            status = scheduler_instance.get_check_status()
            print(f"  停止后状态: is_checking={status['is_checking']}, stop_requested={status['stop_requested']}")
        
        # 等待线程完成
        thread.join()
        
        # 最终状态
        status = scheduler_instance.get_check_status()
        print(f"  最终状态: is_checking={status['is_checking']}, stop_requested={status['stop_requested']}")
        print()

def test_stop_when_idle():
    """测试在空闲状态停止"""
    print("🧪 测试2: 在空闲状态停止")
    
    with app.app_context():
        # 确保没有检测在进行
        time.sleep(1)
        
        status = scheduler_instance.get_check_status()
        print(f"  当前状态: is_checking={status['is_checking']}")
        
        if not status['is_checking']:
            print("  尝试停止空闲状态...")
            success, message = scheduler_instance.stop_checking()
            print(f"  停止结果: success={success}, message={message}")
        else:
            print("  跳过测试：检测仍在进行中")
        print()

def test_restart_after_stop():
    """测试停止后重新开始检测"""
    print("🧪 测试3: 停止后重新开始检测")
    
    with app.app_context():
        print("  启动第一次检测...")
        
        # 第一次检测
        def first_check():
            scheduler_instance.check_all_keys()
        
        thread1 = threading.Thread(target=first_check)
        thread1.start()
        
        # 等待开始并停止
        time.sleep(1)
        if scheduler_instance.is_checking():
            print("  停止第一次检测...")
            scheduler_instance.stop_checking()
            time.sleep(1)
        
        thread1.join()
        
        # 等待完全停止
        time.sleep(1)
        
        # 启动第二次检测
        print("  启动第二次检测...")
        def second_check():
            scheduler_instance.check_all_keys()
        
        thread2 = threading.Thread(target=second_check)
        thread2.start()
        
        time.sleep(1)
        status = scheduler_instance.get_check_status()
        print(f"  第二次检测状态: is_checking={status['is_checking']}")
        
        thread2.join()
        
        print("  测试完成")
        print()

def test_multiple_stop_requests():
    """测试多次停止请求"""
    print("🧪 测试4: 多次停止请求")
    
    with app.app_context():
        print("  启动检测...")
        
        def background_check():
            scheduler_instance.check_all_keys()
        
        thread = threading.Thread(target=background_check)
        thread.start()
        
        time.sleep(1)
        
        if scheduler_instance.is_checking():
            print("  发送第一次停止请求...")
            success1, message1 = scheduler_instance.stop_checking()
            print(f"    结果: {success1}, {message1}")
            
            print("  发送第二次停止请求...")
            success2, message2 = scheduler_instance.stop_checking()
            print(f"    结果: {success2}, {message2}")
            
            print("  发送第三次停止请求...")
            success3, message3 = scheduler_instance.stop_checking()
            print(f"    结果: {success3}, {message3}")
        
        thread.join()
        print("  测试完成")
        print()

def main():
    """主测试函数"""
    print("🚀 开始测试停止检测功能")
    print("=" * 50)
    
    # 初始化应用上下文
    with app.app_context():
        # 创建数据库表
        db.create_all()
        
        # 初始化调度器
        from scheduler import init_scheduler
        global scheduler_instance
        if scheduler_instance is None:
            scheduler_instance = init_scheduler(app)
            print("📝 调度器已初始化")
        
        # 运行测试
        test_stop_when_idle()
        test_stop_during_check()
        test_restart_after_stop()
        test_multiple_stop_requests()
        
        print("✅ 所有测试完成！")
        print("\n📋 测试总结:")
        print("- 停止功能应该能够优雅地中断正在进行的检测")
        print("- 空闲状态下的停止请求应该返回适当的消息")
        print("- 停止后应该能够正常开始新的检测")
        print("- 多次停止请求应该能够正确处理")

if __name__ == '__main__':
    main() 