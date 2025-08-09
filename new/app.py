from flask import Flask, render_template, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from models import db, ApiKey, CheckLog, Settings
from scheduler import init_scheduler, get_log_stream, key_checker
from email_notifier import EmailNotifier
import json
import threading
from datetime import datetime
import os
import logging
import sqlite3
from sqlalchemy import event
from sqlalchemy.engine import Engine

app = Flask(__name__)

# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gemini_keys.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'
# 提高SQLite在多线程场景下的稳定性
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'connect_args': {
        'check_same_thread': False,
        'timeout': 30
    }
}

# 为SQLite启用WAL等PRAGMA，提升并发读写能力
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.execute("PRAGMA temp_store=MEMORY;")
            cursor.execute("PRAGMA foreign_keys=ON;")
        finally:
            cursor.close()

# 初始化数据库
db.init_app(app)

# 全局变量
scheduler_instance = None
email_notifier = None

def create_tables():
    """创建数据库表并初始化默认设置"""
    with app.app_context():
        db.create_all()
        
        # 初始化默认设置
        default_settings = {
            'check_interval': ('60', '检测间隔（分钟）'),
            'proxy_url': ('http://127.0.0.1:7890', '代理服务器地址'),
            'use_proxy': ('false', '是否使用代理'),
            'api_url': ('', 'API端点URL（留空使用Google官方API）'),
            'concurrency': ('100', '并发检测数'),
            'email_enabled': ('true', '是否启用邮件通知'),
            'email1': ('yhm200618@163.com', '邮箱地址1'),
            'email2': ('', '邮箱地址2'), 
            'email3': ('', '邮箱地址3'),
            'email_password': ('', 'Gmail应用密码'),
            'email_triggers': ('completion', '邮件触发条件（completion=检测完成）'),
        }
        
        for key, (value, description) in default_settings.items():
            existing = Settings.query.filter_by(key=key).first()
            if not existing:
                setting = Settings(key=key, value=value, description=description)
                db.session.add(setting)
        
        db.session.commit()
        
        # 初始化邮件通知器
        global email_notifier
        email_notifier = EmailNotifier(app)
        
        # 初始化调度器
        global scheduler_instance
        scheduler_instance = init_scheduler(app)
        scheduler_instance.start_scheduler()
        
        # 设置初始定时任务
        interval_setting = Settings.query.filter_by(key='check_interval').first()
        if interval_setting:
            interval_minutes = int(interval_setting.value)
            scheduler_instance.update_schedule(interval_minutes)

# 路由定义
@app.route('/')
def index():
    """主页"""
    # 获取统计信息
    stats = get_stats_data()
    
    # 获取设置
    settings = {}
    all_settings = Settings.query.all()
    for setting in all_settings:
        settings[setting.key] = setting.value
    
    return render_template('index.html', stats=stats, settings=settings)

@app.route('/logs')
def logs():
    """实时日志流 (Server-Sent Events)"""
    # 禁用代理/缓存，降低延迟
    headers = {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'X-Accel-Buffering': 'no'
    }
    return Response(get_log_stream(), headers=headers)

# API 路由
@app.route('/api/keys', methods=['GET'])
def get_keys():
    """获取所有密钥"""
    keys = ApiKey.query.order_by(ApiKey.created_at.desc()).all()
    return jsonify([{
        'id': key.id,
        'key_value': key.key_value,
        'status': key.status,
        'last_checked': key.last_checked.isoformat() if key.last_checked else None,
        'error_message': key.error_message,
        'created_at': key.created_at.isoformat()
    } for key in keys])

@app.route('/api/keys', methods=['POST'])
def add_keys():
    """添加新密钥"""
    try:
        data = request.get_json()
        keys_input = data.get('keys', [])
        
        # 解析多种输入格式的密钥
        parsed_keys = []
        
        if isinstance(keys_input, list):
            # 如果是数组，按原逻辑处理
            for key_value in keys_input:
                key_value = str(key_value).strip()
                if key_value:
                    parsed_keys.append(key_value)
        elif isinstance(keys_input, str):
            # 如果是字符串，支持多种分隔方式
            keys_text = keys_input.strip()
            
            # 去除末尾的逗号
            if keys_text.endswith(','):
                keys_text = keys_text[:-1]
            
            # 检测分隔方式：如果包含换行符，按行分割；否则按逗号分割
            if '\n' in keys_text:
                # 按行分割，每行一个密钥
                raw_keys = keys_text.split('\n')
            else:
                # 按逗号分割
                raw_keys = keys_text.split(',')
            
            # 清理和过滤密钥
            for key_value in raw_keys:
                key_value = key_value.strip()
                # 去除每个密钥末尾可能的逗号
                if key_value.endswith(','):
                    key_value = key_value[:-1].strip()
                if key_value:
                    parsed_keys.append(key_value)
        
        added_count = 0
        duplicate_count = 0
        
        for key_value in parsed_keys:
            # 检查是否已存在
            existing = ApiKey.query.filter_by(key_value=key_value).first()
            if existing:
                duplicate_count += 1
                continue
            
            # 添加新密钥
            new_key = ApiKey(key_value=key_value, status='pending')
            db.session.add(new_key)
            added_count += 1
        
        db.session.commit()
        
        # 异步检测新添加的密钥
        if added_count > 0:
            threading.Thread(
                target=check_new_keys_async, 
                args=(parsed_keys,)
            ).start()
        
        return jsonify({
            'success': True,
            'message': f'成功添加 {added_count} 个密钥，{duplicate_count} 个重复',
            'added_count': added_count,
            'duplicate_count': duplicate_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/keys/<int:key_id>', methods=['DELETE'])
def delete_key(key_id):
    """删除密钥"""
    try:
        key = ApiKey.query.get_or_404(key_id)
        db.session.delete(key)
        db.session.commit()
        return jsonify({'success': True, 'message': '密钥已删除'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/keys/delete-invalid', methods=['POST'])
def delete_invalid_keys():
    """批量删除无效密钥"""
    try:
        # 查找所有状态为invalid的密钥
        invalid_keys = ApiKey.query.filter_by(status='invalid').all()
        
        if not invalid_keys:
            return jsonify({
                'success': True,
                'message': '没有找到无效密钥',
                'deleted_count': 0
            })
        
        deleted_count = len(invalid_keys)
        
        # 批量删除无效密钥（关联的检测日志会因为cascade='all, delete-orphan'自动删除）
        for key in invalid_keys:
            db.session.delete(key)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'成功删除 {deleted_count} 个无效密钥',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/check-single', methods=['POST'])
def check_single():
    """检测单个密钥"""
    try:
        # 检查是否正在进行其他检测
        if scheduler_instance and scheduler_instance.is_checking():
            status = scheduler_instance.get_check_status()
            return jsonify({
                'success': False, 
                'message': f'检测被跳过：正在进行{status["check_type"]}',
                'is_checking': True
            }), 409
        
        data = request.get_json()
        key_value = data.get('key')
        
        if not key_value:
            return jsonify({'success': False, 'message': '未提供密钥'}), 400
        
        # 异步检测
        threading.Thread(
            target=lambda: scheduler_instance.check_single_key(key_value)
        ).start()
        
        return jsonify({'success': True, 'message': '检测已开始'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/check-all', methods=['POST'])
def check_all():
    """检测所有密钥"""
    try:
        # 检查是否正在进行其他检测
        if scheduler_instance and scheduler_instance.is_checking():
            status = scheduler_instance.get_check_status()
            return jsonify({
                'success': False, 
                'message': f'检测被跳过：正在进行{status["check_type"]}',
                'is_checking': True
            }), 409
        
        data = request.get_json() or {}
        force_all = data.get('force_all', False)
        
        # 异步检测
        threading.Thread(
            target=scheduler_instance.check_all_keys,
            args=(force_all,)
        ).start()
        
        mode_text = "强制全量检测" if force_all else "常规检测"
        return jsonify({'success': True, 'message': f'{mode_text}已开始'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/stop-check', methods=['POST'])
def stop_check():
    """停止当前检测"""
    try:
        if scheduler_instance:
            success, message = scheduler_instance.stop_checking()
            return jsonify({
                'success': success,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': '调度器未初始化'
            }), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/check-status', methods=['GET'])
def get_check_status():
    """获取当前检测状态"""
    try:
        if scheduler_instance:
            status = scheduler_instance.get_check_status()
            return jsonify({'success': True, 'status': status})
        else:
            return jsonify({
                'success': True, 
                'status': {
                    'is_checking': False,
                    'check_type': None,
                    'start_time': None,
                    'duration': 0,
                    'stop_requested': False
                }
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/settings', methods=['POST'])
def save_settings():
    """保存设置"""
    try:
        data = request.get_json()
        
        # 更新检测间隔
        check_interval = data.get('check_interval')
        if check_interval is not None:
            setting = Settings.query.filter_by(key='check_interval').first()
            if setting:
                setting.value = str(check_interval)
            else:
                setting = Settings(key='check_interval', value=str(check_interval))
                db.session.add(setting)
            
            # 更新调度器
            scheduler_instance.update_schedule(int(check_interval))
        
        # 更新代理设置
        proxy_url = data.get('proxy_url')
        if proxy_url is not None:
            setting = Settings.query.filter_by(key='proxy_url').first()
            if setting:
                setting.value = proxy_url
            else:
                setting = Settings(key='proxy_url', value=proxy_url)
                db.session.add(setting)
        
        # 更新并发设置
        concurrency = data.get('concurrency')
        if concurrency is not None:
            setting = Settings.query.filter_by(key='concurrency').first()
            if setting:
                setting.value = str(concurrency)
            else:
                setting = Settings(key='concurrency', value=str(concurrency))
                db.session.add(setting)
        
        # 更新检测策略
        check_strategy = data.get('check_strategy')
        if check_strategy is not None:
            setting = Settings.query.filter_by(key='check_strategy').first()
            if setting:
                setting.value = check_strategy
            else:
                setting = Settings(key='check_strategy', value=check_strategy)
                db.session.add(setting)
        
        # 更新API URL设置
        api_url = data.get('api_url')
        if api_url is not None:
            setting = Settings.query.filter_by(key='api_url').first()
            if setting:
                setting.value = api_url
            else:
                setting = Settings(key='api_url', value=api_url)
                db.session.add(setting)
        
        # 更新代理开关设置
        use_proxy = data.get('use_proxy')
        if use_proxy is not None:
            setting = Settings.query.filter_by(key='use_proxy').first()
            if setting:
                setting.value = use_proxy
            else:
                setting = Settings(key='use_proxy', value=use_proxy)
                db.session.add(setting)
        
        # 更新邮件设置
        email_enabled = data.get('email_enabled')
        if email_enabled is not None:
            setting = Settings.query.filter_by(key='email_enabled').first()
            if setting:
                setting.value = email_enabled
            else:
                setting = Settings(key='email_enabled', value=email_enabled)
                db.session.add(setting)
        
        # 更新3个邮箱地址
        for i in range(1, 4):
            email_key = f'email{i}'
            email_value = data.get(email_key)
            if email_value is not None:
                setting = Settings.query.filter_by(key=email_key).first()
                if setting:
                    setting.value = email_value
                else:
                    setting = Settings(key=email_key, value=email_value)
                    db.session.add(setting)
        
        email_password = data.get('email_password')
        if email_password is not None:
            setting = Settings.query.filter_by(key='email_password').first()
            if setting:
                setting.value = email_password
            else:
                setting = Settings(key='email_password', value=email_password)
                db.session.add(setting)
        
        db.session.commit()
        return jsonify({'success': True, 'message': '设置已保存'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/test-email', methods=['POST'])
def test_email():
    """测试邮件发送"""
    try:
        data = request.get_json()
        receiver_email = data.get('receiver_email')
        app_password = data.get('app_password')
        
        if not receiver_email or not app_password:
            return jsonify({
                'success': False, 
                'message': '缺少必要参数：接收邮箱或应用密码'
            }), 400
        
        # 异步发送测试邮件
        def send_test_async():
            if email_notifier:
                success, message = email_notifier.send_test_email(receiver_email, app_password)
                # 这里可以记录日志或其他处理
            else:
                # 记录错误
                logger = logging.getLogger('EmailNotifier')
                logger.error("邮件通知器未初始化")
            
        threading.Thread(target=send_test_async).start()
        
        return jsonify({
            'success': True, 
            'message': f'测试邮件已发送至 {receiver_email}，请检查邮箱（支持代理设置）'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """获取统计信息"""
    return jsonify(get_stats_data())

@app.route('/api/valid-keys')
def get_valid_keys():
    """获取有效密钥列表"""
    try:
        format_type = request.args.get('format', 'lines')  # lines 或 comma
        
        # 查询有效密钥
        valid_keys = ApiKey.query.filter_by(status='valid').all()
        key_values = [key.key_value for key in valid_keys]
        
        if format_type == 'comma':
            result = ','.join(key_values)
        else:  # lines
            result = '\n'.join(key_values)
        
        return jsonify({
            'success': True,
            'count': len(key_values),
            'format': format_type,
            'content': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/check-pending', methods=['POST'])
def check_pending():
    """只检测待检测（pending）密钥"""
    try:
        if scheduler_instance and scheduler_instance.is_checking():
            status = scheduler_instance.get_check_status()
            return jsonify({
                'success': False,
                'message': f'检测被跳过：正在进行{status["check_type"]}',
                'is_checking': True
            }), 409
        # 异步触发 pending 检测
        threading.Thread(target=scheduler_instance._check_pending_keys_async, daemon=True).start()
        return jsonify({'success': True, 'message': '已开始只检测待检测的密钥'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def get_stats_data():
    """获取统计数据"""
    valid_count = ApiKey.query.filter_by(status='valid').count()
    invalid_count = ApiKey.query.filter_by(status='invalid').count()
    pending_count = ApiKey.query.filter_by(status='pending').count()
    
    return {
        'valid_count': valid_count,
        'invalid_count': invalid_count,
        'pending_count': pending_count,
        'total_count': valid_count + invalid_count + pending_count
    }

def check_new_keys_async(keys):
    """异步检测新添加的密钥：改为触发并发批量检测pending密钥，统一进度条输出"""
    # 如果已有检测在进行，直接记录并返回
    if scheduler_instance and scheduler_instance.is_checking():
        with app.app_context():
            logger = logging.getLogger('KeyChecker')
            logger.warning("⚠️ 新密钥检测被跳过：另一个检测进程正在运行中")
        return

    # 触发批量pending并发检测（统一进度条与并发数设置）
    if scheduler_instance:
        threading.Thread(target=scheduler_instance._check_pending_keys_async, daemon=True).start()

# 优雅关闭
import atexit

def shutdown_scheduler():
    """关闭调度器"""
    if scheduler_instance:
        scheduler_instance.stop_scheduler()

atexit.register(shutdown_scheduler)

if __name__ == '__main__':
    # 确保数据库目录存在
    os.makedirs('instance', exist_ok=True)
    
    # 初始化数据库和调度器
    create_tables()
    
    print("=== Gemini API Key Checker Web 服务 ===")
    print("启动中...")
    print("访问地址: http://localhost:5000")
    print("按 Ctrl+C 退出")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True) 