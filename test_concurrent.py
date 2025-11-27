#!/usr/bin/env python3
"""
并发测试 - 验证连接池在多线程环境下的表现
"""

import sys
import os
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quote_repository.db import create_quote, delete_quote, get_quotes

def worker(worker_id, results):
    """工作线程函数"""
    try:
        # 1. 创建语录
        result = create_quote(f"并发测试语录-{worker_id}", 0)
        quote_id = result['id']
        print(f"  [Worker {worker_id}] 创建成功: ID={quote_id}")
        
        # 2. 查询列表
        quotes = get_quotes(1, 10)
        print(f"  [Worker {worker_id}] 查询成功: 共{quotes['total']}条")
        
        # 3. 删除语录
        delete_quote(quote_id)
        print(f"  [Worker {worker_id}] 删除成功: ID={quote_id}")
        
        results[worker_id] = "SUCCESS"
    except Exception as e:
        print(f"  [Worker {worker_id}] 失败: {e}")
        results[worker_id] = f"FAILED: {e}"

def test_concurrent_operations():
    print("=" * 60)
    print("并发测试 - 10个线程同时操作数据库")
    print("=" * 60)
    
    num_threads = 10
    threads = []
    results = {}
    
    start_time = time.time()
    
    # 创建并启动线程
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(i, results))
        threads.append(t)
        t.start()
    
    # 等待所有线程完成
    for t in threads:
        t.join()
    
    end_time = time.time()
    
    # 统计结果
    success_count = sum(1 for r in results.values() if r == "SUCCESS")
    failed_count = num_threads - success_count
    
    print("\n" + "=" * 60)
    print("测试结果:")
    print(f"  总线程数: {num_threads}")
    print(f"  成功: {success_count}")
    print(f"  失败: {failed_count}")
    print(f"  耗时: {end_time - start_time:.2f}秒")
    print("=" * 60)
    
    if failed_count > 0:
        print("\n失败详情:")
        for worker_id, result in results.items():
            if result != "SUCCESS":
                print(f"  Worker {worker_id}: {result}")
    
    print("\n✅ 并发测试完成,请检查是否有semaphore泄漏警告")
    print("   如果没有警告,说明连接池工作正常!")

if __name__ == "__main__":
    test_concurrent_operations()
