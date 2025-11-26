"""
检查 Qdrant 中 pdf_knowledge_base 集合里的 owner 字段值
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ks_infrastructure import ks_qdrant

def check_owners():
    """检查 Qdrant 中的 owner 值"""
    client = ks_qdrant()
    collection_name = "pdf_knowledge_base"

    print(f"检查集合: {collection_name}")
    print("=" * 60)

    # 获取所有点 (限制前20个)
    scroll_result = client.scroll(
        collection_name=collection_name,
        limit=20,
        with_payload=True,
        with_vectors=False
    )

    points = scroll_result[0]

    if not points:
        print("集合中没有数据")
        return

    print(f"找到 {len(points)} 条记录\n")

    # 统计 owner 值
    owner_stats = {}

    for point in points:
        payload = point.payload
        owner = payload.get('owner', 'N/A')
        filename = payload.get('filename', 'N/A')
        page_number = payload.get('page_number', 'N/A')

        print(f"ID: {point.id}")
        print(f"  Owner: '{owner}' (长度: {len(owner) if owner != 'N/A' else 0})")
        print(f"  Filename: {filename}")
        print(f"  Page: {page_number}")
        print()

        # 统计
        if owner not in owner_stats:
            owner_stats[owner] = 0
        owner_stats[owner] += 1

    print("=" * 60)
    print("Owner 统计:")
    for owner, count in owner_stats.items():
        print(f"  '{owner}': {count} 条记录")

if __name__ == "__main__":
    check_owners()
