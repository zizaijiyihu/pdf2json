#!/usr/bin/env python3
"""
最简单的测试脚本 - 带图片解析
"""

import sys
import os

# 添加项目根目录到 python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

from pdf_to_json import PDFToJSONConverter

if len(sys.argv) < 2:
    print("用法: python simple_test.py <pdf文件路径>")
    sys.exit(1)

pdf_path = sys.argv[1]

# 创建转换器并启用AI图片分析
converter = PDFToJSONConverter()
result = converter.convert(pdf_path, analyze_images=True, verbose=True)

# 打印结果
import json
print("\n" + "="*60)
print("转换结果:")
print("="*60)
print(json.dumps(result, ensure_ascii=False, indent=2))
