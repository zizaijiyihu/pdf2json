#!/usr/bin/env python3
"""
测试使用 ks_infrastructure 的 PDF 转换功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from pdf_to_json import PDFToJSONConverter

def test_basic_conversion():
    """测试基本转换（不启用AI）"""
    print("=" * 60)
    print("测试1: 基本PDF转换（仅文本）")
    print("=" * 60)
    
    converter = PDFToJSONConverter()
    pdf_path = os.path.join(os.path.dirname(__file__), '居住证办理.pdf')
    
    result = converter.convert(pdf_path, analyze_images=False, verbose=True)
    print(f"\n✓ 转换成功！总页数: {result['total_pages']}")
    print(f"✓ 第1页段落数: {len(result['pages'][0]['paragraphs'])}")
    return True

def test_ai_conversion():
    """测试AI图像分析转换"""
    print("\n" + "=" * 60)
    print("测试2: PDF转换 + AI图像分析")
    print("=" * 60)
    
    converter = PDFToJSONConverter()
    pdf_path = os.path.join(os.path.dirname(__file__), '居住证办理.pdf')
    
    result = converter.convert(pdf_path, analyze_images=True, verbose=True)
    print(f"\n✓ 转换成功！总页数: {result['total_pages']}")
    
    # 检查是否有AI分析的内容
    has_ai_content = False
    for page in result['pages']:
        for para in page['paragraphs']:
            if '【此处为原图片解析信息】' in para:
                has_ai_content = True
                break
    
    if has_ai_content:
        print("✓ 检测到AI图像分析内容")
    else:
        print("⚠ 未检测到AI图像分析内容（可能此PDF无图片）")
    
    return True

def test_file_output():
    """测试文件输出"""
    print("\n" + "=" * 60)
    print("测试3: 输出到JSON文件")
    print("=" * 60)
    
    converter = PDFToJSONConverter()
    pdf_path = os.path.join(os.path.dirname(__file__), '居住证办理.pdf')
    output_path = os.path.join(os.path.dirname(__file__), 'output_test.json')
    
    converter.convert_to_file(
        pdf_path,
        output_path,
        analyze_images=False,
        verbose=True
    )
    
    # 验证文件是否创建
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        print(f"\n✓ 文件创建成功: {output_path}")
        print(f"✓ 文件大小: {file_size} bytes")
        
        # 清理测试文件
        os.remove(output_path)
        print("✓ 清理测试文件")
        return True
    else:
        print("✗ 文件创建失败")
        return False

if __name__ == "__main__":
    print("\n开始测试 pdf_to_json 模块（使用 ks_infrastructure）\n")
    
    results = []
    results.append(("基本转换", test_basic_conversion()))
    results.append(("AI图像分析", test_ai_conversion()))
    results.append(("文件输出", test_file_output()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name:>12}: {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print("-" * 60)
    print(f"总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        sys.exit(0)
    else:
        print(f"\n⚠ {total - passed} 项测试失败")
        sys.exit(1)
