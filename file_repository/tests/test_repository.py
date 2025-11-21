"""
文件存储仓库功能测试
"""

import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from file_repository import upload_file, get_file, list_user_files


def test_upload_and_get():
    """测试上传和获取文件"""
    print("\n=== 测试 1: 上传和获取文件 ===")

    # 测试文件路径
    test_file_path = os.path.join(os.path.dirname(__file__), "居住证办理.pdf")

    # 测试用户
    username = "testuser"
    filename = "居住证办理.pdf"

    # 测试 kms bucket
    print(f"\n1.1 上传文件到 kms bucket: {username}/{filename}")
    with open(test_file_path, "rb") as f:
        result = upload_file(username, filename, f, bucket="kms", content_type="application/pdf")
    print(f"✓ 上传成功: {result}")

    # 获取文件
    print(f"\n1.2 从 kms bucket 获取文件: {username}/{filename}")
    content = get_file(username, filename, bucket="kms")
    if content:
        print(f"✓ 获取成功, 文件大小: {len(content)} bytes")

        # 验证内容一致性
        with open(test_file_path, "rb") as f:
            original_content = f.read()
        if content == original_content:
            print("✓ 文件内容验证通过")
        else:
            print("✗ 文件内容不一致")
    else:
        print("✗ 获取失败")

    # 测试 tmp bucket
    print(f"\n1.3 上传文件到 tmp bucket: {username}/{filename}")
    with open(test_file_path, "rb") as f:
        result = upload_file(username, filename, f, bucket="tmp", content_type="application/pdf")
    print(f"✓ 上传成功: {result}")

    # 从 tmp bucket 获取
    print(f"\n1.4 从 tmp bucket 获取文件: {username}/{filename}")
    content = get_file(username, filename, bucket="tmp")
    if content:
        print(f"✓ 获取成功, 文件大小: {len(content)} bytes")
    else:
        print("✗ 获取失败")


def test_overwrite():
    """测试文件覆盖"""
    print("\n\n=== 测试 2: 重复上传覆盖 ===")

    test_file_path = os.path.join(os.path.dirname(__file__), "居住证办理.pdf")
    username = "testuser"
    filename = "test_overwrite.pdf"

    # 第一次上传
    print(f"\n2.1 第一次上传: {username}/{filename}")
    with open(test_file_path, "rb") as f:
        result1 = upload_file(username, filename, f, bucket="kms")
    print(f"✓ 上传成功: {result1}")

    # 第二次上传（覆盖）
    print(f"\n2.2 第二次上传（覆盖）: {username}/{filename}")
    with open(test_file_path, "rb") as f:
        result2 = upload_file(username, filename, f, bucket="kms")
    print(f"✓ 覆盖成功: {result2}")

    # 验证文件仍然可以获取
    content = get_file(username, filename, bucket="kms")
    if content:
        print(f"✓ 覆盖后文件可正常获取, 大小: {len(content)} bytes")
    else:
        print("✗ 覆盖后文件获取失败")


def test_list_files():
    """测试列出用户文件"""
    print("\n\n=== 测试 3: 列出用户文件 ===")

    test_file_path = os.path.join(os.path.dirname(__file__), "居住证办理.pdf")
    username = "listtest"

    # 上传多个文件
    print(f"\n3.1 上传多个文件到 kms bucket")
    files_to_upload = ["file1.pdf", "file2.pdf", "file3.pdf"]
    for fname in files_to_upload:
        with open(test_file_path, "rb") as f:
            upload_file(username, fname, f, bucket="kms")
        print(f"  ✓ 上传: {username}/{fname}")

    # 列出文件
    print(f"\n3.2 列出用户 {username} 的所有文件")
    files = list_user_files(username, bucket="kms")
    print(f"✓ 找到 {len(files)} 个文件:")
    for file_info in files:
        print(f"  - {file_info['filename']} ({file_info['size']} bytes, {file_info['last_modified']})")

    # 测试 tmp bucket
    print(f"\n3.3 上传文件到 tmp bucket")
    with open(test_file_path, "rb") as f:
        upload_file(username, "tmp_file.pdf", f, bucket="tmp")
    print(f"  ✓ 上传: {username}/tmp_file.pdf")

    print(f"\n3.4 列出 tmp bucket 中用户的文件")
    tmp_files = list_user_files(username, bucket="tmp")
    print(f"✓ 找到 {len(tmp_files)} 个文件:")
    for file_info in tmp_files:
        print(f"  - {file_info['filename']} ({file_info['size']} bytes)")


def test_get_nonexistent():
    """测试获取不存在的文件"""
    print("\n\n=== 测试 4: 获取不存在的文件 ===")

    username = "testuser"
    filename = "nonexistent.pdf"

    print(f"\n4.1 尝试获取不存在的文件: {username}/{filename}")
    content = get_file(username, filename, bucket="kms")
    if content is None:
        print("✓ 正确返回 None")
    else:
        print(f"✗ 应该返回 None，但返回了内容: {len(content)} bytes")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("文件存储仓库功能测试")
    print("=" * 60)

    try:
        test_upload_and_get()
        test_overwrite()
        test_list_files()
        test_get_nonexistent()

        print("\n\n" + "=" * 60)
        print("✓ 所有测试完成")
        print("=" * 60)
    except Exception as e:
        print(f"\n\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
