import os
import uuid
from flask import Blueprint, request, jsonify, send_file, current_app
from models import db, Scan, Patient, User, PatientScanMapping
from utils.auth import login_required
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np
import re

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
        
        # 记录查询结果
        logger.info(f"找到 {len(scans)} 条扫描记录，patient_id={patient_id}")
        
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

@scan_bp.route('/upload', methods=['POST'])
@login_required
def upload_scan():
    """上传新的扫描记录"""
    try:
        # 获取请求参数
        patient_id = request.form.get('patientId')
        if not patient_id:
            return jsonify({
                'code': 400,
                'message': '缺少患者ID参数'
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
        
        # 获取医生信息
        doctor = User.query.get(doctor_id)
        if not doctor:
            return jsonify({
                'code': 401,
                'message': '无效的用户'
            }), 401
            
        # 检查是否有文件上传
        if 'octImage' not in request.files and 'fundusImage' not in request.files:
            return jsonify({
                'code': 400,
                'message': '没有上传图像文件'
            }), 400
            
        # 获取OCT图像
        oct_file = request.files.get('octImage')
        oct_image_path = None
        oct_original_path = None
        
        # 获取眼底图像
        fundus_file = request.files.get('fundusImage')
        fundus_image_path = None
        fundus_original_path = None
        
        # 获取最新的图像序号
        latest_oct_number = get_latest_image_number('oct')
        latest_fundus_number = get_latest_image_number('fundus')
        
        # 处理OCT图像
        if oct_file and oct_file.filename:
            if allowed_file(oct_file.filename):
                # 生成新的文件名
                new_oct_number = latest_oct_number + 1
                oct_filename = f"p{new_oct_number:03d}_oct.png"
                oct_tif_filename = f"p{new_oct_number:03d}_oct.tif"
                
                # 保存PNG文件
                oct_png_path = os.path.join(current_app.config['UPLOAD_FOLDER_OCT'], oct_filename)
                oct_file.save(oct_png_path)
                oct_image_path = f"/api/pngs/oct/{oct_filename}"
                
                # 保存TIF文件（如果原始文件是TIF格式）
                if oct_file.filename.lower().endswith(('.tif', '.tiff')):
                    oct_tif_path = os.path.join(current_app.config['ORIGINAL_FOLDER_OCT'], oct_tif_filename)
                    oct_file.seek(0)  # 重置文件指针
                    oct_file.save(oct_tif_path)
                    oct_original_path = f"/api/tifs/oct/{oct_tif_filename}"
                else:
                    # 如果原始文件不是TIF格式，将PNG转换为TIF
                    oct_tif_path = os.path.join(current_app.config['ORIGINAL_FOLDER_OCT'], oct_tif_filename)
                    convert_png_to_tif(oct_png_path, oct_tif_path)
                    oct_original_path = f"/api/tifs/oct/{oct_tif_filename}"
                
                logger.info(f"OCT图像已保存: {oct_png_path}")
            else:
                return jsonify({
                    'code': 400,
                    'message': f"不支持的OCT图像格式: {oct_file.filename}"
                }), 400
        
        # 处理眼底图像
        if fundus_file and fundus_file.filename:
            if allowed_file(fundus_file.filename):
                # 生成新的文件名
                new_fundus_number = latest_fundus_number + 1
                fundus_filename = f"p{new_fundus_number:03d}_fundus.png"
                fundus_tif_filename = f"p{new_fundus_number:03d}_fundus.tif"
                
                # 保存PNG文件
                fundus_png_path = os.path.join(current_app.config['UPLOAD_FOLDER_FUNDUS'], fundus_filename)
                fundus_file.save(fundus_png_path)
                fundus_image_path = f"/api/pngs/fundus/{fundus_filename}"
                
                # 保存TIF文件（如果原始文件是TIF格式）
                if fundus_file.filename.lower().endswith(('.tif', '.tiff')):
                    fundus_tif_path = os.path.join(current_app.config['ORIGINAL_FOLDER_FUNDUS'], fundus_tif_filename)
                    fundus_file.seek(0)  # 重置文件指针
                    fundus_file.save(fundus_tif_path)
                    fundus_original_path = f"/api/tifs/fundus/{fundus_tif_filename}"
                else:
                    # 如果原始文件不是TIF格式，将PNG转换为TIF
                    fundus_tif_path = os.path.join(current_app.config['ORIGINAL_FOLDER_FUNDUS'], fundus_tif_filename)
                    convert_png_to_tif(fundus_png_path, fundus_tif_path)
                    fundus_original_path = f"/api/tifs/fundus/{fundus_tif_filename}"
                
                logger.info(f"眼底图像已保存: {fundus_png_path}")
            else:
                return jsonify({
                    'code': 400,
                    'message': f"不支持的眼底图像格式: {fundus_file.filename}"
                }), 400
        
        # 确定扫描类型
        if oct_image_path and fundus_image_path:
            scan_type = 'Both'
        elif oct_image_path:
            scan_type = 'OCT'
        elif fundus_image_path:
            scan_type = 'Fundus'
        else:
            return jsonify({
                'code': 400,
                'message': '没有有效的图像文件'
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
            fundus_original_path=fundus_original_path,
            created_at=datetime.utcnow()
        )
        db.session.add(scan)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '扫描记录上传成功',
            'data': {
                'id': scan.id,
                'patientId': patient_id,
                'scanType': scan_type,
                'octImage': oct_image_path,
                'fundusImage': fundus_image_path,
                'timestamp': scan.scan_time.strftime('%Y%m%d%H%M%S')
            }
        })
        
    except Exception as e:
        logger.error(f"上传扫描记录时出错: {str(e)}")
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'服务器内部错误: {str(e)}'
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

def get_latest_image_number(image_type):
    """获取最新的图像序号"""
    try:
        if image_type.lower() == 'oct':
            folder_path = current_app.config['UPLOAD_FOLDER_OCT']
        else:  # fundus
            folder_path = current_app.config['UPLOAD_FOLDER_FUNDUS']
        
        # 获取文件夹中的所有文件
        files = os.listdir(folder_path)
        
        # 筛选出符合命名规则的文件
        pattern = r'p(\d+)_' + image_type.lower() + r'\.png'
        numbers = []
        
        for file in files:
            match = re.match(pattern, file)
            if match:
                number = int(match.group(1))
                numbers.append(number)
        
        # 如果没有找到符合规则的文件，返回0
        if not numbers:
            return 0
        
        # 返回最大的序号
        return max(numbers)
        
    except Exception as e:
        logger.error(f"获取最新图像序号时出错: {str(e)}")
        return 0

def convert_png_to_tif(png_path, tif_path):
    """将PNG图像转换为TIF格式"""
    try:
        # 打开PNG图像
        with Image.open(png_path) as img:
            # 保存为TIF
            img.save(tif_path, 'TIFF')
        
        return True
    except Exception as e:
        logger.error(f"转换图像格式时出错: {str(e)}")
        return False 