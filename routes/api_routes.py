import os
from flask import jsonify, send_file
from werkzeug.utils import secure_filename
from flask import current_app

# 添加新的路由处理TIF和PNG图像
@app.route('/api/tifs/<path:filename>', methods=['GET'])
def get_tif_image(filename):
    """获取TIF图像文件"""
    try:
        # 安全检查：防止路径遍历攻击
        if '..' in filename or filename.startswith('/'):
            return jsonify({'error': '无效的文件名'}), 400
            
        # 构建文件路径
        file_path = os.path.join('images/tifs', filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404
            
        # 返回文件
        return send_file(file_path)
        
    except Exception as e:
        logger.error(f"获取TIF图像文件时出错: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/pngs/<path:filename>', methods=['GET'])
def get_png_image(filename):
    """获取PNG图像文件"""
    try:
        # 安全检查：防止路径遍历攻击
        if '..' in filename or filename.startswith('/'):
            return jsonify({'error': '无效的文件名'}), 400
            
        # 构建文件路径
        file_path = os.path.join('images/pngs', filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404
            
        # 返回文件
        return send_file(file_path)
        
    except Exception as e:
        logger.error(f"获取PNG图像文件时出错: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500 