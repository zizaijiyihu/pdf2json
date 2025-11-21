"""
文件存储仓库数据库集成测试
"""

import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from file_repository import upload_file, get_owner_file_list, set_file_public


def test_upload_with_metadata():
    """测试上传文件并保存元数据"""
    print("\n=== 测试 1: 上传文件并保存元数据 ===")

    test_file_path = os.path.join(os.path.dirname(__file__), "居住证办理.pdf")
    owner = "alice"
    filename = "document.pdf"

    # 上传私有文件
    print(f"\n1.1 上传私有文件: {owner}/{filename} (is_public=0)")
    with open(test_file_path, "rb") as f:
        result = upload_file(
            username=owner,
            filename=filename,
            file_data=f,
            bucket="kms",
            content_type="application/pdf",
            is_public=0
        )
    print(f"✓ 上传成功: {result}")

    # 上传公开文件
    print(f"\n1.2 上传公开文件: {owner}/public_doc.pdf (is_public=1)")
    with open(test_file_path, "rb") as f:
        result = upload_file(
            username=owner,
            filename="public_doc.pdf",
            file_data=f,
            bucket="kms",
            content_type="application/pdf",
            is_public=1
        )
    print(f"✓ 上传成功: {result}")


def test_get_owner_files():
    """测试获取所有者文件列表"""
    print("\n\n=== 测试 2: 获取所有者文件列表 ===")

    test_file_path = os.path.join(os.path.dirname(__file__), "居住证办理.pdf")
    owner = "bob"

    # 上传测试文件
    print(f"\n2.1 为用户 {owner} 上传测试文件")
    files_to_upload = [
        ("private1.pdf", 0),
        ("private2.pdf", 0),
        ("public1.pdf", 1)
    ]

    for fname, is_public in files_to_upload:
        with open(test_file_path, "rb") as f:
            upload_file(owner, fname, f, bucket="kms", is_public=is_public)
        public_str = "公开" if is_public == 1 else "私有"
        print(f"  ✓ 上传: {owner}/{fname} ({public_str})")

    # 获取所有者的文件（不包含公开文件）
    print(f"\n2.2 获取 {owner} 的文件列表（include_public=False）")
    files = get_owner_file_list(owner, include_public=False)
    print(f"✓ 找到 {len(files)} 个文件:")
    for file_info in files:
        public_str = "公开" if file_info['is_public'] == 1 else "私有"
        print(f"  - {file_info['filename']} ({public_str}, {file_info['file_size']} bytes)")

    # 获取所有者的文件 + 公开文件
    print(f"\n2.3 获取 {owner} 的文件列表（include_public=True）")
    files_with_public = get_owner_file_list(owner, include_public=True)
    print(f"✓ 找到 {len(files_with_public)} 个文件:")
    for file_info in files_with_public:
        public_str = "公开" if file_info['is_public'] == 1 else "私有"
        owner_str = file_info['owner']
        print(f"  - {file_info['filename']} (所有者:{owner_str}, {public_str})")


def test_set_file_public():
    """测试设置文件公开状态"""
    print("\n\n=== 测试 3: 设置文件公开状态 ===")

    test_file_path = os.path.join(os.path.dirname(__file__), "居住证办理.pdf")
    owner = "charlie"
    filename = "toggle_test.pdf"

    # 上传私有文件
    print(f"\n3.1 上传私有文件: {owner}/{filename}")
    with open(test_file_path, "rb") as f:
        upload_file(owner, filename, f, bucket="kms", is_public=0)
    print(f"✓ 上传成功")

    # 查看初始状态
    files = get_owner_file_list(owner, include_public=False)
    initial_file = [f for f in files if f['filename'] == filename][0]
    print(f"✓ 初始状态: is_public={initial_file['is_public']}")

    # 设置为公开
    print(f"\n3.2 设置文件为公开 (is_public=1)")
    success = set_file_public(owner, filename, 1)
    if success:
        print(f"✓ 设置成功")
        files = get_owner_file_list(owner, include_public=False)
        updated_file = [f for f in files if f['filename'] == filename][0]
        print(f"✓ 更新后状态: is_public={updated_file['is_public']}")
    else:
        print(f"✗ 设置失败")

    # 设置回私有
    print(f"\n3.3 设置文件为私有 (is_public=0)")
    success = set_file_public(owner, filename, 0)
    if success:
        print(f"✓ 设置成功")
        files = get_owner_file_list(owner, include_public=False)
        final_file = [f for f in files if f['filename'] == filename][0]
        print(f"✓ 最终状态: is_public={final_file['is_public']}")
    else:
        print(f"✗ 设置失败")


def test_cross_owner_visibility():
    """测试跨所有者的文件可见性"""
    print("\n\n=== 测试 4: 跨所有者文件可见性 ===")

    test_file_path = os.path.join(os.path.dirname(__file__), "居住证办理.pdf")

    # 用户1上传公开和私有文件
    owner1 = "david"
    print(f"\n4.1 {owner1} 上传文件")
    with open(test_file_path, "rb") as f:
        upload_file(owner1, "david_private.pdf", f, bucket="kms", is_public=0)
    with open(test_file_path, "rb") as f:
        upload_file(owner1, "david_public.pdf", f, bucket="kms", is_public=1)
    print(f"  ✓ {owner1}/david_private.pdf (私有)")
    print(f"  ✓ {owner1}/david_public.pdf (公开)")

    # 用户2上传文件
    owner2 = "eve"
    print(f"\n4.2 {owner2} 上传文件")
    with open(test_file_path, "rb") as f:
        upload_file(owner2, "eve_private.pdf", f, bucket="kms", is_public=0)
    print(f"  ✓ {owner2}/eve_private.pdf (私有)")

    # 用户2查看自己的文件（不包含公开）
    print(f"\n4.3 {owner2} 查看自己的文件（include_public=False）")
    eve_files = get_owner_file_list(owner2, include_public=False)
    print(f"✓ {owner2} 看到 {len(eve_files)} 个文件:")
    for f in eve_files:
        print(f"  - {f['owner']}/{f['filename']}")

    # 用户2查看自己的文件 + 公开文件
    print(f"\n4.4 {owner2} 查看自己的文件 + 公开文件（include_public=True）")
    eve_files_with_public = get_owner_file_list(owner2, include_public=True)
    print(f"✓ {owner2} 看到 {len(eve_files_with_public)} 个文件:")
    for f in eve_files_with_public:
        public_str = "公开" if f['is_public'] == 1 else "私有"
        print(f"  - {f['owner']}/{f['filename']} ({public_str})")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("文件存储仓库数据库集成测试")
    print("=" * 60)

    try:
        test_upload_with_metadata()
        test_get_owner_files()
        test_set_file_public()
        test_cross_owner_visibility()

        print("\n\n" + "=" * 60)
        print("✓ 所有测试完成")
        print("=" * 60)
    except Exception as e:
        print(f"\n\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
