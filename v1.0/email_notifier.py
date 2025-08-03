#!/usr/bin/env python3
"""
邮件通知模块
支持Gmail SMTP发送检测结果通知邮件，集成代理支持
"""

import smtplib
import logging
import socket
import socks
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

class EmailNotifier:
    """Gmail邮件通知类，支持代理连接"""
    
    def __init__(self, app=None):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = "aa1xuyuhuayhm@gmail.com"
        self.sender_name = "Gemini Key Checker"
        self.app = app
        
        # 设置日志
        self.logger = logging.getLogger('EmailNotifier')
        self.logger.setLevel(logging.INFO)
    
    def _get_proxy_settings(self) -> Tuple[bool, str]:
        """
        从数据库获取代理设置
        
        Returns:
            (是否使用代理, 代理URL)
        """
        if not self.app:
            return False, ""
            
        try:
            from models import Settings
            with self.app.app_context():
                # 获取代理开关设置
                use_proxy_setting = Settings.query.filter_by(key='use_proxy').first()
                use_proxy = use_proxy_setting.value.lower() == 'true' if use_proxy_setting else False
                
                # 获取代理URL设置
                proxy_setting = Settings.query.filter_by(key='proxy_url').first()
                proxy_url = proxy_setting.value if proxy_setting else "http://127.0.0.1:7890"
                
                return use_proxy, proxy_url
        except Exception as e:
            self.logger.warning(f"获取代理设置失败，使用默认设置: {str(e)}")
            return False, ""
    
    def _get_email_receivers(self) -> List[str]:
        """
        从数据库获取邮箱接收列表
        
        Returns:
            邮箱地址列表
        """
        if not self.app:
            return []
            
        try:
            import json
            from models import Settings
            with self.app.app_context():
                receivers = []
                
                # 获取主要邮箱
                primary_setting = Settings.query.filter_by(key='email_receiver').first()
                primary_email = primary_setting.value.strip() if primary_setting else ""
                if primary_email:
                    receivers.append(primary_email)
                
                # 获取额外邮箱
                additional_setting = Settings.query.filter_by(key='additional_emails').first()
                additional_emails_json = additional_setting.value if additional_setting else "[]"
                
                try:
                    additional_emails = json.loads(additional_emails_json)
                    if isinstance(additional_emails, list):
                        for email in additional_emails:
                            email = email.strip()
                            if email and email not in receivers:
                                receivers.append(email)
                except json.JSONDecodeError:
                    self.logger.warning("额外邮箱设置JSON格式错误")
                
                return receivers
        except Exception as e:
            self.logger.warning(f"获取邮箱设置失败: {str(e)}")
            return []
    
    def _create_smtp_connection_with_proxy(self, proxy_url: str) -> smtplib.SMTP:
        """
        通过代理创建SMTP连接
        
        Args:
            proxy_url: 代理服务器URL
            
        Returns:
            已连接的SMTP对象
            
        Raises:
            Exception: 代理连接失败时抛出异常
        """
        try:
            # 解析代理URL
            parsed_proxy = urlparse(proxy_url)
            proxy_host = parsed_proxy.hostname
            proxy_port = parsed_proxy.port or 7890
            
            self.logger.info(f"代理连接详情: {proxy_host}:{proxy_port} (类型: {parsed_proxy.scheme})")
            
            # 创建代理socket
            proxy_socket = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
            
            # 根据代理类型设置
            if parsed_proxy.scheme.lower() == 'socks5':
                proxy_socket.set_proxy(socks.SOCKS5, proxy_host, proxy_port)
            elif parsed_proxy.scheme.lower() == 'socks4':
                proxy_socket.set_proxy(socks.SOCKS4, proxy_host, proxy_port)
            elif parsed_proxy.scheme.lower() == 'http':
                # HTTP代理
                proxy_socket.set_proxy(socks.HTTP, proxy_host, proxy_port)
            else:
                # 默认使用HTTP代理
                proxy_socket.set_proxy(socks.HTTP, proxy_host, proxy_port)
            
            # 设置超时
            proxy_socket.settimeout(30)
            
            # 连接到SMTP服务器
            self.logger.info(f"正在通过代理连接到 {self.smtp_server}:{self.smtp_port}")
            proxy_socket.connect((self.smtp_server, self.smtp_port))
            
            # 创建SMTP对象
            smtp = smtplib.SMTP()
            smtp.sock = proxy_socket
            smtp._host = self.smtp_server
            smtp.timeout = 30
            
            # 重要：需要手动处理SMTP握手
            smtp.file = smtp.sock.makefile('rb')
            smtp.sock.settimeout(smtp.timeout)
            
            # 读取服务器的欢迎消息
            code, msg = smtp.getreply()
            if code != 220:
                raise smtplib.SMTPConnectError(code, msg)
            
            self.logger.info(f"SMTP服务器响应: {code} {msg}")
            
            return smtp
            
        except Exception as e:
            raise Exception(f"代理连接失败 ({proxy_url}): {str(e)}")
    
    def send_check_result_email(self, receiver_email: str, app_password: str, 
                               check_results: Dict, check_type: str = "定时检测") -> tuple[bool, str]:
        """
        发送检测结果邮件到多个邮箱
        
        Args:
            receiver_email: 主要接收邮箱（向后兼容参数）
            app_password: Gmail应用密码
            check_results: 检测结果字典
            check_type: 检测类型
            
        Returns:
            (成功状态, 消息)
        """
        try:
            # 获取所有接收邮箱
            receivers = self._get_email_receivers()
            if not receivers:
                return False, "未配置接收邮箱"
            
            # 创建邮件内容
            subject = f"🔑 Gemini密钥检测报告 - {check_type}"
            html_body = self._generate_html_report(check_results, check_type)
            text_body = self._generate_text_report(check_results, check_type)
            
            # 发送到所有邮箱
            return self._send_email_to_multiple(
                receivers=receivers,
                app_password=app_password,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            error_msg = f"发送检测结果邮件失败: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def send_test_email(self, receiver_email: str, app_password: str) -> tuple[bool, str]:
        """
        发送测试邮件到多个邮箱
        
        Args:
            receiver_email: 主要接收邮箱（向后兼容参数）
            app_password: Gmail应用密码
            
        Returns:
            (成功状态, 消息)
        """
        try:
            # 获取所有接收邮箱
            receivers = self._get_email_receivers()
            if not receivers:
                return False, "未配置接收邮箱"
            
            subject = "🧪 Gemini Key Checker 测试邮件"
            html_body = self._generate_test_html()
            text_body = "这是一封测试邮件，如果您收到此邮件，说明邮件配置正确！"
            
            return self._send_email_to_multiple(
                receivers=receivers,
                app_password=app_password,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            error_msg = f"发送测试邮件失败: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _send_email_to_multiple(self, receivers: List[str], app_password: str,
                               subject: str, html_body: str, text_body: str) -> tuple[bool, str]:
        """
        发送邮件到多个接收邮箱
        
        Args:
            receivers: 接收邮箱列表
            app_password: Gmail应用密码
            subject: 邮件主题
            html_body: HTML邮件内容
            text_body: 纯文本邮件内容
            
        Returns:
            (成功状态, 消息)
        """
        if not receivers:
            return False, "没有配置接收邮箱"
        
        success_count = 0
        failed_emails = []
        
        for receiver_email in receivers:
            try:
                success, message = self._send_email(
                    receiver_email=receiver_email,
                    app_password=app_password,
                    subject=subject,
                    html_body=html_body,
                    text_body=text_body
                )
                
                if success:
                    success_count += 1
                    self.logger.info(f"邮件发送成功至 {receiver_email}")
                else:
                    failed_emails.append(f"{receiver_email}: {message}")
                    self.logger.error(f"邮件发送失败至 {receiver_email}: {message}")
                    
            except Exception as e:
                failed_emails.append(f"{receiver_email}: {str(e)}")
                self.logger.error(f"邮件发送异常至 {receiver_email}: {str(e)}")
        
        # 生成结果消息
        total_count = len(receivers)
        if success_count == total_count:
            return True, f"邮件发送成功至所有 {total_count} 个邮箱"
        elif success_count > 0:
            return True, f"邮件发送成功至 {success_count}/{total_count} 个邮箱，失败: {'; '.join(failed_emails)}"
        else:
            return False, f"邮件发送失败至所有邮箱: {'; '.join(failed_emails)}"
    
    def _send_email(self, receiver_email: str, app_password: str, 
                   subject: str, html_body: str, text_body: str) -> tuple[bool, str]:
        """
        发送邮件的核心方法，支持代理连接
        
        Args:
            receiver_email: 接收邮箱
            app_password: Gmail应用密码
            subject: 邮件主题
            html_body: HTML邮件内容
            text_body: 纯文本邮件内容
            
        Returns:
            (成功状态, 消息)
        """
        try:
            # 创建邮件对象
            msg = MIMEMultipart('alternative')
            msg['From'] = formataddr((self.sender_name, self.sender_email))
            msg['To'] = receiver_email
            msg['Subject'] = subject
            
            # 添加纯文本和HTML内容
            part1 = MIMEText(text_body, 'plain', 'utf-8')
            part2 = MIMEText(html_body, 'html', 'utf-8')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # 获取代理设置
            use_proxy, proxy_url = self._get_proxy_settings()
            
            # 创建SMTP连接（根据代理设置）
            server = None
            if use_proxy and proxy_url:
                self.logger.info(f"使用代理发送邮件: {proxy_url}")
                try:
                    server = self._create_smtp_connection_with_proxy(proxy_url)
                    self.logger.info("代理连接建立成功，开始STARTTLS...")
                    server.starttls()  # 启用安全传输
                    self.logger.info("STARTTLS成功")
                except Exception as proxy_error:
                    # 代理连接失败，尝试直连
                    self.logger.warning(f"代理连接失败，尝试直连: {str(proxy_error)}")
                    if server:
                        try:
                            server.quit()
                        except:
                            pass
                    server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                    server.starttls()
            else:
                self.logger.info("使用直连发送邮件")
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()  # 启用安全传输
            
            try:
                # 登录并发送邮件
                server.login(self.sender_email, app_password)
                
                # 发送邮件
                text = msg.as_string()
                server.sendmail(self.sender_email, receiver_email, text)
                server.quit()
                
                success_msg = f"邮件发送成功至 {receiver_email}"
                if use_proxy and proxy_url:
                    success_msg += f" (通过代理: {proxy_url})"
                self.logger.info(success_msg)
                return True, success_msg
                
            finally:
                # 确保连接关闭
                try:
                    server.quit()
                except:
                    pass
            
        except smtplib.SMTPAuthenticationError:
            error_msg = "邮件认证失败，请检查Gmail应用密码是否正确"
            self.logger.error(error_msg)
            return False, error_msg
        except smtplib.SMTPRecipientsRefused:
            error_msg = f"接收邮箱地址无效: {receiver_email}"
            self.logger.error(error_msg)
            return False, error_msg
        except smtplib.SMTPException as e:
            error_msg = f"SMTP错误: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
        except socket.timeout:
            error_msg = "邮件发送超时，请检查网络连接或代理设置"
            self.logger.error(error_msg)
            return False, error_msg
        except ConnectionRefusedError:
            error_msg = "连接被拒绝，请检查代理服务器是否正常运行"
            self.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            # 检查是否是WinError 10060
            if "10060" in str(e) or "由于连接方在一段时间后没有正确答复" in str(e):
                error_msg = "连接超时错误，请检查代理设置或网络连接。如果在受限网络环境中，请确保代理已正确配置并启用"
            else:
                error_msg = f"发送邮件时发生未知错误: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _generate_html_report(self, check_results: Dict, check_type: str) -> str:
        """生成HTML格式的检测报告"""
        total = check_results.get('total', 0)
        valid = check_results.get('valid', 0)
        invalid = check_results.get('invalid', 0)
        processed = check_results.get('processed', 0)
        start_time = check_results.get('start_time', datetime.now())
        duration = check_results.get('duration', 0)
        stopped = check_results.get('stopped', False)
        
        # 计算百分比
        valid_percent = (valid / total * 100) if total > 0 else 0
        invalid_percent = (invalid / total * 100) if total > 0 else 0
        
        # 状态标识
        status_icon = "🛑" if stopped else "✅"
        status_text = "检测被停止" if stopped else "检测完成"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }}
        .content {{ padding: 20px; }}
        .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .stat-item {{ text-align: center; padding: 15px; border-radius: 6px; }}
        .stat-valid {{ background-color: #d4edda; color: #155724; }}
        .stat-invalid {{ background-color: #f8d7da; color: #721c24; }}
        .stat-total {{ background-color: #e2e3e5; color: #383d41; }}
        .progress-bar {{ background-color: #e9ecef; border-radius: 10px; height: 20px; margin: 10px 0; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #28a745, #20c997); transition: width 0.3s ease; }}
        .info-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .info-table th, .info-table td {{ padding: 10px; text-align: left; border-bottom: 1px solid #dee2e6; }}
        .info-table th {{ background-color: #f8f9fa; font-weight: bold; }}
        .footer {{ background-color: #f8f9fa; padding: 15px; border-radius: 0 0 8px 8px; text-align: center; color: #6c757d; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔑 Gemini API 密钥检测报告</h1>
            <p>{status_icon} {status_text} - {check_type}</p>
        </div>
        
        <div class="content">
            <div class="stats">
                <div class="stat-item stat-valid">
                    <h3>{valid}</h3>
                    <p>有效密钥</p>
                    <small>{valid_percent:.1f}%</small>
                </div>
                <div class="stat-item stat-invalid">
                    <h3>{invalid}</h3>
                    <p>无效密钥</p>
                    <small>{invalid_percent:.1f}%</small>
                </div>
                <div class="stat-item stat-total">
                    <h3>{processed}/{total}</h3>
                    <p>已处理</p>
                    <small>总计</small>
                </div>
            </div>
            
            <div class="progress-bar">
                <div class="progress-fill" style="width: {(processed/total*100) if total > 0 else 0:.1f}%;"></div>
            </div>
            
            <table class="info-table">
                <tr><th>检测类型</th><td>{check_type}</td></tr>
                <tr><th>开始时间</th><td>{start_time.strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
                <tr><th>运行时长</th><td>{duration} 秒</td></tr>
                <tr><th>检测状态</th><td>{status_text}</td></tr>
                <tr><th>处理进度</th><td>{processed}/{total} ({(processed/total*100) if total > 0 else 0:.1f}%)</td></tr>
            </table>
            
            {'<p style="color: #856404; background-color: #fff3cd; padding: 10px; border-radius: 5px; border-left: 4px solid #ffc107;"><strong>注意:</strong> 检测过程被用户手动停止，结果可能不完整。</p>' if stopped else ''}
        </div>
        
        <div class="footer">
            <p>此邮件由 Gemini Key Checker 系统自动发送</p>
            <p>发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
        """
        return html
    
    def _generate_text_report(self, check_results: Dict, check_type: str) -> str:
        """生成纯文本格式的检测报告"""
        total = check_results.get('total', 0)
        valid = check_results.get('valid', 0)
        invalid = check_results.get('invalid', 0)
        processed = check_results.get('processed', 0)
        start_time = check_results.get('start_time', datetime.now())
        duration = check_results.get('duration', 0)
        stopped = check_results.get('stopped', False)
        
        status_text = "检测被停止" if stopped else "检测完成"
        
        text = f"""
🔑 Gemini API 密钥检测报告

{status_text} - {check_type}

📊 检测统计:
- 总密钥数: {total}
- 有效密钥: {valid} ({(valid/total*100) if total > 0 else 0:.1f}%)
- 无效密钥: {invalid} ({(invalid/total*100) if total > 0 else 0:.1f}%)
- 已处理: {processed}/{total}

⏱️ 检测信息:
- 检测类型: {check_type}
- 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}
- 运行时长: {duration} 秒
- 检测状态: {status_text}

{'⚠️ 注意: 检测过程被用户手动停止，结果可能不完整。' if stopped else ''}

---
此邮件由 Gemini Key Checker 系统自动发送
发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        return text.strip()
    
    def _generate_test_html(self) -> str:
        """生成测试邮件的HTML内容"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 500px; margin: 0 auto; background-color: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; text-align: center; }}
        .content {{ padding: 30px; text-align: center; }}
        .success-icon {{ font-size: 48px; margin-bottom: 20px; }}
        .footer {{ background-color: #f8f9fa; padding: 15px; border-radius: 0 0 8px 8px; text-align: center; color: #6c757d; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 测试邮件</h1>
            <p>Gemini Key Checker</p>
        </div>
        
        <div class="content">
            <div class="success-icon">✅</div>
            <h2>邮件配置测试成功！</h2>
            <p>如果您收到此邮件，说明您的邮件通知配置已正确设置。</p>
            <p>系统将在密钥检测完成后自动发送检测报告到此邮箱。</p>
        </div>
        
        <div class="footer">
            <p>此邮件由 Gemini Key Checker 系统发送</p>
            <p>测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
        """
        return html

# 全局邮件通知实例
email_notifier = EmailNotifier() 