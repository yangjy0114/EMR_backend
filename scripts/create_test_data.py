import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Patient, Doctor
import uuid

def create_test_data():
    with app.app_context():
        try:
            # 检查是否已存在
            existing_doctor = Doctor.query.get("1")
            existing_patient = Patient.query.get("1")
            
            if not existing_doctor:
                # 创建测试医生
                doctor = Doctor(
                    doctor_id="1",
                    name="测试医生",
                    specialization="眼科"
                )
                db.session.add(doctor)
            
            if not existing_patient:
                # 创建测试患者
                patient = Patient(
                    patient_id="1",
                    name="测试患者",
                    gender="男",
                    age=30,
                    medical_history="无"
                )
                db.session.add(patient)
            
            db.session.commit()
            print("测试数据创建/更新成功！")
            
            # 验证数据
            verify_doctor = Doctor.query.get("1")
            verify_patient = Patient.query.get("1")
            
            if verify_doctor and verify_patient:
                print("\n数据验证成功：")
                print(f"医生信息: ID={verify_doctor.doctor_id}, 姓名={verify_doctor.name}")
                print(f"患者信息: ID={verify_patient.patient_id}, 姓名={verify_patient.name}")
            else:
                print("\n警告：数据验证失败！")
                
        except Exception as e:
            print(f"创建测试数据时出错: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    create_test_data() 