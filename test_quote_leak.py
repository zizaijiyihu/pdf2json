#!/usr/bin/env python3
"""
测试语录CRUD操作,检查是否还有semaphore泄漏
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quote_repository.db import create_quote, delete_quote, get_quotes

def test_quote_operations():
    print("测试语录操作...")
    
    # 1. 创建语录
    print("\n1. 创建语录...")
    result = create_quote("这是一条测试语录", 0)
    print(f"   创建成功: ID={result['id']}")
    quote_id = result['id']
    
    # 2. 获取语录列表
    print("\n2. 获取语录列表...")
    quotes = get_quotes(1, 10)
    print(f"   共有 {quotes['total']} 条语录")
    
    # 3. 删除语录
    print(f"\n3. 删除语录 ID={quote_id}...")
    delete_result = delete_quote(quote_id)
    print(f"   删除成功: {delete_result['message']}")
    
    print("\n✅ 所有操作完成,检查是否有semaphore泄漏警告...")

if __name__ == "__main__":
    test_quote_operations()
