from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ApiKey(db.Model):
    """API密钥模型"""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    key_value = db.Column(db.String(255), unique=True, nullable=False, index=True)
    status = db.Column(db.String(20), default='pending')  # pending, valid, invalid, error
    last_checked = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 与检测记录的关系
    check_logs = db.relationship('CheckLog', backref='api_key', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ApiKey {self.key_value[:10]}...>'

class CheckLog(db.Model):
    """检测记录模型"""
    __tablename__ = 'check_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_keys.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # valid, invalid, error
    message = db.Column(db.Text)
    checked_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CheckLog {self.id}: {self.status}>'

class Settings(db.Model):
    """系统设置模型"""
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Settings {self.key}: {self.value}>' 