import sys
import os
import random
from datetime import datetime, timedelta

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Patient, User, MedicalRecord, Diagnosis, Prescription, Scan, AIAnalysisResult
from sqlalchemy import text
import shutil

def create_medical_records():
    """创建医疗记录"""
    print("创建医疗记录...")
    
    patients = Patient.query.all()
    doctors = User.query.all()
    
    # 为每个患者创建1-3条医疗记录
    records_created = 0
    for patient in patients:
        record_count = random.randint(1, 3)
        
        for i in range(record_count):
            # 随机选择医生
            doctor = random.choice(doctors)
            
            # 随机生成就诊时间（过去30天内）
            days_ago = random.randint(0, 30)
            visit_time = datetime.now() - timedelta(days=days_ago)
            
            record = MedicalRecord(
                patient_id=patient.id,
                doctor_id=doctor.id,
                visit_time=visit_time
            )
            db.session.add(record)
            records_created += 1
    
    db.session.commit()
    print(f"创建了 {records_created} 条医疗记录")

def create_diagnoses():
    """创建诊断信息"""
    print("创建诊断信息...")
    
    eye_diagnoses = [
        {"type": "近视", "description": "视力下降，看远处物体模糊"},
        {"type": "远视", "description": "看近处物体费力，容易疲劳"},
        {"type": "散光", "description": "视物变形或模糊"},
        {"type": "白内障", "description": "晶状体混浊，视力下降"},
        {"type": "青光眼", "description": "眼压升高，视野缺损"},
        {"type": "黄斑变性", "description": "中心视力下降，视物变形"},
        {"type": "糖尿病视网膜病变", "description": "视网膜微血管病变，可能导致视力下降"},
        {"type": "干眼症", "description": "眼睛干涩、疲劳、刺痛"},
        {"type": "结膜炎", "description": "眼睛红、痒、有分泌物"},
        {"type": "视网膜脱离", "description": "视野中出现闪光或飘浮物，视力下降"}
    ]
    
    other_diagnoses = [
        {"type": "高血压", "description": "血压持续升高，超过正常范围"},
        {"type": "糖尿病", "description": "血糖控制不良，需要调整治疗方案"},
        {"type": "冠心病", "description": "胸痛，心电图异常"},
        {"type": "慢性支气管炎", "description": "咳嗽，咳痰，气短"},
        {"type": "胃炎", "description": "上腹部不适，恶心"}
    ]
    
    records = MedicalRecord.query.all()
    diagnoses_created = 0
    
    for record in records:
        # 获取患者所属的医生部门
        doctor = User.query.get(record.doctor_id)
        
        # 根据医生部门选择诊断类型
        if doctor.department_id == 1:  # 眼科
            diagnoses_list = eye_diagnoses
        else:
            diagnoses_list = other_diagnoses
        
        # 为每条记录创建1-2个诊断
        diagnosis_count = random.randint(1, 2)
        selected_diagnoses = random.sample(diagnoses_list, diagnosis_count)
        
        for diag in selected_diagnoses:
            diagnosis = Diagnosis(
                record_id=record.id,
                type=diag["type"],
                description=diag["description"]
            )
            db.session.add(diagnosis)
            diagnoses_created += 1
    
    db.session.commit()
    print(f"创建了 {diagnoses_created} 条诊断信息")

def create_prescriptions():
    """创建处方信息"""
    print("创建处方信息...")
    
    eye_medicines = [
        {"medicine": "人工泪液", "specification": "10ml/瓶", "dosage": "1-2滴", "frequency": "每日3-4次", "days": 30, "price": 35.00, "effect": "缓解眼干"},
        {"medicine": "左氧氟沙星滴眼液", "specification": "5ml/瓶", "dosage": "1滴", "frequency": "每日4次", "days": 7, "price": 28.50, "effect": "治疗细菌性结膜炎"},
        {"medicine": "玻璃酸钠滴眼液", "specification": "5ml/瓶", "dosage": "1滴", "frequency": "每日3次", "days": 30, "price": 68.00, "effect": "治疗干眼症"},
        {"medicine": "盐酸卡替洛尔滴眼液", "specification": "5ml/瓶", "dosage": "1滴", "frequency": "每日2次", "days": 30, "price": 45.00, "effect": "降低眼压，治疗青光眼"},
        {"medicine": "复方托吡卡胺滴眼液", "specification": "15ml/瓶", "dosage": "1-2滴", "frequency": "检查前使用", "days": 1, "price": 32.00, "effect": "散瞳，便于眼底检查"}
    ]
    
    other_medicines = [
        {"medicine": "硝苯地平缓释片", "specification": "20mg*30片/盒", "dosage": "20mg", "frequency": "每日一次", "days": 30, "price": 38.50, "effect": "降低血压"},
        {"medicine": "盐酸二甲双胍片", "specification": "0.5g*60片/盒", "dosage": "0.5g", "frequency": "每日三次", "days": 30, "price": 42.00, "effect": "降低血糖"},
        {"medicine": "阿司匹林肠溶片", "specification": "100mg*30片/盒", "dosage": "100mg", "frequency": "每日一次", "days": 30, "price": 25.00, "effect": "抗血小板聚集，预防心脑血管疾病"},
        {"medicine": "氨氯地平片", "specification": "5mg*7片/盒", "dosage": "5mg", "frequency": "每日一次", "days": 30, "price": 75.00, "effect": "降低血压"},
        {"medicine": "辛伐他汀片", "specification": "20mg*7片/盒", "dosage": "20mg", "frequency": "每晚一次", "days": 30, "price": 86.00, "effect": "降低血脂"}
    ]
    
    records = MedicalRecord.query.all()
    prescriptions_created = 0
    
    for record in records:
        # 获取患者所属的医生部门
        doctor = User.query.get(record.doctor_id)
        
        # 根据医生部门选择药品
        if doctor.department_id == 1:  # 眼科
            medicines_list = eye_medicines
        else:
            medicines_list = other_medicines
        
        # 为每条记录创建1-3个处方
        prescription_count = random.randint(1, 3)
        selected_medicines = random.sample(medicines_list, prescription_count)
        
        for med in selected_medicines:
            prescription = Prescription(
                record_id=record.id,
                medicine=med["medicine"],
                specification=med["specification"],
                dosage=med["dosage"],
                frequency=med["frequency"],
                days=med["days"],
                price=med["price"],
                effect=med["effect"]
            )
            db.session.add(prescription)
            prescriptions_created += 1
    
    db.session.commit()
    print(f"创建了 {prescriptions_created} 条处方信息")

def create_scans():
    """创建扫描记录"""
    print("创建扫描记录...")
    
    # 获取所有患者
    patients = Patient.query.all()
    
    # 获取眼科医生
    eye_doctors = User.query.filter_by(department_id=1).all()
    
    # 获取images文件夹中的图像文件
    image_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "images")
    original_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "originals")
    
    # 确保目录存在
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(original_dir, exist_ok=True)
    
    # 按照要求分配扫描记录
    scans_created = 0
    
    # 第1位患者有4次扫描
    patient1 = patients[0]
    create_patient_scans(patient1, eye_doctors, 4, image_dir, original_dir)
    scans_created += 4
    
    # 第2位患者有3次扫描
    patient2 = patients[1]
    create_patient_scans(patient2, eye_doctors, 3, image_dir, original_dir)
    scans_created += 3
    
    # 剩下的8位患者每人一次扫描
    for i in range(2, 10):
        if i < len(patients):
            create_patient_scans(patients[i], eye_doctors, 1, image_dir, original_dir)
            scans_created += 1
    
    db.session.commit()
    print(f"创建了 {scans_created} 条扫描记录")

def create_patient_scans(patient, doctors, count, image_dir, original_dir):
    """为患者创建指定数量的扫描记录"""
    for i in range(count):
        # 随机选择医生
        doctor = random.choice(doctors)
        
        # 随机生成扫描时间（过去30天内）
        days_ago = random.randint(0, 30)
        scan_time = datetime.now() - timedelta(days=days_ago)
        
        # 生成文件名
        timestamp = scan_time.strftime("%Y%m%d%H%M%S")
        oct_image_name = f"{patient.id}_OCT_{timestamp}.png"
        fundus_image_name = f"{patient.id}_Fundus_{timestamp}.png"
        oct_original_name = f"{patient.id}_OCT_original_{timestamp}.tif"
        fundus_original_name = f"{patient.id}_Fundus_original_{timestamp}.tif"
        
        # 复制示例图像（如果有）
        sample_oct = os.path.join(image_dir, "sample_oct.png")
        sample_fundus = os.path.join(image_dir, "sample_fundus.png")
        sample_oct_original = os.path.join(original_dir, "sample_oct_original.tif")
        sample_fundus_original = os.path.join(original_dir, "sample_fundus_original.tif")
        
        oct_image_path = os.path.join(image_dir, oct_image_name)
        fundus_image_path = os.path.join(image_dir, fundus_image_name)
        oct_original_path = os.path.join(original_dir, oct_original_name)
        fundus_original_path = os.path.join(original_dir, fundus_original_name)
        
        # 如果有示例图像，复制它们
        if os.path.exists(sample_oct):
            shutil.copy(sample_oct, oct_image_path)
        if os.path.exists(sample_fundus):
            shutil.copy(sample_fundus, fundus_image_path)
        if os.path.exists(sample_oct_original):
            shutil.copy(sample_oct_original, oct_original_path)
        if os.path.exists(sample_fundus_original):
            shutil.copy(sample_fundus_original, fundus_original_path)
        
        # 创建扫描记录
        scan = Scan(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scan_type="Both",
            scan_time=scan_time,
            oct_image_path=f"/api/images/{oct_image_name}",
            fundus_image_path=f"/api/images/{fundus_image_name}",
            oct_original_path=f"/api/originals/{oct_original_name}",
            fundus_original_path=f"/api/originals/{fundus_original_name}"
        )
        db.session.add(scan)

def create_ai_analysis_results():
    """创建AI分析结果"""
    print("创建AI分析结果...")
    
    # 获取所有扫描记录
    scans = Scan.query.all()
    
    # 可能的分类结果
    classification_results = [
        "正常（无明显病变）",
        "AMD（年龄相关性黄斑变性）",
        "DME（糖尿病黄斑水肿）",
        "CNV（脉络膜新生血管）",
        "DR（糖尿病视网膜病变）",
        "青光眼",
        "白内障"
    ]
    
    # 为每个扫描记录创建AI分析结果
    results_created = 0
    for scan in scans:
        # 随机选择分类结果
        classification_result = random.choice(classification_results)
        
        # 生成分割图像路径
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        segmentation_image_name = f"segmented_{scan.id}_{timestamp}.png"
        segmentation_image_path = f"images/segmentation/{segmentation_image_name}"
        
        # 创建AI分析结果
        analysis_result = AIAnalysisResult(
            scan_id=scan.id,
            segmentation_image_path=segmentation_image_path,
            classification_result=classification_result
        )
        db.session.add(analysis_result)
        results_created += 1
    
    db.session.commit()
    print(f"创建了 {results_created} 条AI分析结果")

if __name__ == "__main__":
    with app.app_context():
        create_medical_records()
        create_diagnoses()
        create_prescriptions()
        create_scans()
        create_ai_analysis_results() 