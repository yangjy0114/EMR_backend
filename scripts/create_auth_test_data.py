import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Department, User
from utils.auth import Auth

def create_auth_test_data():
    with app.app_context():
        try:
            # 创建眼科部门
            dept = Department.query.filter_by(name='眼科').first()
            if not dept:
                dept = Department(
                    name='眼科',
                    description='眼科部门'
                )
                db.session.add(dept)
                db.session.commit()
            
            # 创建测试用户
            test_users = [
                {
                    'username': 'doctor1',
                    'password': '123456',
                    'real_name': '张医生',
                    'department_id': dept.id
                },
                {
                    'username': 'doctor2',
                    'password': '123456',
                    'real_name': '李医生',
                    'department_id': dept.id
                }
            ]
            
            for user_data in test_users:
                if not User.query.filter_by(username=user_data['username']).first():
                    user = User(
                        username=user_data['username'],
                        password=Auth.hash_password(user_data['password']),
                        real_name=user_data['real_name'],
                        department_id=user_data['department_id']
                    )
                    db.session.add(user)
            
            db.session.commit()
            print("认证测试数据创建成功！")
            
        except Exception as e:
            print(f"创建认证测试数据时出错: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    create_auth_test_data() 