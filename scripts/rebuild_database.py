import sys
import os
import time
from datetime import datetime, timedelta
import random

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import *
from sqlalchemy import text
from werkzeug.security import generate_password_hash

# 导入医疗数据创建函数
from scripts.create_medical_data import (
    create_medical_records, 
    create_diagnoses, 
    create_prescriptions, 
    create_scans, 
    create_ai_analysis_results
)

def rebuild_database():
    """重建数据库并填充基础数据"""
    with app.app_context():
        try:
            print("开始重建数据库...")
            
            # 先删除所有表，然后重新创建
            print("删除所有现有表...")
            db.drop_all()
            print("所有表已删除")
            
            # 创建所有表
            db.create_all()
            print("所有表创建成功")
            
            # 填充基础数据
            create_departments()
            create_users()
            
            # 创建患者数据
            create_patients()
            
            # 创建医疗记录和病史
            create_medical_histories()
            
            print("基础数据创建完成!")
            
        except Exception as e:
            print(f"重建数据库时出错: {str(e)}")
            db.session.rollback()

def create_departments():
    """创建部门数据"""
    print("创建部门数据...")
    departments = [
        {"name": "眼科", "description": "负责眼部疾病的诊断和治疗"},
        {"name": "内科", "description": "负责内部器官疾病的诊断和治疗"},
        {"name": "外科", "description": "负责外部器官疾病的诊断和治疗"},
        {"name": "儿科", "description": "负责儿童疾病的诊断和治疗"},
        {"name": "妇产科", "description": "负责女性生殖系统疾病的诊断和治疗"}
    ]
    
    for dept_data in departments:
        dept = Department(**dept_data)
        db.session.add(dept)
    
    db.session.commit()
    print(f"创建了 {len(departments)} 个部门")

def create_users():
    """创建用户数据"""
    print("创建用户数据...")
    users = [
        {"username": "admin", "password": "admin123", "real_name": "系统管理员", "department_id": 1},
        {"username": "doctor1", "password": "doctor123", "real_name": "张医生", "department_id": 1},
        {"username": "doctor2", "password": "doctor123", "real_name": "李医生", "department_id": 1},
        {"username": "doctor3", "password": "doctor123", "real_name": "王医生", "department_id": 2},
        {"username": "doctor4", "password": "doctor123", "real_name": "赵医生", "department_id": 3},
        {"username": "doctor5", "password": "doctor123", "real_name": "刘医生", "department_id": 4}
    ]
    
    for user_data in users:
        password = user_data.pop("password")
        user_data["password"] = generate_password_hash(password)
        user = User(**user_data)
        db.session.add(user)
    
    db.session.commit()
    print(f"创建了 {len(users)} 个用户")

def create_patients():
    """创建患者数据"""
    print("创建患者数据...")
    patients = []
    
    # 创建20个患者
    for i in range(1, 21):
        gender = "男" if i % 2 == 0 else "女"
        age = random.randint(18, 80)
        status = random.choice(["waiting", "in_treatment", "treated"])
        
        patient_data = {
            "name": f"患者{i}",
            "gender": gender,
            "age": age,
            "serial_no": f"SN{i:04d}",
            "card_no": f"CN{i:04d}",
            "status": status
        }
        patients.append(patient_data)
    
    for patient_data in patients:
        patient = Patient(**patient_data)
        db.session.add(patient)
    
    db.session.commit()
    print(f"创建了 {len(patients)} 个患者")

def create_medical_histories():
    """创建病史数据"""
    print("创建病史数据...")
    
    allergies_options = [
        "无",
        "青霉素",
        "磺胺类药物",
        "阿司匹林",
        "头孢类抗生素",
        "碘造影剂",
        "花粉",
        "海鲜",
        "花生",
        "乳制品"
    ]
    
    history_options = [
        "高血压",
        "糖尿病",
        "冠心病",
        "哮喘",
        "慢性肾病",
        "甲状腺功能亢进",
        "类风湿性关节炎",
        "抑郁症",
        "癫痫",
        "青光眼",
        "白内障",
        "黄斑变性",
        "视网膜病变",
        "干眼症"
    ]
    
    # 为每个患者创建病史
    patients = Patient.query.all()
    for patient in patients:
        # 随机选择1-3种过敏原
        allergies_count = random.randint(0, 3)
        allergies = random.sample(allergies_options, allergies_count)
        
        # 随机选择0-3种病史
        history_count = random.randint(0, 3)
        history = random.sample(history_options, history_count)
        
        medical_history = MedicalHistory(
            patient_id=patient.id,
            allergies=", ".join(allergies) if allergies else "无",
            history=", ".join(history) if history else "无"
        )
        db.session.add(medical_history)
    
    db.session.commit()
    print(f"为 {len(patients)} 个患者创建了病史")

# 其他函数将在后续脚本中实现...

if __name__ == "__main__":
    rebuild_database() 