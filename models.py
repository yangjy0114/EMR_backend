from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import DECIMAL
import os

db = SQLAlchemy()

class Patient(db.Model):
    """患者信息表"""
    __tablename__ = 'patients'
    
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    serial_no = db.Column(db.String(50), unique=True, nullable=False)
    card_no = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.Enum('waiting', 'in_treatment', 'treated', name='patient_status'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    medical_history = db.relationship('MedicalHistory', backref='patient', uselist=False, lazy=True)
    medical_records = db.relationship('MedicalRecord', backref='patient', lazy=True)

class MedicalHistory(db.Model):
    """病史信息表"""
    __tablename__ = 'medical_histories'
    
    id = db.Column(db.BigInteger, primary_key=True)
    patient_id = db.Column(db.BigInteger, db.ForeignKey('patients.id'), nullable=False)
    allergies = db.Column(db.Text)
    history = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MedicalRecord(db.Model):
    """就诊记录表"""
    __tablename__ = 'medical_records'
    
    id = db.Column(db.BigInteger, primary_key=True)
    patient_id = db.Column(db.BigInteger, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    visit_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    diagnoses = db.relationship('Diagnosis', backref='record', lazy=True)
    prescriptions = db.relationship('Prescription', backref='record', lazy=True)

class Diagnosis(db.Model):
    """诊断信息表"""
    __tablename__ = 'diagnoses'
    
    id = db.Column(db.BigInteger, primary_key=True)
    record_id = db.Column(db.BigInteger, db.ForeignKey('medical_records.id'), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Prescription(db.Model):
    """处方信息表"""
    __tablename__ = 'prescriptions'
    
    id = db.Column(db.BigInteger, primary_key=True)
    record_id = db.Column(db.BigInteger, db.ForeignKey('medical_records.id'), nullable=False)
    medicine = db.Column(db.String(100), nullable=False)
    specification = db.Column(db.String(100))
    dosage = db.Column(db.String(50))
    frequency = db.Column(db.String(50))
    days = db.Column(db.String(20))
    price = db.Column(DECIMAL(10, 2))
    effect = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Doctor(db.Model):
    """医生信息表"""
    __tablename__ = 'doctors'
    
    doctor_id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100))

class Scan(db.Model):
    """扫描记录表"""
    __tablename__ = 'scans'
    
    id = db.Column(db.BigInteger, primary_key=True)
    patient_id = db.Column(db.BigInteger, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    medical_record_id = db.Column(db.BigInteger, db.ForeignKey('medical_records.id'), nullable=True)
    scan_type = db.Column(db.Enum('OCT', 'Fundus', 'Both', name='scan_type'), nullable=False)
    scan_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # 显示用的PNG图像路径
    oct_image_path = db.Column(db.String(255))
    fundus_image_path = db.Column(db.String(255))
    # 原始TIF图像路径
    oct_original_path = db.Column(db.String(255))
    fundus_original_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    patient = db.relationship('Patient', backref='scans')
    doctor = db.relationship('User', backref='scans')
    medical_record = db.relationship('MedicalRecord', backref='scans')

class Image(db.Model):
    """图像信息表"""
    __tablename__ = 'images'
    
    image_id = db.Column(db.String(36), primary_key=True)
    scan_id = db.Column(db.BigInteger, db.ForeignKey('scans.id'), nullable=False)
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
    scan_id = db.Column(db.BigInteger, db.ForeignKey('scans.id'), nullable=False)
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

class AIAnalysisResult(db.Model):
    """AI分析结果表"""
    __tablename__ = 'ai_analysis_results'
    
    id = db.Column(db.BigInteger, primary_key=True)
    scan_id = db.Column(db.BigInteger, db.ForeignKey('scans.id'), nullable=False)
    segmentation_image_path = db.Column(db.String(255), nullable=True)
    classification_result = db.Column(db.String(100), nullable=True)
    report = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    scan = db.relationship('Scan', backref='ai_analysis_results')
    
    # 添加属性方法来获取 segmentation_image_url
    @property
    def segmentation_image_url(self):
        if self.segmentation_image_path:
            # 从路径中提取文件名
            filename = os.path.basename(self.segmentation_image_path)
            
            # 确定图像类型
            if '/fundus/' in self.segmentation_image_path:
                return f"/api/segmentation/fundus/{filename}"
            elif '/oct/' in self.segmentation_image_path:
                return f"/api/segmentation/oct/{filename}"
            else:
                # 如果路径中没有类型信息，尝试从文件名判断
                if 'fundus' in filename:
                    return f"/api/segmentation/fundus/{filename}"
                elif 'oct' in filename:
                    return f"/api/segmentation/oct/{filename}"
                else:
                    # 默认返回
                    return f"/api/segmentation/{filename}"
        return None 

class PatientScanMapping(db.Model):
    __tablename__ = 'patient_scan_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    scan_id = db.Column(db.Integer, db.ForeignKey('scans.id'), nullable=False)
    
    # 关系
    patient = db.relationship('Patient', backref=db.backref('scan_mappings', lazy=True))
    scan = db.relationship('Scan', backref=db.backref('patient_mapping', lazy=True)) 