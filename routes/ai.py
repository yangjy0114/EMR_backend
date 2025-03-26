from flask import Blueprint, request, jsonify, send_file
from models import db, Scan, AIAnalysisResult
from utils.auth import login_required
from services.ai_service import AIService
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)
ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

@ai_bp.route('/analyze/image', methods=['POST'])
@login_required
def analyze_image():
    """AI影像分析接口"""
    try:
        # 获取请求参数
        scan_id = request.form.get('scanId')
        image_type = request.form.get('imageType')
        
        # 参数验证
        if not scan_id or not image_type:
            return jsonify({
                'code': 400,
                'message': '缺少必要参数'
            }), 400
            
        if image_type not in ['OCT', 'Fundus', 'Both']:
            return jsonify({
                'code': 400,
                'message': '无效的图像类型'
            }), 400
            
        # 获取扫描记录
        scan = Scan.query.get(scan_id)
        if not scan:
            return jsonify({
                'code': 404,
                'message': '扫描记录不存在'
            }), 404
            
        # 添加调试日志
        logger.info(f"扫描记录ID: {scan.id}")
        logger.info(f"OCT图像路径: {scan.oct_image_path}")
        logger.info(f"眼底图像路径: {scan.fundus_image_path}")
        logger.info(f"OCT原始路径: {scan.oct_original_path}")
        logger.info(f"眼底原始路径: {scan.fundus_original_path}")
        
        # 调用AI服务进行分析
        ai_service = AIService()
        result = ai_service.analyze_images(scan, image_type)
        
        # 保存分析结果
        analysis_result = AIAnalysisResult(
            scan_id=scan_id,
            segmentation_image_path=result['segmentation_image_path'],
            classification_result=result['classification_result']
        )
        db.session.add(analysis_result)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'id': str(analysis_result.id),
                'segmentationImageUrl': analysis_result.segmentation_image_url,
                'classificationResult': analysis_result.classification_result
            }
        })
        
    except Exception as e:
        logger.error(f"AI影像分析时出错: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

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