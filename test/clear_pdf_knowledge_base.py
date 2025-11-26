"""
清空 pdf_knowledge_base 集合中的所有数据
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ks_infrastructure import ks_qdrant

def clear_collection():
    """清空 pdf_knowledge_base 集合"""
    client = ks_qdrant()
    collection_name = "pdf_knowledge_base"

    print(f"准备清空集合: {collection_name}")
    print("=" * 60)

    # 获取集合信息
    try:
        collection_info = client.get_collection(collection_name)
        points_count = collection_info.points_count

        print(f"当前集合中有 {points_count} 条记录")

        if points_count == 0:
            print("集合已经是空的，无需清空")
            return

        # 确认操作
        print(f"\n⚠️  警告: 这将删除所有 {points_count} 条记录！")
        print("开始清空...")

        # 删除集合并重新创建（最快的清空方式）
        print("\n正在删除集合...")
        client.delete_collection(collection_name)
        print("✓ 集合已删除")

        # 重新创建集合
        print("\n正在重新创建集合...")
        from qdrant_client.models import Distance, VectorParams

        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "summary_vector": VectorParams(
                    size=4096,
                    distance=Distance.COSINE
                ),
                "content_vector": VectorParams(
                    size=4096,
                    distance=Distance.COSINE
                )
            }
        )
        print("✓ 集合已重新创建")

        # 验证
        collection_info = client.get_collection(collection_name)
        print(f"\n当前集合中有 {collection_info.points_count} 条记录")
        print("\n✅ 清空完成！")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    clear_collection()
