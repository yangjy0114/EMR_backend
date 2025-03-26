from flask import Blueprint, request, jsonify
from models import db, Patient, MedicalHistory, MedicalRecord, Diagnosis, Prescription
from utils.auth import login_required
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
patient_bp = Blueprint('patient', __name__, url_prefix='/api/patients')

def format_record(record):
    """格式化就诊记录"""
    return {
        'id': str(record.id),
        'timestamp': record.visit_time.strftime('%Y%m%d%H%M%S'),
        'diagnosis': [
            {
                'type': d.type,
                'description': d.description
            } for d in record.diagnoses
        ],
        'prescription': [
            {
                'medicine': p.medicine,
                'specification': p.specification,
                'dosage': p.dosage,
                'frequency': p.frequency,
                'days': p.days,
                'price': str(p.price),
                'effect': p.effect
            } for p in record.prescriptions
        ]
    }

def format_patient(patient):
    """格式化患者信息"""
    return {
        'id': str(patient.id),
        'name': patient.name,
        'gender': patient.gender,
        'age': patient.age,
        'serialNo': patient.serial_no,
        'cardNo': patient.card_no,
        'medicalHistory': {
            'allergies': patient.medical_history.allergies if patient.medical_history else '',
            'history': patient.medical_history.history if patient.medical_history else ''
        },
        'records': [format_record(record) for record in patient.medical_records]
    }

@patient_bp.route('/waiting', methods=['GET'])
@login_required
def get_waiting_patients():
    """获取待诊患者列表"""
    try:
        patients = Patient.query.filter_by(status='waiting').all()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': [format_patient(p) for p in patients]
        })
    except Exception as e:
        logger.error(f"获取待诊患者列表时出错: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@patient_bp.route('/in-treatment', methods=['GET'])
@login_required
def get_in_treatment_patients():
    """获取就诊中患者列表"""
    try:
        patients = Patient.query.filter_by(status='in_treatment').all()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': [format_patient(p) for p in patients]
        })
    except Exception as e:
        logger.error(f"获取就诊中患者列表时出错: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@patient_bp.route('/treated', methods=['GET'])
@login_required
def get_treated_patients():
    """获取已就诊患者列表"""
    try:
        patients = Patient.query.filter_by(status='treated').all()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': [format_patient(p) for p in patients]
        })
    except Exception as e:
        logger.error(f"获取已就诊患者列表时出错: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@patient_bp.route('/<int:patient_id>', methods=['GET'])
@login_required
def get_patient_detail(patient_id):
    """获取患者详情"""
    try:
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({
                'code': 404,
                'message': '患者不存在'
            }), 404
            
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': format_patient(patient)
        })
    except Exception as e:
        logger.error(f"获取患者详情时出错: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@patient_bp.route('/<int:patient_id>/status', methods=['PUT'])
@login_required
def update_patient_status(patient_id):
    """更新患者状态"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({
                'code': 400,
                'message': '状态不能为空'
            }), 400
            
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({
                'code': 404,
                'message': '患者不存在'
            }), 404
            
        # 验证状态转换是否合法
        status_flow = {
            'waiting': ['in_treatment'],
            'in_treatment': ['treated'],
            'treated': []
        }
        
        if new_status not in status_flow[patient.status]:
            return jsonify({
                'code': 400,
                'message': '非法的状态转换'
            }), 400
            
        patient.status = new_status
        patient.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': None
        })
        
    except Exception as e:
        logger.error(f"更新患者状态时出错: {str(e)}")
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500 