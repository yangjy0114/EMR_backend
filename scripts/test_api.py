import requests
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_analyze_scan():
    """测试分析扫描记录API"""
    url = "http://localhost:5000/api/ai/analyze/scan/1"
    params = {"imageType": "Fundus"}
    
    try:
        response = requests.post(url, params=params)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.json()}")
    except Exception as e:
        print(f"请求出错: {str(e)}")

def test_analyze_image():
    """测试分析上传图像API"""
    url = "http://localhost:5000/api/ai/analyze/image"
    
    # 准备文件
    files = {"image": open("images/tifs/fundus/p001_fundus.tif", "rb")}
    
    # 准备表单数据
    data = {
        "imageType": "Fundus",
        "patientId": "1"
    }
    
    try:
        response = requests.post(url, files=files, data=data)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.json()}")
    except Exception as e:
        print(f"请求出错: {str(e)}")

if __name__ == "__main__":
    print("测试分析扫描记录API:")
    test_analyze_scan()
    
    print("\n测试分析上传图像API:")
    test_analyze_image() 