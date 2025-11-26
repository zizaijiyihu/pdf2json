# HR API 接口返回值说明文档

本文档详细说明了HR系统的各个API接口及其返回值格式。

## 1. 考勤信息接口

### 接口地址
```
GET http://10.69.87.93:8001/api/hr/attendance/{email_prefix}
```

### 请求参数
| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| email_prefix | string | 是 | 员工邮箱前缀 |

### 返回值格式
```json
{
  "success": true,
  "data": [
    {
      "earlylong": 0,
      "instatus": "旷工",
      "userno": "00063801",
      "actualouttime": "",
      "endtime": "19:00:00",
      "delaylong": 0,
      "starttime": "10:00:00",
      "startdate": "2025-07-15",
      "actualoutdate": "2025-07-15",
      "zonename": "金山云正常班",
      "userid": "huxiaoxiao",
      "deptname": "新技术预研组",
      "enddate": "2025-07-15",
      "actualstartdate": "2025-07-15",
      "outstatus": "旷工",
      "actualstarttime": "",
      "username": "胡晓晓"
    }
  ]
}
```

### 字段说明
| 字段名 | 类型 | 说明 |
|-------|------|------|
| earlylong | integer | 早退时长（分钟） |
| instatus | string | 上班打卡状态（正常上班、旷工等） |
| userno | string | 员工工号 |
| actualouttime | string | 实际下班时间 |
| endtime | string | 规定下班时间 |
| delaylong | integer | 迟到时长（分钟） |
| starttime | string | 规定上班时间 |
| startdate | string | 考勤日期 |
| actualoutdate | string | 实际下班日期 |
| zonename | string | 考勤时段名称 |
| userid | string | 用户ID（邮箱前缀） |
| deptname | string | 部门名称 |
| enddate | string | 考勤结束日期 |
| actualstartdate | string | 实际上班日期 |
| outstatus | string | 下班打卡状态 |
| actualstarttime | string | 实际上班时间 |
| username | string | 用户姓名 |

## 2. 请假信息接口

### 接口地址
```
GET http://10.69.87.93:8001/api/hr/leave/{email_prefix}
```

### 请求参数
| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| email_prefix | string | 是 | 员工邮箱前缀 |

### 返回值格式
```json
{
  "success": true,
  "data": []
}
```

### 字段说明
返回一个请假记录数组，每条记录包含请假详情。对于[huxiaoxiao](file:///Users/xiaohu/projects/km-agent_2/ks_infrastructure/configs/default.py#L51-L54)用户，当前没有请假记录。

## 3. 年假信息接口

### 接口地址
```
GET http://10.69.87.93:8001/api/hr/annual-leave/{email_prefix}
```

### 请求参数
| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| email_prefix | string | 是 | 员工邮箱前缀 |

### 返回值格式
```json
{
  "success": true,
  "data": {
    "balance": 0,
    "quota": 0,
    "userid": "huxiaoxiao"
  }
}
```

### 字段说明
| 字段名 | 类型 | 说明 |
|-------|------|------|
| balance | integer | 年假余额（天） |
| quota | integer | 年假配额（天） |
| userid | string | 用户ID（邮箱前缀） |

## 4. 部门信息接口

### 接口地址
```
GET http://10.69.87.93:8001/api/hr/departments/{email_prefix}
```

### 请求参数
| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| email_prefix | string | 是 | 员工邮箱前缀 |

### 返回值格式
```json
{
  "success": false,
  "message": "无部门权限",
  "data": []
}
```

### 字段说明
此接口返回错误，表示当前用户没有查询部门信息的权限。

## 5. 下属信息接口

### 接口地址
```
GET http://10.69.87.93:8001/api/hr/subordinates/{email_prefix}
```

### 请求参数
| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| email_prefix | string | 是 | 员工邮箱前缀 |

### 返回值格式
```json
{
  "success": false,
  "message": "不是json格式",
  "data": []
}
```

### 字段说明
此接口返回错误，表明接口返回的数据不是有效的JSON格式。

## 6. 部门员工信息接口

### 接口地址
```
GET http://10.69.87.93:8001/api/hr/users/dept/{dept_id}
```

### 请求参数
| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| dept_id | string | 是 | 部门ID |

### 返回值格式
由于前面的部门信息接口调用失败，未能获取到有效的部门ID，因此未测试此接口。

## 通用返回格式说明

所有接口都采用统一的成功/失败标识格式：

### 成功响应
```json
{
  "success": true,
  "data": {...}
}
```

### 失败响应
```json
{
  "success": false,
  "message": "错误信息"
}
```

## 错误处理

接口可能返回以下HTTP状态码：

| 状态码 | 说明 |
|-------|------|
| 200 | 请求成功 |
| 401 | 未授权，检查Authorization头 |
| 404 | 资源未找到 |
| 500 | 服务器内部错误 |

## 使用示例

### Curl命令示例
```bash
curl -X GET "http://10.69.87.93:8001/api/hr/attendance/huxiaoxiao" \
-H "Authorization: demo-api-token-please-change-this"
```

### Python请求示例
```python
import requests

headers = {
    "Authorization": "demo-api-token-please-change-this"
}

response = requests.get(
    "http://10.69.87.93:8001/api/hr/attendance/huxiaoxiao",
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    if data.get("success"):
        # 处理成功响应
        print(data["data"])
    else:
        # 处理业务逻辑错误
        print(data.get("message"))
else:
    # 处理HTTP错误
    print(f"请求失败: {response.status_code}")
```