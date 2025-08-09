from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import threading
import queue
import logging
import concurrent.futures
from models import db, ApiKey, CheckLog, Settings
from gemini_key_checker.checker import check_key

# 全局日志队列，用于实时推送日志到前端
log_queue = queue.Queue()

class LogHandler(logging.Handler):
    """自定义日志处理器，将日志推送到队列"""
    def emit(self, record):
        log_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'level': record.levelname,
            'message': self.format(record)
        }
        
        # 检查是否是可更新的日志（如进度条）
        if hasattr(record, 'update_id'):
            log_entry['update_id'] = record.update_id
            log_entry['is_update'] = True
        
        log_queue.put(log_entry)

class KeyChecker:
    """密钥检测类"""
    
    def __init__(self, app):
        self.app = app
        self.scheduler = BackgroundScheduler()
        
        # 添加互斥锁和状态管理
        self._check_lock = threading.Lock()
        self._is_checking = False
        self._current_check_type = None
        self._check_start_time = None
        self._stop_requested = False  # 添加停止标志
        self.current_check_id = None
        
        # 持续检测相关属性
        self._continuous_check_enabled = True  # 是否启用持续检测
        self._continuous_check_interval = 30  # 持续检测间隔（秒）
        
        # 设置日志
        self.logger = logging.getLogger('KeyChecker')
        self.logger.setLevel(logging.INFO)
        
        # 清除现有处理器
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 添加我们的处理器
        log_handler = LogHandler()
        log_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.logger.addHandler(log_handler)
    
    def is_checking(self):
        """检查是否正在进行检测"""
        return self._is_checking
    
    def stop_checking(self):
        """请求停止当前检测"""
        if self._is_checking:
            self._stop_requested = True
            self.logger.warning("🛑 收到停止检测请求，正在优雅停止...")
            return True, "停止请求已发送，检测将在当前批次完成后停止"
        else:
            return False, "当前没有正在进行的检测"
    
    def get_check_status(self):
        """获取当前检测状态信息"""
        if not self._is_checking:
            return {
                'is_checking': False,
                'check_type': None,
                'start_time': None,
                'duration': 0,
                'stop_requested': False
            }
        
        duration = 0
        if self._check_start_time:
            duration = int((datetime.now() - self._check_start_time).total_seconds())
        
        return {
            'is_checking': True,
            'check_type': self._current_check_type,
            'start_time': self._check_start_time.isoformat() if self._check_start_time else None,
            'duration': duration,
            'stop_requested': self._stop_requested
        }
    
    def _generate_progress_bar(self, processed, total, valid_count, invalid_count):
        """生成ASCII进度条"""
        if total == 0:
            return "📊 进度: [████████████████████] 100% (0/0) ✅ 0 ❌ 0"
        
        percent = (processed / total) * 100
        filled_blocks = int((processed / total) * 20)  # 20个字符的进度条
        empty_blocks = 20 - filled_blocks
        
        progress_chars = "█" * filled_blocks + "░" * empty_blocks
        
        return f"📊 进度: [{progress_chars}] {percent:5.1f}% ({processed}/{total}) ✅ {valid_count} ❌ {invalid_count}"
    
    def _log_progress_update(self, processed, total, valid_count, invalid_count):
        """记录可更新的进度条日志"""
        progress_message = self._generate_progress_bar(processed, total, valid_count, invalid_count)
        
        # 创建自定义的日志记录，带有更新ID
        record = self.logger.makeRecord(
            name=self.logger.name,
            level=logging.INFO,
            fn='',
            lno=0,
            msg=progress_message,
            args=(),
            exc_info=None
        )
        
        # 添加更新ID，用于前端识别和更新同一个进度条
        record.update_id = self.current_check_id
        
        # 发送日志
        self.logger.handle(record)
    
    def _send_email_notification(self, total: int, valid: int, invalid: int, 
                                processed: int, check_type: str, stopped: bool = False):
        """发送邮件通知"""
        try:
            # 获取邮件设置
            email_enabled_setting = Settings.query.filter_by(key='email_enabled').first()
            email_enabled = email_enabled_setting.value.lower() == 'true' if email_enabled_setting else False
            
            if not email_enabled:
                return  # 邮件通知未启用
            
            # 获取应用密码
            email_password_setting = Settings.query.filter_by(key='email_password').first()
            email_password = email_password_setting.value if email_password_setting else ""
            
            # 获取接收邮箱列表（兼容 email1/email2/email3）
            receivers = []
            try:
                from app import email_notifier
                if email_notifier:
                    receivers = email_notifier._get_email_receivers()
            except Exception:
                receivers = []
            
            if not receivers:
                self.logger.warning("📧 邮件通知已启用但未配置接收邮箱（请在设置中填写 email1/email2/email3）")
                return
            if not email_password:
                self.logger.warning("📧 邮件通知已启用但缺少应用密码")
                return
            
            # 计算运行时长
            duration = 0
            if self._check_start_time:
                duration = int((datetime.now() - self._check_start_time).total_seconds())
            
            # 构建检测结果
            check_results = {
                'total': total,
                'valid': valid,
                'invalid': invalid,
                'processed': processed,
                'start_time': self._check_start_time or datetime.now(),
                'duration': duration,
                'stopped': stopped
            }
            
            # 异步发送邮件（避免阻塞检测流程）
            threading.Thread(
                target=self._send_email_async,
                args=("__MULTI__", email_password, check_results, check_type)
            ).start()
            
        except Exception as e:
            self.logger.error(f"准备邮件通知时发生错误: {str(e)}")
    
    def _send_email_async(self, receiver_email: str, app_password: str, 
                         check_results: dict, check_type: str):
        """异步发送邮件"""
        try:
            # 导入邮件通知器（避免循环导入）
            from app import email_notifier
            
            if email_notifier:
                # 当 receiver_email 为特殊标识时，内部会读取 email1/email2/email3 列表
                success, message = email_notifier.send_check_result_email(
                    receiver_email=receiver_email,
                    app_password=app_password,
                    check_results=check_results,
                    check_type=check_type
                )
                
                if success:
                    self.logger.info("📧 检测报告邮件发送成功（多收件人）")
                else:
                    self.logger.error(f"📧 检测报告邮件发送失败: {message}")
            else:
                self.logger.error("📧 邮件通知器未初始化")
                
        except Exception as e:
            self.logger.error(f"发送邮件时发生异常: {str(e)}")
        
    def start_scheduler(self):
        """启动定时调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
            self.logger.info("🚀 定时调度器已启动")
            
            # 启动持续检测任务
            if self._continuous_check_enabled:
                self.scheduler.add_job(
                    func=self._continuous_check_pending_keys,
                    trigger=IntervalTrigger(seconds=self._continuous_check_interval),
                    id='continuous_check_job',
                    name='持续检测待处理密钥',
                    replace_existing=True
                )
                self.logger.info(f"🔄 持续检测已启用，检测间隔: {self._continuous_check_interval} 秒")
            
            self.logger.info("💡 系统准备就绪，等待任务...")
            
            # 发送欢迎消息
            welcome_msg = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'level': 'INFO',
                'message': '🎉 Gemini Key Checker 服务已启动！'
            }
            log_queue.put(welcome_msg)
    
    def stop_scheduler(self):
        """停止定时调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info("定时调度器已停止")
    
    def update_schedule(self, interval_minutes):
        """更新检测间隔"""
        # 移除现有任务
        self.scheduler.remove_all_jobs()
        
        if interval_minutes > 0:
            # 添加新任务
            self.scheduler.add_job(
                func=self.check_all_keys,
                trigger=IntervalTrigger(minutes=interval_minutes),
                id='key_check_job',
                name='定期检测密钥',
                replace_existing=True
            )
            self.logger.info(f"已设置定时检测：每 {interval_minutes} 分钟执行一次")
        else:
            self.logger.info("已禁用定时检测")
    
    def check_all_keys(self, force_all=False):
        """检测所有待检测的密钥"""
        # 检查是否已有检测在进行
        if not self._check_lock.acquire(blocking=False):
            check_type = "强制全量检测" if force_all else "常规检测"
            self.logger.warning(f"⚠️ {check_type}被跳过：另一个检测进程正在运行中")
            return
        
        try:
            # 设置检测状态
            self._is_checking = True
            self._current_check_type = "强制全量检测" if force_all else "常规检测"
            self._check_start_time = datetime.now()
            self._stop_requested = False  # 重置停止标志
            
            with self.app.app_context():
                try:
                    # 检查停止请求
                    if self._stop_requested:
                        self.logger.info("🛑 检测在开始前被停止")
                        return
                    
                    # 获取设置
                    proxy_setting = Settings.query.filter_by(key='proxy_url').first()
                    proxy_url = proxy_setting.value if proxy_setting else "http://127.0.0.1:7890"
                    
                    use_proxy_setting = Settings.query.filter_by(key='use_proxy').first()
                    use_proxy = use_proxy_setting.value.lower() == 'true' if use_proxy_setting else True
                    
                    api_url_setting = Settings.query.filter_by(key='api_url').first()
                    api_url = api_url_setting.value if api_url_setting else ""
                    
                    concurrency_setting = Settings.query.filter_by(key='concurrency').first()
                    concurrency = int(concurrency_setting.value) if concurrency_setting else 10
                    
                    # 获取所有需要检测的密钥
                    if force_all:
                        # 强制检测所有密钥
                        keys_to_check = ApiKey.query.all()
                        self.logger.info("🔥 执行强制全量检测模式")
                    else:
                        # 获取检测策略设置
                        strategy_setting = Settings.query.filter_by(key='check_strategy').first()
                        check_strategy = strategy_setting.value if strategy_setting else 'all'
                        
                        # 根据策略获取需要检测的密钥
                        if check_strategy == 'all':
                            # 检测所有有效和待检测的密钥（排除已失效的）
                            keys_to_check = ApiKey.query.filter(
                                ApiKey.status.in_(['valid', 'pending'])
                            ).all()
                            self.logger.info("📋 执行全量检测模式（排除已失效密钥）")
                        elif check_strategy == 'incremental':
                            # 只检测新的或24小时内未检测的密钥（排除已失效的）
                            from datetime import timedelta
                            cutoff_time = datetime.utcnow() - timedelta(hours=24)
                            keys_to_check = ApiKey.query.filter(
                                (
                                    (ApiKey.status == 'pending') | 
                                    (ApiKey.last_checked.is_(None)) |
                                    ((ApiKey.status == 'valid') & (ApiKey.last_checked < cutoff_time))
                                )
                            ).all()
                            self.logger.info("⚡ 执行增量检测模式（24小时内未检测，排除已失效密钥）")
                        else:
                            # 默认检测有效和待检测的密钥
                            keys_to_check = ApiKey.query.filter(
                                ApiKey.status.in_(['valid', 'pending'])
                            ).all()
                            self.logger.info("📋 执行默认检测模式（排除已失效密钥）")
                    
                    if not keys_to_check:
                        self.logger.info("没有需要检测的密钥")
                        return
                    
                    # 再次检查停止请求
                    if self._stop_requested:
                        self.logger.info("🛑 检测在获取密钥列表后被停止")
                        return
                    
                    self.logger.info(f"🔍 开始检测 {len(keys_to_check)} 个密钥，并发数: {concurrency}")
                    
                    valid_count = 0
                    invalid_count = 0
                    processed_count = 0
                    total_count = len(keys_to_check)
                    
                    # 生成唯一的检测会话ID
                    import uuid
                    self.current_check_id = f"check_{uuid.uuid4().hex[:8]}"
                    
                    # 显示初始进度条
                    self._log_progress_update(0, total_count, 0, 0)
                    
                    # 使用线程池并发检测
                    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                        # 提交所有检测任务
                        future_to_key = {
                            executor.submit(check_key, api_key.key_value, proxy_url, use_proxy, api_url): api_key 
                            for api_key in keys_to_check
                        }
                        
                        # 处理完成的任务
                        for future in concurrent.futures.as_completed(future_to_key):
                            # 检查停止请求
                            if self._stop_requested:
                                self.logger.warning(f"🛑 检测被用户停止！已处理 {processed_count}/{total_count} 个密钥")
                                # 最后一帧进度刷新
                                self._log_progress_update(processed_count, total_count, valid_count, invalid_count)
                                # 取消剩余的任务
                                for remaining_future in future_to_key:
                                    if not remaining_future.done():
                                        remaining_future.cancel()
                                break
                            
                            api_key = future_to_key[future]
                            try:
                                is_valid, message = future.result()
                                
                                # 更新密钥状态
                                api_key.status = 'valid' if is_valid else 'invalid'
                                api_key.last_checked = datetime.utcnow()
                                api_key.error_message = None if is_valid else message
                                
                                # 创建检测记录
                                check_log = CheckLog(
                                    api_key_id=api_key.id,
                                    status='valid' if is_valid else 'invalid',
                                    message=message
                                )
                                db.session.add(check_log)
                                
                                processed_count += 1
                                if is_valid:
                                    valid_count += 1
                                else:
                                    invalid_count += 1
                                
                                # 更新进度条
                                self._log_progress_update(processed_count, total_count, valid_count, invalid_count)
                                    
                            except Exception as exc:
                                # 处理单个检测的异常
                                api_key.status = 'invalid'
                                api_key.last_checked = datetime.utcnow()
                                api_key.error_message = f"检测异常: {str(exc)}"
                                
                                check_log = CheckLog(
                                    api_key_id=api_key.id,
                                    status='invalid',
                                    message=f"检测异常: {str(exc)}"
                                )
                                db.session.add(check_log)
                                
                                processed_count += 1
                                invalid_count += 1
                                
                                # 更新进度条
                                self._log_progress_update(processed_count, total_count, valid_count, invalid_count)
                    
                    db.session.commit()
                    
                    # 检查是否被停止
                    # 强制刷新最终进度
                    self._log_progress_update(processed_count, total_count, valid_count, invalid_count)
                    if self._stop_requested:
                        self.logger.info(f"🛑 检测已停止！部分完成: {processed_count}/{total_count} 个密钥，有效: {valid_count} 个，无效: {invalid_count} 个")
                    else:
                        self.logger.info(f"🎉 检测完成！总计: {processed_count} 个，有效: {valid_count} 个，无效: {invalid_count} 个")
                    
                    # 发送邮件通知
                    self._send_email_notification(
                        total=total_count,
                        valid=valid_count,
                        invalid=invalid_count,
                        processed=processed_count,
                        check_type=self._current_check_type,
                        stopped=self._stop_requested
                    )
                    
                except Exception as e:
                    db.session.rollback()
                    self.logger.error(f"检测过程中发生错误: {str(e)}")
        finally:
            # 无论如何都要清除检测状态
            self._is_checking = False
            self._current_check_type = None
            self._check_start_time = None
            self._stop_requested = False
            self.current_check_id = None
            self._check_lock.release()
    
    def _continuous_check_pending_keys(self):
        """持续检测pending状态的密钥"""
        # 如果已经有检测在进行，跳过
        if self._is_checking:
            return
            
        try:
            with self.app.app_context():
                # 查找pending状态的密钥数量
                pending_count = ApiKey.query.filter_by(status='pending').count()
                
                if pending_count > 0:
                    # 有待检测的密钥，触发检测
                    self.logger.info(f"🔍 发现 {pending_count} 个待检测密钥，自动启动检测...")
                    
                    # 异步启动检测，避免阻塞持续检测任务
                    threading.Thread(
                        target=self._check_pending_keys_async,
                        daemon=True
                    ).start()
                    
        except Exception as e:
            self.logger.error(f"持续检测过程中发生错误: {str(e)}")
    
    def _check_pending_keys_async(self):
        """异步检测所有pending状态的密钥"""
        # 检查是否已有检测在进行
        if not self._check_lock.acquire(blocking=False):
            return  # 如果有其他检测在进行，直接返回
        
        try:
            # 设置检测状态
            self._is_checking = True
            self._current_check_type = "持续检测（pending密钥）"
            self._check_start_time = datetime.now()
            self._stop_requested = False
            
            with self.app.app_context():
                try:
                    # 获取设置
                    proxy_setting = Settings.query.filter_by(key='proxy_url').first()
                    proxy_url = proxy_setting.value if proxy_setting else "http://127.0.0.1:7890"
                    
                    use_proxy_setting = Settings.query.filter_by(key='use_proxy').first()
                    use_proxy = use_proxy_setting.value.lower() == 'true' if use_proxy_setting else True
                    
                    api_url_setting = Settings.query.filter_by(key='api_url').first()
                    api_url = api_url_setting.value if api_url_setting else ""
                    
                    concurrency_setting = Settings.query.filter_by(key='concurrency').first()
                    concurrency = int(concurrency_setting.value) if concurrency_setting else 10
                    
                    # 只获取pending状态的密钥
                    keys_to_check = ApiKey.query.filter_by(status='pending').all()
                    
                    if not keys_to_check:
                        return
                    
                    self.logger.info(f"🔍 开始检测 {len(keys_to_check)} 个待检测密钥，并发数: {concurrency}")
                    
                    valid_count = 0
                    invalid_count = 0
                    processed_count = 0
                    total_count = len(keys_to_check)
                    
                    # 生成唯一的检测会话ID
                    import uuid
                    self.current_check_id = f"continuous_{uuid.uuid4().hex[:8]}"
                    
                    # 显示初始进度条
                    self._log_progress_update(0, total_count, 0, 0)
                    
                    # 使用线程池并发检测
                    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                        # 提交所有检测任务
                        future_to_key = {
                            executor.submit(check_key, api_key.key_value, proxy_url, use_proxy, api_url): api_key 
                            for api_key in keys_to_check
                        }
                        
                        # 处理完成的任务
                        for future in concurrent.futures.as_completed(future_to_key):
                            # 检查停止请求
                            if self._stop_requested:
                                self.logger.warning(f"🛑 持续检测被停止！已处理 {processed_count}/{total_count} 个密钥")
                                # 最后一帧进度刷新
                                self._log_progress_update(processed_count, total_count, valid_count, invalid_count)
                                # 取消剩余任务，加速停止响应
                                for remaining_future in future_to_key:
                                    if not remaining_future.done():
                                        remaining_future.cancel()
                                break
                            
                            api_key = future_to_key[future]
                            try:
                                is_valid, message = future.result()
                                
                                # 更新密钥状态
                                api_key.status = 'valid' if is_valid else 'invalid'
                                api_key.last_checked = datetime.utcnow()
                                api_key.error_message = None if is_valid else message
                                
                                # 创建检测记录
                                check_log = CheckLog(
                                    api_key_id=api_key.id,
                                    status='valid' if is_valid else 'invalid',
                                    message=message
                                )
                                db.session.add(check_log)
                                
                                processed_count += 1
                                if is_valid:
                                    valid_count += 1
                                else:
                                    invalid_count += 1
                                
                                # 更新进度条
                                self._log_progress_update(processed_count, total_count, valid_count, invalid_count)
                                    
                            except Exception as exc:
                                # 处理单个检测的异常
                                api_key.status = 'invalid'
                                api_key.last_checked = datetime.utcnow()
                                api_key.error_message = f"检测异常: {str(exc)}"
                                
                                check_log = CheckLog(
                                    api_key_id=api_key.id,
                                    status='invalid',
                                    message=f"检测异常: {str(exc)}"
                                )
                                db.session.add(check_log)
                                
                                processed_count += 1
                                invalid_count += 1
                                
                                # 更新进度条
                                self._log_progress_update(processed_count, total_count, valid_count, invalid_count)
                    
                    db.session.commit()
                    
                    # 强制刷新最终进度
                    self._log_progress_update(processed_count, total_count, valid_count, invalid_count)
                    # 检查是否被停止
                    if self._stop_requested:
                        self.logger.info(f"🛑 持续检测已停止！部分完成: {processed_count}/{total_count} 个密钥，有效: {valid_count} 个，无效: {invalid_count} 个")
                    else:
                        self.logger.info(f"✅ 持续检测完成！总计: {processed_count} 个，有效: {valid_count} 个，无效: {invalid_count} 个")
                    
                except Exception as e:
                    db.session.rollback()
                    self.logger.error(f"持续检测过程中发生错误: {str(e)}")
        finally:
            # 清除检测状态
            self._is_checking = False
            self._current_check_type = None
            self._check_start_time = None
            self._stop_requested = False
            self._check_lock.release()
    
    def check_single_key(self, key_value):
        """检测单个密钥"""
        # 检查是否已有检测在进行
        if not self._check_lock.acquire(blocking=False):
            self.logger.warning(f"⚠️ 单个密钥检测被跳过：另一个检测进程正在运行中")
            return False, "另一个检测进程正在运行中"
        
        try:
            # 设置检测状态
            self._is_checking = True
            self._current_check_type = "单个密钥检测"
            self._check_start_time = datetime.now()
            
            with self.app.app_context():
                try:
                    # 获取设置
                    proxy_setting = Settings.query.filter_by(key='proxy_url').first()
                    proxy_url = proxy_setting.value if proxy_setting else "http://127.0.0.1:7890"
                    
                    use_proxy_setting = Settings.query.filter_by(key='use_proxy').first()
                    use_proxy = use_proxy_setting.value.lower() == 'true' if use_proxy_setting else True
                    
                    api_url_setting = Settings.query.filter_by(key='api_url').first()
                    api_url = api_url_setting.value if api_url_setting else ""
                    
                    is_valid, message = check_key(key_value, proxy_url, use_proxy, api_url)
                    
                    # 查找或创建密钥记录
                    api_key = ApiKey.query.filter_by(key_value=key_value).first()
                    if not api_key:
                        api_key = ApiKey(key_value=key_value)
                        db.session.add(api_key)
                    
                    # 更新状态
                    api_key.status = 'valid' if is_valid else 'invalid'
                    api_key.last_checked = datetime.utcnow()
                    api_key.error_message = None if is_valid else message
                    
                    # 创建检测记录
                    check_log = CheckLog(
                        api_key_id=api_key.id,
                        status='valid' if is_valid else 'invalid',
                        message=message
                    )
                    db.session.add(check_log)
                    db.session.commit()
                    
                    result_text = "检测通过" if is_valid else f"检测失败: {message}"
                    self.logger.info(f"{'✅' if is_valid else '❌'} 密钥 {key_value[:10]}... {result_text}")
                    
                    return is_valid, message
                    
                except Exception as e:
                    db.session.rollback()
                    self.logger.error(f"检测密钥时发生错误: {str(e)}")
                    return False, f"检测过程中发生错误: {str(e)}"
        finally:
            # 无论如何都要清除检测状态
            self._is_checking = False
            self._current_check_type = None
            self._check_start_time = None
            self._check_lock.release()

# 全局调度器实例
key_checker = None

def init_scheduler(app):
    """初始化调度器"""
    global key_checker
    key_checker = KeyChecker(app)
    return key_checker

def get_log_stream():
    """获取日志流生成器"""
    import json
    while True:
        try:
            log_entry = log_queue.get(timeout=1)
            yield f"data: {json.dumps(log_entry)}\n\n"
        except queue.Empty:
            yield f"data: {json.dumps({'heartbeat': True})}\n\n" 