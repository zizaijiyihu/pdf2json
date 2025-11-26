#!/usr/bin/env python3
"""
测试上传接口的 owner 参数
"""
import requests
import json
import os

API_BASE_URL = 'http://localhost:5000'
TEST_PDF = '/Users/xiaohu/projects/km-agent_2/app_api/test/居住证办理.pdf'

if not os.path.exists(TEST_PDF):
    print(f"测试文件不存在: {TEST_PDF}")
    exit(1)

print("开始上传测试...")
print(f"文件: {TEST_PDF}")
print(f"API: {API_BASE_URL}/api/upload")
print("=" * 60)

with open(TEST_PDF, 'rb') as f:
    files = {'file': (os.path.basename(TEST_PDF), f, 'application/pdf')}
    data = {'is_public': '0'}

    response = requests.post(
        f"{API_BASE_URL}/api/upload",
        files=files,
        data=data,
        stream=True,
        timeout=300
    )

print(f"响应状态码: {response.status_code}")

for line in response.iter_lines():
    if line:
        line_str = line.decode('utf-8')
        if line_str.startswith('data: '):
            try:
                event_data = json.loads(line_str[6:])
                stage = event_data.get('stage')
                progress = event_data.get('progress_percent', 0)
                message = event_data.get('message', '')

                print(f"[{stage}] {progress}% - {message}")

                if stage == 'completed':
                    print("\n完成! 最终数据:")
                    print(json.dumps(event_data.get('data', {}), indent=2, ensure_ascii=False))
                    break
                elif stage == 'error':
                    print(f"\n错误: {event_data.get('error')}")
                    break
            except json.JSONDecodeError as e:
                print(f"解析错误: {e}")
