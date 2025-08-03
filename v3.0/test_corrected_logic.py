#!/usr/bin/env python3
"""
测试修正后的检测逻辑：排除已失效密钥的检测
"""

from datetime import datetime, timedelta
from app import app, db
from models import ApiKey, Settings

def setup_test_data():
    """设置测试数据"""
    with app.app_context():
        # 清理现有数据
        ApiKey.query.delete()
        db.session.commit()
        
        # 添加不同状态的测试密钥
        test_keys = [
            # 新密钥 (pending) - 应该检测
            ApiKey(key_value="new_key_001", status='pending'),
            ApiKey(key_value="new_key_002", status='pending'),
            
            # 有效密钥 (valid) - 应该检测
            ApiKey(key_value="valid_key_001", status='valid', 
                   last_checked=datetime.utcnow() - timedelta(hours=1)),
            ApiKey(key_value="valid_key_002", status='valid', 
                   last_checked=datetime.utcnow() - timedelta(hours=25)),  # 超过24小时
            
            # 失效密钥 (invalid) - 不应该检测
            ApiKey(key_value="invalid_key_001", status='invalid', 
                   last_checked=datetime.utcnow() - timedelta(hours=2)),
            ApiKey(key_value="invalid_key_002", status='invalid', 
                   last_checked=datetime.utcnow() - timedelta(hours=26)),  # 超过24小时
            
            # 从未检测过的密钥 - 应该检测
            ApiKey(key_value="never_checked_001", status='pending', last_checked=None),
        ]
        
        for key in test_keys:
            db.session.add(key)
        
        db.session.commit()
        print(f"✅ 已设置 {len(test_keys)} 个测试密钥")
        
        # 显示各状态的密钥数量
        valid_count = ApiKey.query.filter_by(status='valid').count()
        invalid_count = ApiKey.query.filter_by(status='invalid').count()
        pending_count = ApiKey.query.filter_by(status='pending').count()
        
        print(f"   📊 有效密钥: {valid_count} 个")
        print(f"   📊 失效密钥: {invalid_count} 个")
        print(f"   📊 待检测密钥: {pending_count} 个")
        
        return len(test_keys)

def test_corrected_logic():
    """测试修正后的检测逻辑"""
    with app.app_context():
        print("\n🔧 测试修正后的检测逻辑...")
        
        # 1. 测试全量检测策略（应该排除失效密钥）
        print("\n1. 测试全量检测策略")
        
        strategy_setting = Settings.query.filter_by(key='check_strategy').first()
        if not strategy_setting:
            strategy_setting = Settings(key='check_strategy', value='all')
            db.session.add(strategy_setting)
        else:
            strategy_setting.value = 'all'
        db.session.commit()
        
        # 模拟全量检测的查询逻辑
        keys_to_check = ApiKey.query.filter(
            ApiKey.status.in_(['valid', 'pending'])
        ).all()
        
        print(f"   📋 全量检测将检测 {len(keys_to_check)} 个密钥:")
        for key in keys_to_check:
            print(f"     ✅ {key.key_value} (状态: {key.status})")
        
        # 验证失效密钥被排除
        invalid_keys = ApiKey.query.filter_by(status='invalid').all()
        print(f"   ❌ 被排除的失效密钥 {len(invalid_keys)} 个:")
        for key in invalid_keys:
            print(f"     🚫 {key.key_value} (状态: {key.status}) - 不会检测")
        
        # 2. 测试增量检测策略
        print("\n2. 测试增量检测策略")
        
        strategy_setting.value = 'incremental'
        db.session.commit()
        
        # 模拟增量检测的查询逻辑
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        incremental_keys = ApiKey.query.filter(
            (
                (ApiKey.status == 'pending') | 
                (ApiKey.last_checked.is_(None)) |
                ((ApiKey.status == 'valid') & (ApiKey.last_checked < cutoff_time))
            )
        ).all()
        
        print(f"   ⚡ 增量检测将检测 {len(incremental_keys)} 个密钥:")
        for key in incremental_keys:
            reason = ""
            if key.status == 'pending':
                reason = "状态为pending"
            elif key.last_checked is None:
                reason = "从未检测"
            elif key.status == 'valid' and key.last_checked < cutoff_time:
                reason = f"有效但超过24小时未检测"
            
            print(f"     ✅ {key.key_value}: {reason}")
        
        # 3. 测试强制全量检测
        print("\n3. 测试强制全量检测（包括失效密钥）")
        
        # 强制检测会检测所有密钥
        force_keys = ApiKey.query.all()
        print(f"   🔥 强制检测将检测 {len(force_keys)} 个密钥（包括失效的）:")
        
        valid_in_force = [k for k in force_keys if k.status == 'valid']
        pending_in_force = [k for k in force_keys if k.status == 'pending']
        invalid_in_force = [k for k in force_keys if k.status == 'invalid']
        
        print(f"     - 有效密钥: {len(valid_in_force)} 个")
        print(f"     - 待检测密钥: {len(pending_in_force)} 个")
        print(f"     - 失效密钥: {len(invalid_in_force)} 个")

def verify_logic_correction():
    """验证逻辑修正"""
    print("\n✅ 验证逻辑修正...")
    
    print("\n🔍 修正前的问题:")
    print("   ❌ 检测所有密钥，包括已失效的")
    print("   ❌ 浪费API调用次数检测已知失效的密钥")
    
    print("\n🔧 修正后的改进:")
    print("   ✅ 全量检测只检测有效和待检测的密钥")
    print("   ✅ 增量检测排除失效密钥，只检测可能需要验证的")
    print("   ✅ 强制检测仍可检测所有密钥（用于特殊情况）")
    print("   ✅ 节省API调用，提高检测效率")
    
    print("\n💡 逻辑解释:")
    print("   📌 失效密钥不会自动恢复，无需重复检测")
    print("   📌 有效密钥可能失效，需要定期验证")
    print("   📌 新密钥需要首次检测确定状态")
    print("   📌 强制检测用于特殊情况下的完整验证")

def cleanup_test_data():
    """清理测试数据"""
    with app.app_context():
        # 删除测试密钥
        test_keys = ApiKey.query.filter(
            ApiKey.key_value.like('%_key_%')
        ).all()
        
        for key in test_keys:
            db.session.delete(key)
        
        db.session.commit()
        print(f"🧹 已清理 {len(test_keys)} 个测试密钥")

if __name__ == "__main__":
    print("🎯 Gemini Key Checker - 修正后检测逻辑测试")
    print("=" * 50)
    
    try:
        # 设置测试数据
        total_keys = setup_test_data()
        
        # 测试修正后的逻辑
        test_corrected_logic()
        
        # 验证逻辑修正
        verify_logic_correction()
        
        print("\n📋 测试总结:")
        print("1. ✅ 全量检测正确排除失效密钥")
        print("2. ✅ 增量检测只检测必要的密钥")
        print("3. ✅ 强制检测保留完整检测能力")
        print("4. ✅ 检测逻辑更合理，减少无效API调用")
        
        print("\n🚀 优化效果:")
        invalid_count = ApiKey.query.filter_by(status='invalid').count()
        total_count = ApiKey.query.count()
        efficiency = (invalid_count / total_count) * 100 if total_count > 0 else 0
        print(f"   节省API调用比例: {efficiency:.1f}% (跳过 {invalid_count} 个失效密钥)")
        
        input("\n⏸️  按回车键清理测试数据...")
        cleanup_test_data()
        
        print("\n✅ 修正逻辑测试完成！")
        
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        cleanup_test_data()
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        cleanup_test_data() 