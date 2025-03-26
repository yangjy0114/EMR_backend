import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Patient, MedicalHistory, MedicalRecord, Diagnosis, Prescription
from datetime import datetime

def create_patient_test_data():
    with app.app_context():
        try:
            # 创建测试患者数据
            patients_data = [
                {
                    'name': '李萍',
                    'gender': '女',
                    'age': 27,
                    'serial_no': '202005090005',
                    'card_no': '202003100012',
                    'status': 'in_treatment',
                    'medical_history': {
                        'allergies': '头孢噻肟钠，氯雷他定，甲氧氯普胺',
                        'history': '支气管哮喘，慢性荨麻疹，高血压'
                    }
                },
                {
                    'name': '张明',
                    'gender': '男',
                    'age': 45,
                    'serial_no': '202005090006',
                    'card_no': '202003100013',
                    'status': 'treated',
                    'medical_history': {
                        'allergies': '青霉素，阿莫西林',
                        'history': '高血压，冠心病'
                    }
                },
                {
                    'name': '王华',
                    'gender': '女',
                    'age': 33,
                    'serial_no': '202005090007',
                    'card_no': '202003100014',
                    'status': 'waiting',
                    'medical_history': {
                        'allergies': '无',
                        'history': '糖尿病'
                    }
                }
            ]
            
            for data in patients_data:
                # 检查患者是否已存在
                patient = Patient.query.filter_by(serial_no=data['serial_no']).first()
                if not patient:
                    patient = Patient(
                        name=data['name'],
                        gender=data['gender'],
                        age=data['age'],
                        serial_no=data['serial_no'],
                        card_no=data['card_no'],
                        status=data['status']
                    )
                    db.session.add(patient)
                    db.session.flush()  # 获取 patient.id
                    
                    # 创建病史记录
                    history = MedicalHistory(
                        patient_id=patient.id,
                        allergies=data['medical_history']['allergies'],
                        history=data['medical_history']['history']
                    )
                    db.session.add(history)
            
            db.session.commit()
            print("患者测试数据创建成功！")
            
        except Exception as e:
            print(f"创建患者测试数据时出错: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    create_patient_test_data() 