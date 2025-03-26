import os
import uuid
from flask import Blueprint, request, jsonify, send_file, current_app
from models import db, Scan, Patient, User
from utils.auth import login_required
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)
scan_bp = Blueprint('scan', __name__, url_prefix='/api/scans')

# 允许的图像格式
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'tif', 'tiff'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_tif_to_png(tif_path, png_path):
    """将TIF图像转换为PNG格式"""
    try:
        # 打开TIF图像
        with Image.open(tif_path) as img:
            # 如果是多页TIF，只取第一页
            if hasattr(img, 'n_frames') and img.n_frames > 1:
                img.seek(0)
            
            # 转换为RGB模式（如果是RGBA或其他模式）
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 保存为PNG
            img.save(png_path, 'PNG')
        
        return True
    except Exception as e:
        logger.error(f"转换图像格式时出错: {str(e)}")
        return False

def format_scan_summary(scan):
    """格式化扫描记录摘要信息"""
    doctor = User.query.get(scan.doctor_id)
    return {
        'id': str(scan.id),
        'patientId': str(scan.patient_id),
        'timestamp': scan.scan_time.strftime('%Y%m%d%H%M%S'),
        'scanType': scan.scan_type,
        'doctorName': doctor.real_name if doctor else '未知医生'
    }

def format_patient_scan(scan):
    """格式化患者扫描记录信息"""
    return {
        'id': str(scan.id),
        'timestamp': scan.scan_time.strftime('%Y%m%d%H%M%S'),
        'scanType': scan.scan_type,
        'octImage': scan.oct_image_path if scan.oct_image_path else '',
        'fundusImage': scan.fundus_image_path if scan.fundus_image_path else ''
    }

def format_scan_detail(scan):
    """格式化扫描记录详细信息"""
    doctor = User.query.get(scan.doctor_id)
    patient = Patient.query.get(scan.patient_id)
    return {
        'id': str(scan.id),
        'patientId': str(scan.patient_id),
        'patientName': patient.name if patient else '未知患者',
        'timestamp': scan.scan_time.strftime('%Y%m%d%H%M%S'),
        'scanType': scan.scan_type,
        'octImage': scan.oct_image_path if scan.oct_image_path else '',
        'fundusImage': scan.fundus_image_path if scan.fundus_image_path else '',
        'octOriginal': scan.oct_original_path if scan.oct_original_path else '',
        'fundusOriginal': scan.fundus_original_path if scan.fundus_original_path else '',
        'medicalRecordId': str(scan.medical_record_id) if scan.medical_record_id else '',
        'doctorName': doctor.real_name if doctor else '未知医生'
    }

@scan_bp.route('', methods=['GET'])
@login_required
def get_scans():
    """获取扫描记录列表"""
    try:
        # 获取当前医生信息（从token中）
        token = request.headers['Authorization'].split(' ')[1]
        from utils.auth import Auth
        doctor_id = Auth.verify_token(token)
        
        # 获取医生所在科室
        doctor = User.query.get(doctor_id)
        if not doctor:
            return jsonify({
                'code': 401,
                'message': '无效的用户'
            }), 401
            
        # 获取该科室的所有扫描记录
        scans = Scan.query.join(User).filter(User.department_id == doctor.department_id).order_by(Scan.scan_time.desc()).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': [format_scan_summary(scan) for scan in scans]
        })
        
    except Exception as e:
        logger.error(f"获取扫描记录列表时出错: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@scan_bp.route('/patient/<int:patient_id>', methods=['GET'])
@login_required
def get_patient_scans(patient_id):
    """获取患者的扫描记录"""
    try:
        # 验证患者是否存在
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
        
        # 获取医生所在科室
        doctor = User.query.get(doctor_id)
        if not doctor:
            return jsonify({
                'code': 401,
                'message': '无效的用户'
            }), 401
            
        # 获取患者的所有扫描记录
        scans = Scan.query.filter_by(patient_id=patient_id).order_by(Scan.scan_time.desc()).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': [format_patient_scan(scan) for scan in scans]
        })
        
    except Exception as e:
        logger.error(f"获取患者扫描记录时出错: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@scan_bp.route('/<int:scan_id>', methods=['GET'])
@login_required
def get_scan_detail(scan_id):
    """获取扫描记录详情"""
    try:
        # 获取扫描记录
        scan = Scan.query.get(scan_id)
        if not scan:
            return jsonify({
                'code': 404,
                'message': '扫描记录不存在'
            }), 404
            
        # 获取当前医生信息（从token中）
        token = request.headers['Authorization'].split(' ')[1]
        from utils.auth import Auth
        doctor_id = Auth.verify_token(token)
        
        # 获取医生所在科室
        doctor = User.query.get(doctor_id)
        if not doctor:
            return jsonify({
                'code': 401,
                'message': '无效的用户'
            }), 401
            
        # 验证医生是否有权限查看该扫描记录（同科室）
        scan_doctor = User.query.get(scan.doctor_id)
        if scan_doctor.department_id != doctor.department_id:
            return jsonify({
                'code': 403,
                'message': '无权访问该扫描记录'
            }), 403
            
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': format_scan_detail(scan)
        })
        
    except Exception as e:
        logger.error(f"获取扫描记录详情时出错: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@scan_bp.route('', methods=['POST'])
@login_required
def upload_scan():
    """上传新扫描记录"""
    try:
        # 验证必要字段
        patient_id = request.form.get('patientId')
        scan_type = request.form.get('scanType')
        
        if not patient_id or not scan_type:
            return jsonify({
                'code': 400,
                'message': '缺少必要参数'
            }), 400
            
        # 验证患者是否存在
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
        
        # 验证扫描类型
        if scan_type not in ['OCT', 'Fundus', 'Both']:
            return jsonify({
                'code': 400,
                'message': '无效的扫描类型'
            }), 400
            
        # 处理文件上传
        oct_image_path = None
        fundus_image_path = None
        oct_original_path = None
        fundus_original_path = None
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        
        # 确保上传目录存在
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'scans')
        original_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'originals')
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(original_folder, exist_ok=True)
        
        # 处理OCT图像
        if 'octImage' in request.files and (scan_type == 'OCT' or scan_type == 'Both'):
            oct_file = request.files['octImage']
            if oct_file and oct_file.filename and allowed_file(oct_file.filename):
                # 获取文件扩展名
                ext = oct_file.filename.rsplit('.', 1)[1].lower()
                
                # 保存原始文件
                original_filename = f"{patient_id}_OCT_{timestamp}.{ext}"
                original_filename = secure_filename(original_filename)
                original_path = os.path.join(original_folder, original_filename)
                oct_file.save(original_path)
                oct_original_path = f"/api/originals/{original_filename}"
                
                # 如果是TIF格式，转换为PNG
                if ext in ['tif', 'tiff']:
                    png_filename = f"{patient_id}_OCT_{timestamp}.png"
                    png_filename = secure_filename(png_filename)
                    png_path = os.path.join(upload_folder, png_filename)
                    
                    if convert_tif_to_png(original_path, png_path):
                        oct_image_path = f"/api/images/{png_filename}"
                    else:
                        return jsonify({
                            'code': 500,
                            'message': 'OCT图像转换失败'
                        }), 500
                else:
                    # 如果已经是支持的格式，直接复制
                    display_filename = f"{patient_id}_OCT_{timestamp}.{ext}"
                    display_filename = secure_filename(display_filename)
                    display_path = os.path.join(upload_folder, display_filename)
                    
                    # 复制文件
                    with open(original_path, 'rb') as src, open(display_path, 'wb') as dst:
                        dst.write(src.read())
                    
                    oct_image_path = f"/api/images/{display_filename}"
            else:
                return jsonify({
                    'code': 400,
                    'message': 'OCT图像格式不支持或未提供'
                }), 400
                
        # 处理眼底图像
        if 'fundusImage' in request.files and (scan_type == 'Fundus' or scan_type == 'Both'):
            fundus_file = request.files['fundusImage']
            if fundus_file and fundus_file.filename and allowed_file(fundus_file.filename):
                # 获取文件扩展名
                ext = fundus_file.filename.rsplit('.', 1)[1].lower()
                
                # 保存原始文件
                original_filename = f"{patient_id}_Fundus_{timestamp}.{ext}"
                original_filename = secure_filename(original_filename)
                original_path = os.path.join(original_folder, original_filename)
                fundus_file.save(original_path)
                fundus_original_path = f"/api/originals/{original_filename}"
                
                # 如果是TIF格式，转换为PNG
                if ext in ['tif', 'tiff']:
                    png_filename = f"{patient_id}_Fundus_{timestamp}.png"
                    png_filename = secure_filename(png_filename)
                    png_path = os.path.join(upload_folder, png_filename)
                    
                    if convert_tif_to_png(original_path, png_path):
                        fundus_image_path = f"/api/images/{png_filename}"
                    else:
                        return jsonify({
                            'code': 500,
                            'message': '眼底图像转换失败'
                        }), 500
                else:
                    # 如果已经是支持的格式，直接复制
                    display_filename = f"{patient_id}_Fundus_{timestamp}.{ext}"
                    display_filename = secure_filename(display_filename)
                    display_path = os.path.join(upload_folder, display_filename)
                    
                    # 复制文件
                    with open(original_path, 'rb') as src, open(display_path, 'wb') as dst:
                        dst.write(src.read())
                    
                    fundus_image_path = f"/api/images/{display_filename}"
            else:
                return jsonify({
                    'code': 400,
                    'message': '眼底图像格式不支持或未提供'
                }), 400
                
        # 验证是否至少上传了一张图像
        if not oct_image_path and not fundus_image_path:
            return jsonify({
                'code': 400,
                'message': '至少需要上传一张图像'
            }), 400
            
        # 创建扫描记录
        scan = Scan(
            patient_id=patient_id,
            doctor_id=doctor_id,
            scan_type=scan_type,
            scan_time=datetime.utcnow(),
            oct_image_path=oct_image_path,
            fundus_image_path=fundus_image_path,
            oct_original_path=oct_original_path,
            fundus_original_path=fundus_original_path
        )
        db.session.add(scan)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'id': str(scan.id),
                'timestamp': scan.scan_time.strftime('%Y%m%d%H%M%S'),
                'octImageUrl': oct_image_path,
                'fundusImageUrl': fundus_image_path,
                'octOriginalUrl': oct_original_path,
                'fundusOriginalUrl': fundus_original_path
            }
        })
        
    except Exception as e:
        logger.error(f"上传扫描记录时出错: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@scan_bp.route('/link/<int:scan_id>/record/<int:record_id>', methods=['PUT'])
@login_required
def link_to_record(scan_id, record_id):
    """将扫描记录关联到病历"""
    try:
        # 获取扫描记录和病历
        scan = Scan.query.get(scan_id)
        if not scan:
            return jsonify({
                'code': 404,
                'message': '扫描记录不存在'
            }), 404
            
        from models import MedicalRecord
        record = MedicalRecord.query.get(record_id)
        if not record:
            return jsonify({
                'code': 404,
                'message': '病历不存在'
            }), 404
            
        # 验证患者ID是否匹配
        if scan.patient_id != record.patient_id:
            return jsonify({
                'code': 400,
                'message': '扫描记录和病历不属于同一患者'
            }), 400
            
        # 关联扫描记录到病历
        scan.medical_record_id = record_id
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': None
        })
        
    except Exception as e:
        logger.error(f"关联扫描记录到病历时出错: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500 