from flask import Blueprint, request, jsonify, send_file
from models import db, Scan, AIAnalysisResult
from utils.auth import login_required
from services.ai_service import AIService
import logging
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app

logger = logging.getLogger(__name__)
ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

@ai_bp.route('/analyze/image', methods=['POST'])
@login_required
def analyze_image():
    """分析上传的图像"""
    try:
        # 检查是否有文件上传
        if 'image' not in request.files:
            return jsonify({'code': 400, 'message': '没有上传图像'}), 400
            
        file = request.files['image']
        if file.filename == '':
            return jsonify({'code': 400, 'message': '没有选择图像'}), 400
            
        # 获取图像类型参数
        image_type = request.form.get('imageType', 'Fundus')
        
        # 获取患者ID参数
        patient_id = request.form.get('patientId')
        if not patient_id:
            return jsonify({'code': 400, 'message': '缺少患者ID参数'}), 400
            
        # 保存上传的图像
        filename = secure_filename(file.filename)
        
        # 确定保存路径
        if image_type.lower() == 'oct':
            png_path = os.path.join(current_app.config['UPLOAD_FOLDER_OCT'], filename)
            tif_filename = filename.replace('.png', '.tif') if filename.endswith('.png') else filename
            tif_path = os.path.join(current_app.config['ORIGINAL_FOLDER_OCT'], tif_filename)
        else:  # Fundus
            png_path = os.path.join(current_app.config['UPLOAD_FOLDER_FUNDUS'], filename)
            tif_filename = filename.replace('.png', '.tif') if filename.endswith('.png') else filename
            tif_path = os.path.join(current_app.config['ORIGINAL_FOLDER_FUNDUS'], tif_filename)
            
        # 保存文件
        file.save(png_path)
        
        # 如果是PNG格式，转换为TIF
        if filename.lower().endswith('.png'):
            from PIL import Image
            img = Image.open(png_path)
            img.save(tif_path)
            
        # 创建临时扫描记录
        scan = Scan(
            patient_id=patient_id,
            created_at=datetime.utcnow()
        )
        
        # 设置图像路径
        if image_type.lower() == 'oct':
            scan.oct_image_path = f"/api/pngs/oct/{filename}"
            scan.oct_original_path = f"/api/tifs/oct/{tif_filename}"
        else:  # Fundus
            scan.fundus_image_path = f"/api/pngs/fundus/{filename}"
            scan.fundus_original_path = f"/api/tifs/fundus/{tif_filename}"
            
        db.session.add(scan)
        db.session.commit()
        
        # 分析图像
        ai_service = AIService()
        result = ai_service.analyze_image(scan.id, image_type)
        
        if not result:
            return jsonify({'code': 500, 'message': 'AI分析失败'}), 500
            
        # 获取分析结果
        analysis = AIAnalysisResult.query.filter_by(scan_id=scan.id).first()
        if not analysis:
            return jsonify({'code': 500, 'message': '无法获取分析结果'}), 500
            
        # 生成报告
        if not analysis.report:
            report = ai_service.generate_report(analysis.id)
            analysis.report = report
            db.session.commit()
            
        # 返回结果
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'id': analysis.id,
                'scanId': scan.id,
                'segmentationImageUrl': analysis.segmentation_image_url,
                'classificationResult': analysis.classification_result,
                'report': analysis.report,
                'analyzedAt': analysis.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
        
    except Exception as e:
        logger.error(f"AI影像分析时出错: {str(e)}")
        return jsonify({'code': 500, 'message': f'服务器内部错误: {str(e)}'}), 500

@ai_bp.route('/generate/report', methods=['POST'])
@login_required
def generate_report():
    """生成AI诊断报告接口"""
    try:
        # 获取请求参数
        data = request.get_json()
        analysis_id = data.get('analysisId')
        
        # 参数验证
        if not analysis_id:
            return jsonify({
                'code': 400,
                'message': '缺少必要参数'
            }), 400
            
        # 获取分析结果
        analysis = AIAnalysisResult.query.get(analysis_id)
        if not analysis:
            return jsonify({
                'code': 404,
                'message': '分析结果不存在'
            }), 404
            
        # 调用AI服务生成报告
        ai_service = AIService()
        report = ai_service.generate_report(analysis_id)
        
        # 不更新分析结果
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'id': str(analysis.id),
                'scanId': str(analysis.scan_id),
                'segmentationImageUrl': analysis.segmentation_image_url,
                'classificationResult': analysis.classification_result,
                'report': report,  # 直接返回生成的报告
                'analyzedAt': analysis.created_at.strftime('%Y-%m-%d %H:%M:%S') if analysis.created_at else None
            }
        })
        
    except Exception as e:
        logger.error(f"生成AI诊断报告时出错: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@ai_bp.route('/analysis/<analysis_id>', methods=['GET'])
@login_required
def get_analysis(analysis_id):
    """获取分析结果接口，如果需要报告，就自动生成报告"""
    try:
        # 获取分析结果
        analysis = AIAnalysisResult.query.get(analysis_id)
        if not analysis:
            return jsonify({
                'code': 404,
                'message': '分析结果不存在'
            }), 404
            
        # 生成报告
        ai_service = AIService()
        report = ai_service.generate_report(analysis_id)
            
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'id': str(analysis.id),
                'scanId': str(analysis.scan_id),
                'segmentationImageUrl': analysis.segmentation_image_url,
                'classificationResult': analysis.classification_result,
                'report': report,  # 直接返回生成的报告
                'analyzedAt': analysis.created_at.strftime('%Y-%m-%d %H:%M:%S') if analysis.created_at else None
            }
        })
        
    except Exception as e:
        logger.error(f"获取分析结果时出错: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@ai_bp.route('/analyze/scan/<int:scan_id>', methods=['POST'])
def analyze_scan(scan_id):
    """分析扫描图像"""
    try:
        logger.info(f"扫描记录ID: {scan_id}")
        
        # 获取图像类型参数
        image_type = request.args.get('imageType', 'Fundus')
        
        # 获取扫描记录
        scan = Scan.query.get(scan_id)
        if not scan:
            return jsonify({'code': 404, 'message': '扫描记录不存在'}), 404
            
        # 记录图像路径
        logger.info(f"OCT图像路径: {scan.oct_image_path}")
        logger.info(f"眼底图像路径: {scan.fundus_image_path}")
        logger.info(f"OCT原始路径: {scan.oct_original_path}")
        logger.info(f"眼底原始路径: {scan.fundus_original_path}")
        
        # 分析图像
        ai_service = AIService()
        result = ai_service.analyze_image(scan_id, image_type)
        
        if not result:
            return jsonify({'code': 500, 'message': 'AI分析失败'}), 500
            
        # 获取分析结果
        analysis = AIAnalysisResult.query.filter_by(scan_id=scan_id).first()
        if not analysis:
            return jsonify({'code': 500, 'message': '无法获取分析结果'}), 500
            
        # 生成报告
        if not analysis.report:
            report = ai_service.generate_report(analysis.id)
            analysis.report = report
            db.session.commit()
            
        # 返回结果
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'id': analysis.id,
                'scanId': scan_id,
                'segmentationImageUrl': analysis.segmentation_image_url,
                'classificationResult': analysis.classification_result,
                'report': analysis.report,
                'analyzedAt': analysis.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
        
    except Exception as e:
        logger.error(f"AI影像分析时出错: {str(e)}")
        return jsonify({'code': 500, 'message': f'服务器内部错误: {str(e)}'}), 500 