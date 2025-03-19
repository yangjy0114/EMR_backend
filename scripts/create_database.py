from mysql import connector

def create_database():
    # 创建数据库连接
    cnx = connector.connect(
        host='test-db-mysql.ns-32fwr7d7.svc',
        user='root',
        password='59fh8r22'
    )
    
    cursor = cnx.cursor()
    
    try:
        # 创建数据库
        cursor.execute("CREATE DATABASE IF NOT EXISTS `test_db`")
        print("数据库创建成功！")
    except Exception as e:
        print(f"创建数据库时出错: {str(e)}")
    finally:
        cursor.close()
        cnx.close()

if __name__ == "__main__":
    create_database() 