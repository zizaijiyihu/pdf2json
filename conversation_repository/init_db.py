#!/usr/bin/env python3
"""
初始化会话管理数据库表

运行此脚本将创建 conversations 和 conversation_messages 表
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ks_infrastructure.db_session import db_session


def init_conversation_tables():
    """初始化会话管理相关的数据库表"""
    
    # 读取SQL文件
    sql_file = os.path.join(
        os.path.dirname(__file__),
        'schema.sql'
    )
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 分割SQL语句(按分号分割，过滤注释和空行)
    sql_statements = []
    for stmt in sql_content.split(';'):
        # 移除注释行
        lines = [
            line for line in stmt.split('\n')
            if line.strip() and not line.strip().startswith('--')
        ]
        stmt_clean = '\n'.join(lines).strip()
        if stmt_clean:
            sql_statements.append(stmt_clean)
    
    print("开始初始化会话管理数据库表...")
    print(f"共 {len(sql_statements)} 条SQL语句")
    
    try:
        with db_session() as cursor:
            for i, statement in enumerate(sql_statements, 1):
                print(f"\n执行第 {i} 条SQL语句...")
                print(f"语句预览: {statement[:100]}...")
                cursor.execute(statement)
                print(f"✓ 成功")
        
        print("\n" + "="*50)
        print("✓ 数据库表初始化成功！")
        print("="*50)
        print("\n创建的表:")
        print("  - conversations (会话表)")
        print("  - conversation_messages (消息表)")
        
    except Exception as e:
        print(f"\n✗ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def check_tables():
    """检查表是否存在"""
    print("\n检查表是否存在...")
    
    try:
        with db_session(dictionary=True) as cursor:
            # 检查 conversations 表
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = 'conversations'
            """)
            result = cursor.fetchone()
            conversations_exists = result['count'] > 0
            
            # 检查 conversation_messages 表
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = 'conversation_messages'
            """)
            result = cursor.fetchone()
            messages_exists = result['count'] > 0
            
            print(f"  conversations 表: {'✓ 存在' if conversations_exists else '✗ 不存在'}")
            print(f"  conversation_messages 表: {'✓ 存在' if messages_exists else '✗ 不存在'}")
            
            return conversations_exists and messages_exists
            
    except Exception as e:
        print(f"检查失败: {e}")
        return False


if __name__ == '__main__':
    print("="*50)
    print("会话管理模块 - 数据库初始化")
    print("="*50)
    
    # 先检查表是否已存在
    if check_tables():
        print("\n⚠️  表已存在！")
        response = input("是否要重新创建表? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("取消操作")
            sys.exit(0)
        
        print("\n删除现有表...")
        try:
            with db_session() as cursor:
                cursor.execute("DROP TABLE IF EXISTS conversation_messages")
                cursor.execute("DROP TABLE IF EXISTS conversations")
            print("✓ 删除成功")
        except Exception as e:
            print(f"✗ 删除失败: {e}")
            sys.exit(1)
    
    # 初始化表
    init_conversation_tables()
    
    # 再次检查
    print("\n验证表创建...")
    if check_tables():
        print("\n✓ 验证成功！所有表已正确创建。")
    else:
        print("\n✗ 验证失败！请检查错误信息。")
        sys.exit(1)
