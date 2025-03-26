import os
import uuid
from datetime import datetime
from flask import Flask, request, send_file, jsonify
from werkzeug.utils import secure_filename
from models import db, Patient, Doctor, Scan, Image, SegmentedImage
import logging
from sqlalchemy.exc import SQLAlchemyError
from services.ai_service import AIService
from routes.auth import auth_bp
from routes.patient import patient_bp
from routes.medical_record import medical_record_bp
from routes.scan import scan_bp
from routes.ai import ai_bp

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 配置
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'mysql+mysqlconnector://root:59fh8r22@test-db-mysql.ns-32fwr7d7.svc:3306/test_db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'images/original'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB 最大文件大小
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('images/segmented', exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'scans'), exist_ok=True)
os.makedirs('images/segmentation', exist_ok=True)

# 初始化数据库
db.init_app(app)

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tiff', 'tif'}

# 初始化分割服务
ai_service = AIService()

# 注册认证蓝图
app.register_blueprint(auth_bp)

# 注册患者蓝图
app.register_blueprint(patient_bp)

# 注册病历管理蓝图
app.register_blueprint(medical_record_bp)

# 注册扫描蓝图
app.register_blueprint(scan_bp)

# 注册AI蓝图
app.register_blueprint(ai_bp)

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    """处理图像上传的接口"""
    try:
        patient_id = request.form.get('patient_id')
        doctor_id = request.form.get('doctor_id')
        
        # 详细的请求信息日志
        logger.info("=== 开始处理上传请求 ===")
        logger.info(f"请求方法: {request.method}")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"表单数据: {request.form}")
        logger.info(f"文件数据: {request.files}")
        logger.info(f"文件keys: {list(request.files.keys())}")
        
        if not patient_id or not doctor_id:
            logger.error(f"缺少参数 - patient_id: {patient_id}, doctor_id: {doctor_id}")
            return jsonify({'error': '缺少必要参数'}), 400
            
        # 验证患者和医生是否存在
        patient = db.session.get(Patient, patient_id)
        doctor = db.session.get(Doctor, doctor_id)
        
        if not patient or not doctor:
            logger.error(f"找不到记录 - patient: {patient}, doctor: {doctor}")
            return jsonify({'error': '患者或医生不存在'}), 404
            
        # 创建新的扫描记录
        scan = Scan(
            scan_id=str(uuid.uuid4()),
            patient_id=patient_id,
            doctor_id=doctor_id,
            scan_date=datetime.utcnow()
        )
        db.session.add(scan)
        
        uploaded_images = []
        files = request.files.getlist('images')
        logger.info(f"接收到的文件数量: {len(files)}")
        
        if not files:
            logger.warning("没有接收到任何文件")
            return jsonify({'error': '没有上传文件'}), 400
        
        for file in files:
            logger.info(f"处理文件: {file.filename}")
            if not file.filename:
                logger.warning("文件名为空")
                continue
                
            if file and allowed_file(file.filename):
                # 生成时间戳
                timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                
                # 从原始文件名中获取患者ID和类型
                original_filename = file.filename.lower()
                if 'oct' in original_filename:
                    file_type = 'oct'
                elif 'fundus' in original_filename:
                    file_type = 'fundus'
                else:
                    logger.warning(f"无法从文件名确定图像类型: {file.filename}")
                    continue
                
                # 提取患者ID（假设格式为 p001_xxx.tif）
                try:
                    patient_prefix = original_filename.split('_')[0]
                except:
                    patient_prefix = f"p{patient_id}"  # 如果无法从文件名获取，使用传入的patient_id
                
                new_filename = f"{patient_prefix}_{file_type}_{timestamp}.{file.filename.rsplit('.', 1)[1].lower()}"
                
                filename = secure_filename(new_filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                try:
                    file.save(file_path)
                    logger.info(f"文件保存到: {file_path}")
                except Exception as e:
                    logger.error(f"保存文件时出错: {str(e)}")
                    continue
                
                # 创建图像记录
                image = Image(
                    image_id=str(uuid.uuid4()),
                    scan_id=scan.scan_id,
                    image_type='OCT' if 'oct' in filename.lower() else '眼底图像',
                    image_path=file_path
                )
                db.session.add(image)
                uploaded_images.append({
                    'image_id': image.image_id,
                    'image_type': image.image_type,
                    'filename': filename
                })
                logger.info(f"图像记录已创建: {image.image_id}")
            else:
                logger.warning(f"文件 {file.filename} 不被允许或无效")
        
        if not uploaded_images:
            logger.warning("没有成功上传任何图片")
            return jsonify({'error': '没有成功上传任何图片'}), 400
        
        db.session.commit()
        logger.info("数据库事务已提交")
        logger.info(f"上传成功 - scan_id: {scan.scan_id}, images: {uploaded_images}")
        
        return jsonify({
            'scan_id': scan.scan_id,
            'uploaded_images': uploaded_images
        }), 201
        
    except Exception as e:
        logger.error(f"上传图像时发生错误: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-image/<image_id>', methods=['GET'])
def download_image(image_id):
    """处理图像下载的接口"""
    try:
        image = db.session.get(Image, image_id)
        
        if not image:
            return jsonify({'error': '图像不存在'}), 404
            
        return send_file(image.image_path, as_attachment=True)
        
    except Exception as e:
        logger.error(f"下载图像时发生错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/list-images/<scan_id>', methods=['GET'])
def list_images(scan_id):
    """列出指定扫描记录的所有图片"""
    try:
        scan = db.session.get(Scan, scan_id)
        if not scan:
            return jsonify({'error': '扫描记录不存在'}), 404
            
        images = Image.query.filter_by(scan_id=scan_id).all()
        image_list = [{
            'image_id': img.image_id,
            'image_type': img.image_type,
            'filename': os.path.basename(img.image_path)
        } for img in images]
        
        return jsonify({
            'scan_id': scan_id,
            'images': image_list
        })
        
    except Exception as e:
        logger.error(f"列出图片时发生错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/segment-image', methods=['POST'])
def segment_image():
    """处理图像分割的接口"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data or 'image_id' not in data:
            return jsonify({'error': '缺少图像ID'}), 400
            
        image_id = data['image_id']
        
        # 获取原始图像
        image = db.session.get(Image, image_id)
        if not image:
            return jsonify({'error': '图像不存在'}), 404
            
        # 创建分割记录
        segmented = SegmentedImage(
            segmented_id=str(uuid.uuid4()),
            image_id=image_id,
            segmented_image_path='pending',
            status='pending'
        )
        db.session.add(segmented)
        db.session.commit()
        
        try:
            # 执行分割
            output_path = ai_service.segment_image(image.image_path)
            
            # 更新分割记录
            segmented.segmented_image_path = output_path
            segmented.status = 'completed'
            db.session.commit()
            
            return jsonify({
                'segmented_id': segmented.segmented_id,
                'original_image_id': image_id,
                'segmented_image_path': output_path,
                'status': 'completed'
            }), 201
            
        except Exception as e:
            # 记录错误并更新状态
            segmented.status = 'failed'
            segmented.error_message = str(e)
            db.session.commit()
            raise
            
    except Exception as e:
        logger.error(f"处理分割请求时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-segmented-image/<segmented_id>', methods=['GET'])
def get_segmented_image(segmented_id):
    """获取分割后的图像"""
    try:
        segmented = db.session.get(SegmentedImage, segmented_id)
        if not segmented:
            return jsonify({'error': '分割图像不存在'}), 404
            
        return send_file(segmented.segmented_image_path, as_attachment=True)
        
    except Exception as e:
        logger.error(f"获取分割图像时发生错误: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/images/<filename>', methods=['GET'])
def get_image(filename):
    """获取图像文件"""
    try:
        # 安全检查：防止路径遍历攻击
        if '..' in filename or filename.startswith('/'):
            return jsonify({'error': '无效的文件名'}), 400
            
        # 构建文件路径
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'scans', filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404
            
        # 返回文件
        return send_file(file_path)
        
    except Exception as e:
        logger.error(f"获取图像文件时出错: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/originals/<filename>', methods=['GET'])
def get_original_image(filename):
    """获取原始图像文件"""
    try:
        # 安全检查：防止路径遍历攻击
        if '..' in filename or filename.startswith('/'):
            return jsonify({'error': '无效的文件名'}), 400
            
        # 构建文件路径
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'originals', filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404
            
        # 返回文件
        return send_file(file_path)
        
    except Exception as e:
        logger.error(f"获取原始图像文件时出错: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/images/segmentation/<filename>', methods=['GET'])
def get_segmentation_image(filename):
    """获取分割图像文件"""
    try:
        # 安全检查：防止路径遍历攻击
        if '..' in filename or filename.startswith('/'):
            return jsonify({'error': '无效的文件名'}), 400
            
        # 构建文件路径
        file_path = os.path.join('images/segmentation', filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404
            
        # 返回文件
        return send_file(file_path)
        
    except Exception as e:
        logger.error(f"获取分割图像文件时出错: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@app.errorhandler(SQLAlchemyError)
def handle_db_error(error):
    logger.error(f"数据库错误: {str(error)}")
    return jsonify({'error': '数据库连接错误'}), 500

if __name__ == '__main__':
    # 修改为监听所有地址，并指定端口
    app.run(host='0.0.0.0', port=5000, debug=True) 