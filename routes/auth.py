import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Blueprint, request, jsonify
from models import db, User
from utils.auth import Auth
import logging
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def login_required(f):
    """验证token的装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未提供有效的认证信息'}), 401
            
        token = token.split(' ')[1]
        user_id = Auth.verify_token(token)
        if not user_id:
            return jsonify({'code': 401, 'message': 'token已过期或无效'}), 401
            
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 401, 'message': '用户不存在'}), 401
            
        return f(*args, **kwargs)
    return decorated

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'code': 400,
                'message': '用户名和密码不能为空'
            }), 400
            
        user = User.query.filter_by(username=username).first()
        
        if not user:
            return jsonify({
                'code': 401,
                'message': '用户名或密码错误'
            }), 401
            
        if user.is_locked:
            return jsonify({
                'code': 403,
                'message': '账号已被锁定，请联系管理员'
            }), 403
            
        if not Auth.check_password(user.password, password):
            user.login_fails += 1
            if user.login_fails >= Auth.MAX_LOGIN_FAILS:
                user.is_locked = True
                logger.warning(f"用户 {username} 已被锁定")
            db.session.commit()
            
            return jsonify({
                'code': 401,
                'message': '用户名或密码错误'
            }), 401
            
        # 登录成功，重置失败次数，更新登录时间
        user.login_fails = 0
        user.last_login_at = datetime.utcnow()
        db.session.commit()
        
        # 生成token
        token = Auth.generate_token(user.id)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'token': token,
                'userInfo': {
                    'id': user.id,
                    'username': user.username,
                    'realName': user.real_name,
                    'department': user.department.name,
                    'avatar': user.avatar
                }
            }
        })
        
    except Exception as e:
        logger.error(f"登录时发生错误: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """用户登出"""
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': None
    })

@auth_bp.route('/current-user', methods=['GET'])
@login_required
def get_current_user():
    """获取当前用户信息"""
    try:
        token = request.headers['Authorization'].split(' ')[1]
        user_id = Auth.verify_token(token)
        user = User.query.get(user_id)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'id': user.id,
                'username': user.username,
                'realName': user.real_name,
                'department': user.department.name,
                'avatar': user.avatar
            }
        })
        
    except Exception as e:
        logger.error(f"获取用户信息时发生错误: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500 