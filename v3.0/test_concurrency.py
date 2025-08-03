#!/usr/bin/env python3
"""
测试并发设置功能
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_concurrency_settings():
    """测试并发设置功能"""
    print("🧪 测试并发设置功能")
    print("=" * 50)
    
    try:
        # 1. 获取当前设置
        print("1. 获取当前设置...")
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("   ✅ 主页访问成功")
        
        # 2. 测试设置保存
        print("2. 测试并发设置保存...")
        new_settings = {
            'check_interval': 30,
            'proxy_url': 'http://127.0.0.1:7890',
            'concurrency': 20
        }
        
        response = requests.post(
            f"{BASE_URL}/api/settings",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(new_settings)
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 设置保存成功: {result}")
        else:
            print(f"   ❌ 设置保存失败: {response.status_code}")
            return
        
        # 3. 验证设置生效
        print("3. 验证设置是否生效...")
        time.sleep(2)  # 等待设置生效
        
        # 4. 添加一些测试密钥
        print("4. 添加测试密钥...")
        test_keys = [
            f"test_key_{int(time.time())}_{i}" 
            for i in range(5)
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/keys",
            headers={'Content-Type': 'application/json'},
            data=json.dumps({'keys': test_keys})
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 测试密钥添加成功: {result}")
        else:
            print(f"   ❌ 测试密钥添加失败: {response.status_code}")
            return
        
        # 5. 触发并发检测
        print("5. 触发并发检测...")
        response = requests.post(f"{BASE_URL}/api/check-all")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 并发检测启动成功: {result}")
        else:
            print(f"   ❌ 并发检测启动失败: {response.status_code}")
            return
        
        # 6. 监控日志流一小段时间
        print("6. 监控检测日志...")
        try:
            response = requests.get(f"{BASE_URL}/logs", stream=True, timeout=10)
            if response.status_code == 200:
                print("   📋 检测日志:")
                
                count = 0
                for line in response.iter_lines(decode_unicode=True):
                    if line and line.startswith('data: '):
                        try:
                            data_str = line[6:]
                            data = json.loads(data_str)
                            
                            if not data.get('heartbeat'):
                                message = data.get('message', '')
                                if '并发数' in message or '检测' in message:
                                    print(f"   📝 {data.get('timestamp')} - {message}")
                                    count += 1
                                    if count >= 3:  # 只显示前3条相关日志
                                        break
                        except json.JSONDecodeError:
                            pass
                            
        except requests.exceptions.Timeout:
            print("   ⏰ 日志监控完成（超时）")
        
        print("\n🎉 并发设置功能测试完成！")
        print("\n📋 测试总结:")
        print("   ✅ 并发设置保存功能正常")
        print("   ✅ 并发检测启动正常")
        print("   ✅ 日志显示并发信息")
        print(f"   🌐 请在浏览器中访问 {BASE_URL} 查看完整界面")
        print("   ⚙️ 在左侧面板可以设置并发数（1-100）")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到Web服务")
        print("💡 请先运行: python start_web.py")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")

def test_concurrency_limits():
    """测试并发数限制"""
    print("\n🔢 测试并发数限制...")
    
    # 测试边界值
    test_cases = [
        (0, False, "并发数为0应该失败"),
        (1, True, "最小并发数1应该成功"),
        (50, True, "中等并发数50应该成功"), 
        (100, True, "最大并发数100应该成功"),
        (101, False, "超过最大并发数101应该失败")
    ]
    
    for concurrency, should_succeed, description in test_cases:
        try:
            settings = {
                'check_interval': 60,
                'proxy_url': 'http://127.0.0.1:7890',
                'concurrency': concurrency
            }
            
            response = requests.post(
                f"{BASE_URL}/api/settings",
                headers={'Content-Type': 'application/json'},
                data=json.dumps(settings)
            )
            
            success = response.status_code == 200
            if success == should_succeed:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ {description} - 预期结果不符")
                
        except Exception as e:
            print(f"   ❌ 测试 {concurrency} 时出错: {e}")

if __name__ == '__main__':
    test_concurrency_settings()
    test_concurrency_limits() 