#!/usr/bin/env python3
"""
测试日志流和自动刷新功能
"""

import requests
import json
import time
from threading import Thread

def test_log_stream():
    """测试日志流"""
    print("📡 测试Server-Sent Events日志流...")
    
    try:
        response = requests.get('http://localhost:5000/logs', stream=True, timeout=10)
        print(f"   连接状态: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ 日志流连接成功")
            print("   📋 接收到的日志数据:")
            
            count = 0
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith('data: '):
                    try:
                        data_str = line[6:]  # 移除 'data: ' 前缀
                        data = json.loads(data_str)
                        
                        if data.get('heartbeat'):
                            print(f"   💓 心跳信号 ({count})")
                        else:
                            print(f"   📝 [{data.get('timestamp')}] {data.get('level')}: {data.get('message')}")
                        
                        count += 1
                        if count >= 5:  # 只显示前5条
                            break
                            
                    except json.JSONDecodeError as e:
                        print(f"   ❌ JSON解析错误: {e}")
                        print(f"   原始数据: {line}")
                        
            print("   ✅ 日志流测试完成")
        else:
            print(f"   ❌ 连接失败: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ 测试异常: {e}")

def trigger_log_activity():
    """触发一些日志活动"""
    print("🔧 触发日志活动...")
    
    # 添加测试密钥
    test_keys = ["test_key_" + str(int(time.time()))]
    response = requests.post(
        'http://localhost:5000/api/keys',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({'keys': test_keys})
    )
    
    if response.status_code == 200:
        print("   ✅ 测试密钥添加成功")
    else:
        print(f"   ❌ 测试密钥添加失败: {response.status_code}")
    
    time.sleep(1)
    
    # 触发检测
    response = requests.post('http://localhost:5000/api/check-all')
    if response.status_code == 200:
        print("   ✅ 触发检测成功")
    else:
        print(f"   ❌ 触发检测失败: {response.status_code}")

def test_auto_refresh():
    """测试自动刷新数据"""
    print("🔄 测试API数据刷新...")
    
    # 测试统计API
    response = requests.get('http://localhost:5000/api/stats')
    if response.status_code == 200:
        stats = response.json()
        print(f"   📊 当前统计: {stats}")
    
    # 测试密钥列表API
    response = requests.get('http://localhost:5000/api/keys')
    if response.status_code == 200:
        keys = response.json()
        print(f"   🔑 当前密钥数量: {len(keys)}")
        if keys:
            latest_key = keys[0]
            print(f"   🕒 最新密钥状态: {latest_key['status']}")

def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 Gemini Key Checker 日志流和自动刷新测试")
    print("=" * 60)
    
    # 测试基础API
    test_auto_refresh()
    print()
    
    # 在后台触发一些活动
    thread = Thread(target=trigger_log_activity)
    thread.start()
    
    # 测试日志流
    test_log_stream()
    
    # 等待后台任务完成
    thread.join()
    
    print()
    print("📋 测试总结:")
    print("   ✅ 如果看到日志数据，说明日志流正常")
    print("   ✅ 如果看到统计信息，说明API正常")
    print("   🌐 请在浏览器中访问 http://localhost:5000 查看完整界面")
    print("   📱 观察界面的实时日志和自动刷新功能")

if __name__ == '__main__':
    main() 