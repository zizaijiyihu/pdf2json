import requests
import json

def get_access_token():
    """
    获取北森系统access_token
    """
    url = "http://10.69.80.179:8888/token"
    
    payload = {
        "grant_type": "client_credentials",
        "app_key": "DDE762E6C9F141F0B9F2432F063171B6",
        "app_secret": "B6F8BA8D587D4893AFF9EDE75B3A3EC50454F849BE8D4265A6575C10CFDB4FF3"
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        if response.status_code == 200:
            result = response.json()
            return result.get('access_token')
        else:
            print(f"获取access_token失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
    except Exception as e:
        print(f"获取access_token时发生异常: {str(e)}")
        return None

def get_course_list(access_token, page_index=1, page_size=10):
    """
    获取课程列表
    
    Args:
        access_token (str): 访问令牌
        page_index (int): 页码，必须从1开始
        page_size (int): 页容量，默认为10条，最大300条
    
    Returns:
        dict: 课程列表数据
    """
    url = "http://10.69.80.179:8888/Learning/api/v1/course/GetCourseList"
    
    payload = {
        "pageIndex": page_index,
        "pageSize": page_size
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            print(f"获取课程列表失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
    except Exception as e:
        print(f"获取课程列表时发生异常: {str(e)}")
        return None

def main():
    """主函数"""
    # 先获取access_token
    print("正在获取access_token...")
    access_token = get_access_token()
    
    if not access_token:
        print("获取access_token失败，无法继续获取课程列表")
        return
    
    print(f"获取access_token成功: {access_token[:20]}...")
    
    # 获取课程列表
    print("正在获取课程列表...")
    course_list = get_course_list(access_token, page_index=1, page_size=10)
    
    if course_list:
        print("课程标题列表:")
        # 只输出课程标题
        items = course_list.get('data', {}).get('items', [])
        for i, item in enumerate(items, 1):
            title = item.get('title', '未知标题')
            print(f"{i}. {title}")
    else:
        print("获取课程列表失败")

if __name__ == "__main__":
    main()