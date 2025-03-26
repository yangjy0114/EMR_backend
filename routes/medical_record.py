from flask import Blueprint, request, jsonify
from models import db, Patient, MedicalHistory, MedicalRecord, Diagnosis, Prescription, User
from utils.auth import login_required
import logging
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)
medical_record_bp = Blueprint('medical_record', __name__, url_prefix='/api/medical-records')

def format_diagnosis(diagnosis):
    """格式化诊断信息"""
    return {
        'type': diagnosis.type,
        'description': diagnosis.description
    }

def format_prescription(prescription):
    """格式化处方信息"""
    return {
        'medicine': prescription.medicine,
        'specification': prescription.specification,
        'dosage': prescription.dosage,
        'frequency': prescription.frequency,
        'days': prescription.days,
        'price': str(prescription.price) if prescription.price else '',
        'effect': prescription.effect
    }

def format_record_summary(record):
    """格式化病历摘要信息"""
    doctor = User.query.get(record.doctor_id)
    return {
        'id': str(record.id),
        'timestamp': record.visit_time.strftime('%Y%m%d%H%M%S'),
        'doctorName': doctor.real_name if doctor else '未知医生',
        'diagnosis': [format_diagnosis(d) for d in record.diagnoses],
        'prescription': [format_prescription(p) for p in record.prescriptions]
    }

def format_record_detail(record):
    """格式化病历详细信息"""
    doctor = User.query.get(record.doctor_id)
    patient = record.patient
    
    # 获取患者病史信息
    medical_history = patient.medical_history
    
    return {
        'id': str(record.id),
        'timestamp': record.visit_time.strftime('%Y%m%d%H%M%S'),
        'doctorName': doctor.real_name if doctor else '未知医生',
        'patientInfo': {
            'id': str(patient.id),
            'name': patient.name,
            'gender': patient.gender,
            'age': patient.age,
            'serialNo': patient.serial_no,
            'cardNo': patient.card_no,
            'medicalHistory': {
                'allergies': medical_history.allergies if medical_history else '',
                'history': medical_history.history if medical_history else ''
            }
        },
        'diagnosis': [format_diagnosis(d) for d in record.diagnoses],
        'prescription': [format_prescription(p) for p in record.prescriptions]
    }

@medical_record_bp.route('/patient/<int:patient_id>', methods=['GET'])
@login_required
def get_patient_records(patient_id):
    """获取患者病历列表"""
    try:
        # 验证患者是否存在
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({
                'code': 404,
                'message': '患者不存在'
            }), 404
            
        # 获取患者的所有病历记录
        records = MedicalRecord.query.filter_by(patient_id=patient_id).order_by(MedicalRecord.visit_time.desc()).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': [format_record_summary(record) for record in records]
        })
        
    except Exception as e:
        logger.error(f"获取患者病历列表时出错: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@medical_record_bp.route('/<int:record_id>', methods=['GET'])
@login_required
def get_record_detail(record_id):
    """获取病历详情"""
    try:
        # 获取病历记录
        record = MedicalRecord.query.get(record_id)
        if not record:
            return jsonify({
                'code': 404,
                'message': '病历不存在'
            }), 404
            
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': format_record_detail(record)
        })
        
    except Exception as e:
        logger.error(f"获取病历详情时出错: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@medical_record_bp.route('', methods=['POST'])
@login_required
def create_medical_record():
    """创建新病历"""
    try:
        data = request.get_json()
        
        # 验证必要字段
        if not data or 'patientId' not in data:
            return jsonify({
                'code': 400,
                'message': '缺少患者ID'
            }), 400
            
        if 'diagnosis' not in data or not data['diagnosis']:
            return jsonify({
                'code': 400,
                'message': '至少需要一条诊断信息'
            }), 400
            
        # 获取患者信息
        patient_id = data['patientId']
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({
                'code': 404,
                'message': '患者不存在'
            }), 404
            
        # 获取当前医生信息（从token中）
        token = request.headers['Authorization'].split(' ')[1]
        from utils.auth import Auth
        doctor_id = Auth.verify_token(token)
        
        # 开始事务
        try:
            # 1. 创建病历记录
            record = MedicalRecord(
                patient_id=patient_id,
                doctor_id=doctor_id,
                visit_time=datetime.utcnow()
            )
            db.session.add(record)
            db.session.flush()  # 获取record.id
            
            # 2. 更新患者病史（如果提供）
            if 'medicalHistory' in data and data['medicalHistory']:
                medical_history = patient.medical_history
                if not medical_history:
                    medical_history = MedicalHistory(
                        patient_id=patient_id,
                        allergies=data['medicalHistory'].get('allergies', ''),
                        history=data['medicalHistory'].get('history', '')
                    )
                    db.session.add(medical_history)
                else:
                    medical_history.allergies = data['medicalHistory'].get('allergies', medical_history.allergies)
                    medical_history.history = data['medicalHistory'].get('history', medical_history.history)
            
            # 3. 添加诊断信息
            for diag_data in data['diagnosis']:
                if not diag_data.get('type'):
                    raise ValueError('诊断类型不能为空')
                    
                diagnosis = Diagnosis(
                    record_id=record.id,
                    type=diag_data['type'],
                    description=diag_data.get('description', '')
                )
                db.session.add(diagnosis)
            
            # 4. 添加处方信息（如果有）
            if 'prescription' in data and data['prescription']:
                for pres_data in data['prescription']:
                    if not pres_data.get('medicine'):
                        raise ValueError('药品名称不能为空')
                        
                    # 验证价格是否为有效数字
                    price = None
                    if pres_data.get('price'):
                        try:
                            price = Decimal(pres_data['price'])
                        except InvalidOperation:
                            raise ValueError('价格必须是有效数字')
                    
                    prescription = Prescription(
                        record_id=record.id,
                        medicine=pres_data['medicine'],
                        specification=pres_data.get('specification', ''),
                        dosage=pres_data.get('dosage', ''),
                        frequency=pres_data.get('frequency', ''),
                        days=pres_data.get('days', ''),
                        price=price,
                        effect=pres_data.get('effect', '')
                    )
                    db.session.add(prescription)
            
            # 5. 更新患者状态
            if patient.status == 'waiting':
                patient.status = 'in_treatment'
            elif patient.status == 'in_treatment':
                patient.status = 'treated'
            
            # 提交事务
            db.session.commit()
            
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'id': str(record.id),
                    'timestamp': record.visit_time.strftime('%Y%m%d%H%M%S')
                }
            })
            
        except ValueError as ve:
            db.session.rollback()
            return jsonify({
                'code': 400,
                'message': str(ve)
            }), 400
            
        except SQLAlchemyError as se:
            db.session.rollback()
            logger.error(f"数据库错误: {str(se)}")
            return jsonify({
                'code': 500,
                'message': '数据库错误'
            }), 500
            
    except Exception as e:
        logger.error(f"创建病历时出错: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500 