import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Patient, User, MedicalRecord, Diagnosis, Prescription
from datetime import datetime, timedelta
from decimal import Decimal

def create_medical_record_test_data():
    with app.app_context():
        try:
            # 获取测试患者和医生
            patient = Patient.query.filter_by(serial_no='202005090006').first()  # 张明
            doctor = User.query.filter_by(username='doctor1').first()
            
            if not patient or not doctor:
                print("找不到测试患者或医生，请先创建患者和用户测试数据")
                return
                
            # 创建测试病历记录
            record = MedicalRecord(
                patient_id=patient.id,
                doctor_id=doctor.id,
                visit_time=datetime.utcnow() - timedelta(days=7)  # 一周前的记录
            )
            db.session.add(record)
            db.session.flush()
            
            # 添加诊断
            diagnoses = [
                {
                    'type': '高血压',
                    'description': '血压偏高，需要控制饮食和用药'
                },
                {
                    'type': '冠心病',
                    'description': '需要定期复查'
                }
            ]
            
            for diag_data in diagnoses:
                diagnosis = Diagnosis(
                    record_id=record.id,
                    type=diag_data['type'],
                    description=diag_data['description']
                )
                db.session.add(diagnosis)
            
            # 添加处方
            prescriptions = [
                {
                    'medicine': '硝苯地平缓释片',
                    'specification': '10mg*36片/盒',
                    'dosage': '10mg',
                    'frequency': '每日两次',
                    'days': '30',
                    'price': Decimal('65.50'),
                    'effect': '用于治疗高血压，扩张冠状动脉'
                },
                {
                    'medicine': '阿司匹林肠溶片',
                    'specification': '100mg*30片/盒',
                    'dosage': '100mg',
                    'frequency': '每日一次',
                    'days': '30',
                    'price': Decimal('32.80'),
                    'effect': '抗血小板聚集，预防心脑血管疾病'
                }
            ]
            
            for pres_data in prescriptions:
                prescription = Prescription(
                    record_id=record.id,
                    medicine=pres_data['medicine'],
                    specification=pres_data['specification'],
                    dosage=pres_data['dosage'],
                    frequency=pres_data['frequency'],
                    days=pres_data['days'],
                    price=pres_data['price'],
                    effect=pres_data['effect']
                )
                db.session.add(prescription)
            
            # 更新患者状态
            patient.status = 'treated'
            
            db.session.commit()
            print("病历测试数据创建成功！")
            
        except Exception as e:
            print(f"创建病历测试数据时出错: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    create_medical_record_test_data() 