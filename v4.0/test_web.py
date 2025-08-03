#!/usr/bin/env python3
"""
Web应用功能测试脚本
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_web_app():
    """测试Web应用各项功能"""
    
    print("🧪 Gemini API Key Checker Web应用测试")
    print("=" * 50)
    
    try:
        # 1. 测试主页
        print("1. 测试主页访问...")
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            print("   ✅ 主页访问成功")
        else:
            print(f"   ❌ 主页访问失败: {response.status_code}")
            return
        
        # 2. 测试统计API
        print("2. 测试统计API...")
        response = requests.get(f"{BASE_URL}/api/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✅ 统计API成功: {stats}")
        else:
            print(f"   ❌ 统计API失败: {response.status_code}")
        
        # 3. 测试密钥列表API
        print("3. 测试密钥列表API...")
        response = requests.get(f"{BASE_URL}/api/keys")
        if response.status_code == 200:
            keys = response.json()
            print(f"   ✅ 密钥列表API成功: 当前有 {len(keys)} 个密钥")
        else:
            print(f"   ❌ 密钥列表API失败: {response.status_code}")
        
        # 4. 测试添加密钥API
        print("4. 测试添加密钥API...")
        test_keys = [
            "AIzaSyC_test_key_1_invalid",
            "AIzaSyC_test_key_2_invalid"
        ]
        response = requests.post(
            f"{BASE_URL}/api/keys",
            headers={'Content-Type': 'application/json'},
            data=json.dumps({'keys': test_keys})
        )
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 添加密钥API成功: {result}")
        else:
            print(f"   ❌ 添加密钥API失败: {response.status_code}")
        
        # 5. 测试设置API
        print("5. 测试设置API...")
        settings = {
            'check_interval': 30,
            'proxy_url': 'http://127.0.0.1:7890'
        }
        response = requests.post(
            f"{BASE_URL}/api/settings",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(settings)
        )
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 设置API成功: {result}")
        else:
            print(f"   ❌ 设置API失败: {response.status_code}")
        
        # 6. 测试日志流（只测试连接）
        print("6. 测试日志流连接...")
        try:
            response = requests.get(f"{BASE_URL}/logs", stream=True, timeout=3)
            if response.status_code == 200:
                print("   ✅ 日志流连接成功")
            else:
                print(f"   ❌ 日志流连接失败: {response.status_code}")
        except requests.exceptions.Timeout:
            print("   ✅ 日志流连接成功（超时正常）")
        except Exception as e:
            print(f"   ❌ 日志流连接异常: {e}")
        
        print("\n🎉 Web应用功能测试完成！")
        print(f"🌐 在浏览器中访问: {BASE_URL}")
        print("📊 功能预览:")
        print("   - 左侧面板：添加密钥、设置定时检测")
        print("   - 右侧区域：实时日志、密钥管理")
        print("   - 统计信息：有效/无效/待检测密钥数量")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到Web服务，请确保服务正在运行")
        print("💡 运行命令启动服务: python start_web.py")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")

if __name__ == '__main__':
    test_web_app() 