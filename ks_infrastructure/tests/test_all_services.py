#!/usr/bin/env python3
"""
测试所有基础设施服务的功能

该脚本测试ks_infrastructure模块中所有服务的功能，
包括数据存储、检索、处理等操作，而不仅仅是连接测试。
"""

import os
import sys
import tempfile
import uuid
import base64
import json
import time
import io

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def test_mysql_functionality():
    """测试MySQL服务功能"""
    print("=== 测试MySQL服务功能 ===")
    try:
        from ks_infrastructure import ks_mysql
        
        # 获取MySQL连接
        mysql_client = ks_mysql()
        cursor = mysql_client.cursor()
        
        # 创建测试表
        table_name = f"test_table_{uuid.uuid4().hex[:8]}"
        create_table_sql = f"""
        CREATE TABLE {table_name} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            age INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_table_sql)
        print(f"✓ 成功创建测试表 {table_name}")
        
        # 插入测试数据
        insert_sql = f"INSERT INTO {table_name} (name, age) VALUES (%s, %s)"
        test_data = [("张三", 25), ("李四", 30)]
        cursor.executemany(insert_sql, test_data)
        mysql_client.commit()
        print(f"✓ 成功插入 {len(test_data)} 条测试数据")
        
        # 查询数据
        select_sql = f"SELECT id, name, age FROM {table_name}"
        cursor.execute(select_sql)
        results = cursor.fetchall()
        print(f"✓ 成功查询到 {len(results)} 条记录")
        for row in results:
            print(f"  - ID: {row[0]}, Name: {row[1]}, Age: {row[2]}")
        
        # 删除测试表
        cursor.execute(f"DROP TABLE {table_name}")
        mysql_client.commit()
        print(f"✓ 成功删除测试表 {table_name}")
        
        cursor.close()
        mysql_client.close()
        return True
        
    except Exception as e:
        print(f"✗ MySQL功能测试失败: {e}")
        return False

def test_minio_functionality():
    """测试MinIO服务功能"""
    print("\n=== 测试MinIO服务功能 ===")
    try:
        from ks_infrastructure import ks_minio
        
        # 获取MinIO客户端
        minio_client = ks_minio()
        
        # 创建测试bucket
        bucket_name = f"test-bucket-{uuid.uuid4().hex[:8]}"
        minio_client.create_bucket(Bucket=bucket_name)
        print(f"✓ 成功创建bucket: {bucket_name}")
        
        # 上传测试文件
        test_content = "这是一个测试文件的内容"
        test_key = "test-file.txt"
        minio_client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=test_content.encode('utf-8'),
            ContentLength=len(test_content.encode('utf-8')),
            ContentType='text/plain'
        )
        print(f"✓ 成功上传文件: {test_key}")
        
        # 下载并验证文件
        response = minio_client.get_object(Bucket=bucket_name, Key=test_key)
        downloaded_content = response['Body'].read().decode('utf-8')
        if downloaded_content == test_content:
            print("✓ 成功下载并验证文件内容")
        else:
            print("✗ 下载的文件内容不匹配")
            return False
        
        # 删除测试对象和bucket
        minio_client.delete_object(Bucket=bucket_name, Key=test_key)
        minio_client.delete_bucket(Bucket=bucket_name)
        print("✓ 成功清理测试数据")
        
        return True
        
    except Exception as e:
        print(f"✗ MinIO功能测试失败: {e}")
        return False

def test_qdrant_functionality():
    """测试Qdrant服务功能"""
    print("\n=== 测试Qdrant服务功能 ===")
    try:
        from ks_infrastructure import ks_qdrant
        
        # 获取Qdrant客户端
        qdrant_client = ks_qdrant()
        
        # 创建测试集合
        collection_name = f"test_collection_{uuid.uuid4().hex[:8]}"
        qdrant_client.recreate_collection(
            collection_name=collection_name,
            vectors_config={
                "size": 4,
                "distance": "Cosine"
            }
        )
        print(f"✓ 成功创建集合: {collection_name}")
        
        # 插入测试向量点
        points = [
            {"id": 1, "vector": [0.1, 0.2, 0.3, 0.4], "payload": {"city": "北京", "population": 21000000}},
            {"id": 2, "vector": [0.5, 0.6, 0.7, 0.8], "payload": {"city": "上海", "population": 24000000}}
        ]
        
        qdrant_client.upsert(
            collection_name=collection_name,
            points=points
        )
        print(f"✓ 成功插入 {len(points)} 个向量点")
        
        # 搜索相似向量
        search_result = qdrant_client.search(
            collection_name=collection_name,
            query_vector=[0.1, 0.2, 0.3, 0.4],
            limit=2
        )
        print(f"✓ 成功搜索到 {len(search_result)} 个相似向量")
        for result in search_result:
            print(f"  - ID: {result.id}, Score: {result.score:.4f}, Payload: {result.payload}")
        
        # 删除测试集合
        qdrant_client.delete_collection(collection_name=collection_name)
        print(f"✓ 成功删除集合: {collection_name}")
        
        return True
        
    except Exception as e:
        print(f"✗ Qdrant功能测试失败: {e}")
        return False

def test_openai_functionality():
    """测试OpenAI服务功能"""
    print("\n=== 测试OpenAI服务功能 ===")
    try:
        from ks_infrastructure import ks_openai
        from ks_infrastructure.configs.default import OPENAI_CONFIG
        
        # 获取OpenAI客户端
        openai_client = ks_openai()
        
        # 发起聊天请求
        response = openai_client.chat.completions.create(
            model="DeepSeek-V3.1-Ksyun",
            messages=[
                {"role": "system", "content": "你是人工智能助手"},
                {"role": "user", "content": "请列出3个中国的省会城市"}
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        if response.choices and response.choices[0].message.content:
            print("✓ 成功获得AI响应:")
            cities = response.choices[0].message.content.strip()
            print(f"  {cities}")
            return True
        else:
            print("✗ AI响应为空")
            return False
            
    except Exception as e:
        print(f"✗ OpenAI功能测试失败: {e}")
        return False

def test_embedding_functionality():
    """测试Embedding服务功能"""
    print("\n=== 测试Embedding服务功能 ===")
    try:
        from ks_infrastructure import ks_embedding
        
        # 获取Embedding服务
        embedding_service = ks_embedding()
        
        # 测试文本嵌入功能
        test_text = "人工智能是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。"
        
        # 方法1: 获取完整响应
        result = embedding_service.create_embedding(test_text)
        if result.get('data') and len(result['data']) > 0:
            embedding = result['data'][0]['embedding']
            dimensions = len(embedding)
            print(f"✓ 成功生成文本嵌入向量，维度: {dimensions}")
            print(f"  前5个维度值: {[round(val, 4) for val in embedding[:5]]}")
        else:
            print("✗ Embedding服务响应异常")
            return False
        
        # 方法2: 直接获取向量数组
        vector = embedding_service.get_embedding_vector(test_text)
        if vector and len(vector) > 0:
            print(f"✓ 成功获取嵌入向量，维度: {len(vector)}")
            print(f"  前5个维度值: {[round(val, 4) for val in vector[:5]]}")
            return True
        else:
            print("✗ 获取嵌入向量失败")
            return False
            
    except Exception as e:
        print(f"✗ Embedding功能测试失败: {e}")
        return False

def test_vision_functionality():
    """测试Vision服务功能"""
    print("\n=== 测试Vision服务功能 ===")
    try:
        from ks_infrastructure import ks_vision
        from PIL import Image, ImageDraw
        
        # 创建测试图像
        image = Image.new('RGB', (200, 200), color=(73, 109, 137))
        draw = ImageDraw.Draw(image)
        draw.rectangle([50, 50, 150, 150], fill=(255, 255, 255))
        draw.text((60, 60), "Test Image", fill=(255, 0, 0))
        
        # 保存到内存缓冲区
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_data = buffer.getvalue()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # 获取Vision客户端
        vision_client = ks_vision()
        
        # 调用视觉分析（支持自定义提示词）
        result = vision_client.analyze_image(
            image_base64=image_base64,
            image_format="png",
            prompt="请用中文描述这张图片的背景和文字内容"
        )
        
        if result and not result.startswith("Error") and not result.startswith("图像分析错误"):
            print("✓ 成功获得视觉分析响应:")
            # 只显示前200个字符以避免输出过长
            print(f"  {result[:200]}{'...' if len(result) > 200 else ''}")
            return True
        else:
            print(f"✗ Vision服务响应异常: {result}")
            return False
            
    except Exception as e:
        print(f"✗ Vision功能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试所有基础设施服务的功能...")
    print("=" * 50)
    
    test_results = {}
    
    # 依次测试各项服务功能
    test_results['MySQL'] = test_mysql_functionality()
    test_results['MinIO'] = test_minio_functionality()
    test_results['Qdrant'] = test_qdrant_functionality()
    test_results['OpenAI'] = test_openai_functionality()
    test_results['Embedding'] = test_embedding_functionality()
    test_results['Vision'] = test_vision_functionality()
    
    # 输出测试总结
    print("\n" + "=" * 50)
    print("功能测试结果总结:")
    print("=" * 50)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for service, result in test_results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{service:>10}: {status}")
        if result:
            passed_tests += 1
    
    print("-" * 50)
    print(f"总计: {passed_tests}/{total_tests} 项测试通过")
    
    if passed_tests == total_tests:
        print("\n🎉 所有服务功能测试均通过!")
        return 0
    else:
        print(f"\n⚠ {total_tests - passed_tests} 项服务功能测试失败，请检查相关配置。")
        return 1

if __name__ == "__main__":
    sys.exit(main())