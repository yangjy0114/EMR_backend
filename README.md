# Eye Medical System Backend

医疗系统后端服务，提供用户认证、患者管理、图像处理等功能。

## 功能特性

- 用户认证（登录、登出、获取用户信息）
- 患者管理
- 医疗图像处理
- AI 辅助诊断

## 技术栈

- Python 3.8+
- Flask
- SQLAlchemy
- PyTorch
- JWT

## 安装和运行

1. 创建虚拟环境：
```bash
python -m venv myenv
source myenv/bin/activate  # Linux/Mac
myenv\Scripts\activate  # Windows
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 初始化数据库：
```bash
python scripts/reset_db.py
python scripts/create_auth_test_data.py
```

4. 运行服务：
```bash
python app.py
```

## API 文档

### 认证接口

#### 登录
POST /api/auth/login
...（其他接口文档）
