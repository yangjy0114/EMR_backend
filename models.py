from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Patient(db.Model):
    """患者信息表"""
    __tablename__ = 'patients'
    
    patient_id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10))
    age = db.Column(db.Integer)
    medical_history = db.Column(db.Text)
    
    # 关联关系
    scans = db.relationship('Scan', backref='patient', lazy=True)

class Doctor(db.Model):
    """医生信息表"""
    __tablename__ = 'doctors'
    
    doctor_id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100))

class Scan(db.Model):
    """扫描记录表"""
    __tablename__ = 'scans'
    
    scan_id = db.Column(db.String(36), primary_key=True)
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.patient_id'), nullable=False)
    doctor_id = db.Column(db.String(36), db.ForeignKey('doctors.doctor_id'), nullable=False)
    scan_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    images = db.relationship('Image', backref='scan', lazy=True)
    reports = db.relationship('Report', backref='scan', lazy=True)

class Image(db.Model):
    """图像信息表"""
    __tablename__ = 'images'
    
    image_id = db.Column(db.String(36), primary_key=True)
    scan_id = db.Column(db.String(36), db.ForeignKey('scans.scan_id'), nullable=False)
    image_type = db.Column(db.String(50), nullable=False)  # OCT或眼底图像
    image_path = db.Column(db.String(255), nullable=False)
    is_segmented = db.Column(db.Boolean, default=False)
    
    # 关联关系
    segmented_images = db.relationship('SegmentedImage', backref='original_image', lazy=True)
    classification_results = db.relationship('ClassificationResult', backref='image', lazy=True)

class SegmentedImage(db.Model):
    """分割后的图像表"""
    __tablename__ = 'segmented_images'
    
    segmented_id = db.Column(db.String(36), primary_key=True)
    image_id = db.Column(db.String(36), db.ForeignKey('images.image_id'), nullable=False)
    segmented_image_path = db.Column(db.String(255), nullable=False)
    segmentation_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    error_message = db.Column(db.Text)

class ClassificationResult(db.Model):
    """分类结果表"""
    __tablename__ = 'classification_results'
    
    classification_id = db.Column(db.String(36), primary_key=True)
    image_id = db.Column(db.String(36), db.ForeignKey('images.image_id'), nullable=False)
    result = db.Column(db.Text, nullable=False)

class Report(db.Model):
    """检查报告表"""
    __tablename__ = 'reports'
    
    report_id = db.Column(db.String(36), primary_key=True)
    scan_id = db.Column(db.String(36), db.ForeignKey('scans.scan_id'), nullable=False)
    report_content = db.Column(db.Text, nullable=False)
    generation_date = db.Column(db.DateTime, default=datetime.utcnow)

class Department(db.Model):
    """部门/科室表"""
    __tablename__ = 'departments'
    
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    users = db.relationship('User', backref='department', lazy=True)

class User(db.Model):
    """用户表"""
    __tablename__ = 'users'
    
    id = db.Column(db.BigInteger, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    real_name = db.Column(db.String(50), nullable=False)
    department_id = db.Column(db.BigInteger, db.ForeignKey('departments.id'), nullable=False)
    avatar = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)
    login_fails = db.Column(db.Integer, default=0)  # 登录失败次数
    is_locked = db.Column(db.Boolean, default=False)  # 是否锁定 