import jwt
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)

class Auth:
    """认证工具类"""
    
    SECRET_KEY = "your-secret-key"  # 实际应用中应该从配置文件读取
    TOKEN_EXPIRY = timedelta(hours=24)
    MAX_LOGIN_FAILS = 5  # 最大登录失败次数
    
    @staticmethod
    def hash_password(password):
        """对密码进行哈希"""
        return generate_password_hash(password)
    
    @staticmethod
    def check_password(hash_value, password):
        """验证密码"""
        return check_password_hash(hash_value, password)
    
    @classmethod
    def generate_token(cls, user_id):
        """生成JWT token"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + cls.TOKEN_EXPIRY
        }
        return jwt.encode(payload, cls.SECRET_KEY, algorithm='HS256')
    
    @classmethod
    def verify_token(cls, token):
        """验证JWT token"""
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=['HS256'])
            return payload['user_id']
        except jwt.ExpiredSignatureError:
            logger.warning("Token已过期")
            return None
        except jwt.InvalidTokenError:
            logger.warning("无效的Token")
            return None

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
            
        return f(*args, **kwargs)
    return decorated 