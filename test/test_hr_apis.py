#!/usr/bin/env python3
"""
HR APIs 测试脚本

测试以下HR相关接口:
1. 考勤信息接口: http://10.69.87.93:8001/api/hr/attendance/{email_prefix}
2. 请假信息接口: http://10.69.87.93:8001/api/hr/leave/{email_prefix}
3. 年假信息接口: http://10.69.87.93:8001/api/hr/annual-leave/{email_prefix}
4. 部门信息接口: http://10.69.87.93:8001/api/hr/departments/{email_prefix}
5. 下属信息接口: http://10.69.87.93:8001/api/hr/subordinates/{email_prefix}
6. 部门员工信息接口: http://10.69.87.93:8001/api/hr/users/dept/{dept_id}

使用示例:
curl -X GET "http://10.69.87.93:8001/api/hr/attendance/huxiaoxiao" \
-H "Authorization: demo-api-token-please-change-this"
"""

import requests
import json
import sys
import os

# API基础配置
BASE_URL = "http://10.69.87.93:8001/api/hr"
AUTH_TOKEN = "demo-api-token-please-change-this"
HEADERS = {
    "Authorization": AUTH_TOKEN
}

# 测试邮箱前缀
TEST_EMAIL_PREFIX = "huxiaoxiao"


def test_attendance_api(email_prefix):
    """
    测试考勤信息接口
    
    Args:
        email_prefix (str): 员工邮箱前缀
        
    Returns:
        dict: 接口返回的数据
    """
    url = f"{BASE_URL}/attendance/{email_prefix}"
    print(f"测试考勤信息接口: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("返回数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
        else:
            print(f"请求失败: {response.status_code} - {response.text}")
            return {"error": f"Status code: {response.status_code}", "message": response.text}
    except Exception as e:
        print(f"请求异常: {e}")
        return {"error": str(e)}


def test_leave_api(email_prefix):
    """
    测试请假信息接口
    
    Args:
        email_prefix (str): 员工邮箱前缀
        
    Returns:
        dict: 接口返回的数据
    """
    url = f"{BASE_URL}/leave/{email_prefix}"
    print(f"测试请假信息接口: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("返回数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
        else:
            print(f"请求失败: {response.status_code} - {response.text}")
            return {"error": f"Status code: {response.status_code}", "message": response.text}
    except Exception as e:
        print(f"请求异常: {e}")
        return {"error": str(e)}


def test_annual_leave_api(email_prefix):
    """
    测试年假信息接口
    
    Args:
        email_prefix (str): 员工邮箱前缀
        
    Returns:
        dict: 接口返回的数据
    """
    url = f"{BASE_URL}/annual-leave/{email_prefix}"
    print(f"测试年假信息接口: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("返回数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
        else:
            print(f"请求失败: {response.status_code} - {response.text}")
            return {"error": f"Status code: {response.status_code}", "message": response.text}
    except Exception as e:
        print(f"请求异常: {e}")
        return {"error": str(e)}


def test_departments_api(email_prefix):
    """
    测试部门信息接口
    
    Args:
        email_prefix (str): 员工邮箱前缀
        
    Returns:
        dict: 接口返回的数据
    """
    url = f"{BASE_URL}/departments/{email_prefix}"
    print(f"测试部门信息接口: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("返回数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
        else:
            print(f"请求失败: {response.status_code} - {response.text}")
            return {"error": f"Status code: {response.status_code}", "message": response.text}
    except Exception as e:
        print(f"请求异常: {e}")
        return {"error": str(e)}


def test_subordinates_api(email_prefix):
    """
    测试下属信息接口
    
    Args:
        email_prefix (str): 员工邮箱前缀
        
    Returns:
        dict: 接口返回的数据
    """
    url = f"{BASE_URL}/subordinates/{email_prefix}"
    print(f"测试下属信息接口: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("返回数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
        else:
            print(f"请求失败: {response.status_code} - {response.text}")
            return {"error": f"Status code: {response.status_code}", "message": response.text}
    except Exception as e:
        print(f"请求异常: {e}")
        return {"error": str(e)}


def test_users_by_dept_api(dept_id):
    """
    测试根据部门ID获取用户列表接口
    
    Args:
        dept_id (str): 部门ID
        
    Returns:
        dict: 接口返回的数据
    """
    url = f"{BASE_URL}/users/dept/{dept_id}"
    print(f"测试部门用户列表接口: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("返回数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
        else:
            print(f"请求失败: {response.status_code} - {response.text}")
            return {"error": f"Status code: {response.status_code}", "message": response.text}
    except Exception as e:
        print(f"请求异常: {e}")
        return {"error": str(e)}


def main():
    """主函数，依次测试所有HR接口"""
    print("开始测试HR相关API接口")
    print("=" * 50)
    
    results = {}
    
    # 1. 测试考勤信息接口
    print("\n1. 测试考勤信息接口")
    print("-" * 30)
    results['attendance'] = test_attendance_api(TEST_EMAIL_PREFIX)
    
    # 2. 测试请假信息接口
    print("\n2. 测试请假信息接口")
    print("-" * 30)
    results['leave'] = test_leave_api(TEST_EMAIL_PREFIX)
    
    # 3. 测试年假信息接口
    print("\n3. 测试年假信息接口")
    print("-" * 30)
    results['annual_leave'] = test_annual_leave_api(TEST_EMAIL_PREFIX)
    
    # 4. 测试部门信息接口
    print("\n4. 测试部门信息接口")
    print("-" * 30)
    results['departments'] = test_departments_api(TEST_EMAIL_PREFIX)
    
    # 5. 测试下属信息接口
    print("\n5. 测试下属信息接口")
    print("-" * 30)
    results['subordinates'] = test_subordinates_api(TEST_EMAIL_PREFIX)
    
    # 6. 测试部门用户列表接口 (需要从departments接口获取部门ID)
    print("\n6. 测试部门用户列表接口")
    print("-" * 30)
    if 'departments' in results and results['departments'].get('success'):
        # 尝试从部门信息中获取第一个部门ID
        dept_data = results['departments'].get('data', [])
        if dept_data and isinstance(dept_data, list) and len(dept_data) > 0:
            first_dept = dept_data[0]
            dept_id = first_dept.get('id') or first_dept.get('deptId')
            if dept_id:
                results['users_by_dept'] = test_users_by_dept_api(dept_id)
            else:
                print("无法从部门信息中提取部门ID")
                results['users_by_dept'] = {"error": "无法提取部门ID"}
        else:
            print("部门信息为空，无法测试部门用户列表接口")
            results['users_by_dept'] = {"error": "部门信息为空"}
    else:
        print("部门信息接口调用失败，无法测试部门用户列表接口")
        results['users_by_dept'] = {"error": "部门信息接口调用失败"}
    
    # 保存结果到文件
    output_file = "hr_api_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n测试结果已保存至: {output_file}")
    
    print("\n测试完成!")


if __name__ == "__main__":
    main()