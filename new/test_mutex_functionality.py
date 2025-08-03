#!/usr/bin/env python3
"""
测试检测进程互斥功能

这个脚本将测试确保同一时间只有一个检测进程运行的功能：
1. 测试并发调用check_all_keys时的互斥
2. 测试并发调用check_single_key时的互斥  
3. 测试混合调用时的互斥
4. 测试定时任务和手动检测的互斥
"""

import threading
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, scheduler_instance, create_tables
from models import db, ApiKey

def test_concurrent_check_all():
    """测试并发调用check_all_keys"""
    print("🧪 测试1: 并发调用check_all_keys")
    
    results = []
    
    def call_check_all(test_id):
        print(f"  线程{test_id}: 开始调用check_all_keys")
        start_time = time.time()
        scheduler_instance.check_all_keys()
        end_time = time.time()
        results.append({
            'test_id': test_id,
            'duration': end_time - start_time
        })
        print(f"  线程{test_id}: check_all_keys完成，耗时{end_time - start_time:.2f}秒")
    
    # 创建3个并发线程
    threads = []
    for i in range(3):
        thread = threading.Thread(target=call_check_all, args=(i+1,))
        threads.append(thread)
    
    # 启动所有线程
    for thread in threads:
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    print(f"  结果: {len(results)}个线程完成")
    for result in results:
        print(f"    线程{result['test_id']}: {result['duration']:.2f}秒")
    print()

def test_concurrent_single_check():
    """测试并发调用check_single_key"""
    print("🧪 测试2: 并发调用check_single_key")
    
    results = []
    test_key = "AIzaSyTest123456789"
    
    def call_single_check(test_id):
        print(f"  线程{test_id}: 开始调用check_single_key")
        start_time = time.time()
        is_valid, message = scheduler_instance.check_single_key(test_key)
        end_time = time.time()
        results.append({
            'test_id': test_id,
            'duration': end_time - start_time,
            'result': (is_valid, message)
        })
        print(f"  线程{test_id}: check_single_key完成，耗时{end_time - start_time:.2f}秒，结果:{message}")
    
    # 创建3个并发线程
    threads = []
    for i in range(3):
        thread = threading.Thread(target=call_single_check, args=(i+1,))
        threads.append(thread)
    
    # 启动所有线程
    for thread in threads:
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    print(f"  结果: {len(results)}个线程完成")
    for result in results:
        print(f"    线程{result['test_id']}: {result['duration']:.2f}秒, {result['result'][1]}")
    print()

def test_mixed_calls():
    """测试混合调用（check_all + check_single）"""
    print("🧪 测试3: 混合调用check_all_keys和check_single_key")
    
    results = []
    test_key = "AIzaSyTest987654321"
    
    def call_check_all(test_id):
        print(f"  线程{test_id}: 开始调用check_all_keys")
        start_time = time.time()
        scheduler_instance.check_all_keys()
        end_time = time.time()
        results.append({
            'test_id': test_id,
            'type': 'check_all',
            'duration': end_time - start_time
        })
        print(f"  线程{test_id}: check_all_keys完成，耗时{end_time - start_time:.2f}秒")
    
    def call_single_check(test_id):
        print(f"  线程{test_id}: 开始调用check_single_key")
        start_time = time.time()
        is_valid, message = scheduler_instance.check_single_key(test_key)
        end_time = time.time()
        results.append({
            'test_id': test_id,
            'type': 'check_single',
            'duration': end_time - start_time,
            'message': message
        })
        print(f"  线程{test_id}: check_single_key完成，耗时{end_time - start_time:.2f}秒")
    
    # 创建混合线程
    threads = []
    
    # 2个check_all线程
    for i in range(2):
        thread = threading.Thread(target=call_check_all, args=(f'A{i+1}',))
        threads.append(thread)
    
    # 2个check_single线程
    for i in range(2):
        thread = threading.Thread(target=call_single_check, args=(f'S{i+1}',))
        threads.append(thread)
    
    # 启动所有线程
    for thread in threads:
        thread.start()
        time.sleep(0.1)  # 稍微错开启动时间
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    print(f"  结果: {len(results)}个线程完成")
    for result in results:
        msg = result.get('message', 'N/A')
        print(f"    线程{result['test_id']} ({result['type']}): {result['duration']:.2f}秒, {msg}")
    print()

def test_status_checking():
    """测试状态检查功能"""
    print("🧪 测试4: 检测状态查询功能")
    
    print("  初始状态:")
    status = scheduler_instance.get_check_status()
    print(f"    is_checking: {status['is_checking']}")
    print(f"    check_type: {status['check_type']}")
    
    # 在后台启动一个检测
    print("  启动后台检测...")
    def background_check():
        scheduler_instance.check_all_keys()
    
    thread = threading.Thread(target=background_check)
    thread.start()
    
    # 检查状态变化
    time.sleep(0.5)  # 等待检测开始
    status = scheduler_instance.get_check_status()
    print(f"  检测中状态:")
    print(f"    is_checking: {status['is_checking']}")
    print(f"    check_type: {status['check_type']}")
    print(f"    duration: {status['duration']}秒")
    
    # 等待检测完成
    thread.join()
    
    # 检查最终状态
    status = scheduler_instance.get_check_status()
    print(f"  检测完成后状态:")
    print(f"    is_checking: {status['is_checking']}")
    print(f"    check_type: {status['check_type']}")
    print()

def main():
    """主测试函数"""
    print("🚀 开始测试检测进程互斥功能")
    print("=" * 50)
    
    # 初始化应用上下文和数据库
    with app.app_context():
        # 创建数据库表
        from models import db
        db.create_all()
        
        # 初始化调度器
        from scheduler import init_scheduler
        global scheduler_instance
        if scheduler_instance is None:
            scheduler_instance = init_scheduler(app)
            print("📝 调度器已初始化")
        
        # 确保有一些测试数据
        if ApiKey.query.count() == 0:
            print("📝 创建测试数据...")
            test_keys = [
                "AIzaSyTest1_InvalidKey12345",
                "AIzaSyTest2_InvalidKey67890", 
                "AIzaSyTest3_InvalidKey11111"
            ]
            for key_value in test_keys:
                api_key = ApiKey(key_value=key_value, status='pending')
                db.session.add(api_key)
            db.session.commit()
            print(f"   已创建 {len(test_keys)} 个测试密钥")
            print()
        
        # 运行测试
        test_status_checking()
        test_concurrent_single_check()
        test_concurrent_check_all()
        test_mixed_calls()
        
        print("✅ 所有测试完成！")
        print("\n📋 测试总结:")
        print("- 如果看到'被跳过：另一个检测进程正在运行中'的日志，说明互斥功能正常工作")
        print("- 每组测试中应该只有一个线程真正执行检测，其他的被跳过")
        print("- 状态查询应该正确反映当前的检测状态")

if __name__ == '__main__':
    main() 