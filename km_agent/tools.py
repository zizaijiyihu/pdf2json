"""
KM Agent Tools - Tool definitions and execution handlers
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
import sys
import os

# Add project root to path to allow imports from other modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from aibase_news.news_service import get_aibase_news
from beisen_course.course_service import get_course_list


class AgentTools:
    """
    Agent tools for knowledge management and HR operations

    Handles:
    - Tool definitions for function calling
    - Tool execution logic
    """

    def __init__(self, vectorizer, user_info_service, verbose: bool = False):
        """
        Initialize agent tools

        Args:
            vectorizer: PDFVectorizer instance for knowledge base operations
            user_info_service: User info service for HR operations
            verbose: Whether to print debug information
        """
        self.vectorizer = vectorizer
        self.user_info_service = user_info_service
        self.verbose = verbose

        # Tool definitions for function calling
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_knowledge",
                    "description": "搜索知识库，返回与查询相关的知识切片。使用语义搜索找到最相关的文档页面。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索查询内容"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "返回结果数量，默认5",
                                "default": 5
                            },
                            "mode": {
                                "type": "string",
                                "enum": ["content"],
                                "description": "搜索模式：只使用content(内容)召回",
                                "default": "content"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_pages",
                    "description": "根据文件名和页码获取完整的知识内容。当需要查看完整内容或后续页面时使用。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "文档文件名"
                            },
                            "page_numbers": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "要获取的页码列表，例如 [1, 2, 3]"
                            },
                            "fields": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "要返回的字段列表，可选值：filename, page_number, content, owner。默认返回 filename, page_number, content。"
                            }
                        },
                        "required": ["filename", "page_numbers"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_subordinate_attendance",
                    "description": "获取下属的考勤记录。会自动验证当前用户是否有权限查看目标用户的考勤记录（仅限直接下属）。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target_email_prefix": {
                                "type": "string",
                                "description": "目标员工的邮箱前缀，例如 'lihaoze2'"
                            }
                        },
                        "required": ["target_email_prefix"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_manager_style",
                    "description": "获取管理者的管理风格类型。",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "description": "获取当前时间，返回格式化的时间字符串和时间戳。",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_subordinates",
                    "description": "获取指定用户的下属列表。如果不指定email_prefix，则获取当前用户的下属列表。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email_prefix": {
                                "type": "string",
                                "description": "员工的邮箱前缀，例如 'huxiaoxiao'。如果不指定，则获取当前用户的下属列表。"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_subordinate_employee_info",
                    "description": "获取下属的详细员工档案信息，包括：基本信息（姓名、工号、邮箱前缀、性别、年龄、生日）、工作信息（部门、职位、职级、工作地点）、背景信息（入职日期、工龄、学历、毕业院校、专业特长、合同到期日期）。适用场景：查询下属的个人档案、了解团队成员背景、获取员工详细资料。会自动验证当前用户是否有权限查看目标用户的信息（仅限直接下属）。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target_email_prefix": {
                                "type": "string",
                                "description": "目标员工的邮箱前缀，例如 'zhangqiushi1'"
                            }
                        },
                        "required": ["target_email_prefix"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_latest_ai_news",
                    "description": "获取最新的AI相关新闻资讯。默认返回15条。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "返回新闻数量，默认15",
                                "default": 15
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_current_user_info",
                    "description": "获取当前登录用户的详细信息，包括：基本信息（姓名、工号、邮箱前缀、性别、年龄、生日）、工作信息（部门、职位、职级、工作地点）、背景信息（入职日期、工龄、学历、毕业院校、专业特长、合同到期日期）。",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_course_list",
                    "description": "获取北森系统的课程列表，包括课程标题、课程ID、课程描述等信息。适用场景：查询可用的培训课程、浏览课程列表、了解课程信息。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "page_index": {
                                "type": "integer",
                                "description": "页码，必须从1开始，默认1",
                                "default": 1
                            },
                            "page_size": {
                                "type": "integer",
                                "description": "每页数量，默认10，最大300",
                                "default": 10
                            }
                        }
                    }
                }
            }
        ]

    def get_tool_definitions(self) -> List[Dict]:
        """
        Get tool definitions for LLM function calling

        Returns:
            List of tool definitions
        """
        return self.tools

    def _search_knowledge(self, query: str, limit: int = 5, mode: str = "content") -> Dict:
        """
        Search knowledge base

        Args:
            query: Search query
            limit: Number of results
            mode: Search mode (dual/summary/content)

        Returns:
            Search results
        """
        if self.verbose:
            print(f"\n[Tool] search_knowledge: query='{query}', limit={limit}, mode={mode}")

        results = self.vectorizer.search(query, limit=limit, mode=mode, verbose=False)

        # Format results for LLM - only return content, no summary
        formatted_results = []

        if "content_results" in results:
            for result in results["content_results"]:
                formatted_results.append({
                    "filename": result["filename"],
                    "page_number": result["page_number"],
                    "score": result["score"],
                    "content": result["content"]  # Return full content, not preview
                })

        if self.verbose:
            print(f"[Tool] Found {len(formatted_results)} results")

        return {
            "success": True,
            "total_results": len(formatted_results),
            "results": formatted_results
        }

    def _get_pages(self, filename: str, page_numbers: List[int], fields: Optional[List[str]] = None) -> Dict:
        """
        Get specific pages from knowledge base

        Args:
            filename: Document filename
            page_numbers: List of page numbers to retrieve
            fields: Optional list of fields to return (default: filename, page_number, content)

        Returns:
            Page data
        """
        # Default fields: only content-related fields, no summary
        if fields is None:
            fields = ["filename", "page_number", "content"]

        if self.verbose:
            print(f"\n[Tool] get_pages: filename='{filename}', page_numbers={page_numbers}, fields={fields}")

        pages = self.vectorizer.get_pages(
            filename=filename,
            page_numbers=page_numbers,
            fields=fields,
            verbose=False
        )

        if self.verbose:
            print(f"[Tool] Retrieved {len(pages)} pages")

        return {
            "success": True,
            "total_pages": len(pages),
            "pages": pages
        }

    def _get_subordinate_attendance(self, target_email_prefix: str, current_user_email_prefix: str) -> Dict:
        """
        Get subordinate's attendance records with permission verification

        Args:
            target_email_prefix: Target employee's email prefix
            current_user_email_prefix: Current user's email prefix for permission check

        Returns:
            Attendance records (top 10 records with filtered fields) or permission denied message
        """
        if self.verbose:
            print(f"\n[Tool] get_subordinate_attendance: target_email_prefix='{target_email_prefix}'")

        try:
            # Use the current user to check permissions
            result = self.user_info_service.get_subordinate_attendance(
                target_email_prefix=target_email_prefix,
                current_user_email_prefix=current_user_email_prefix
            )

            if self.verbose:
                if result.get('success'):
                    attendance_count = len(result.get('data', []))
                    print(f"[Tool] Retrieved {attendance_count} attendance records")
                else:
                    print(f"[Tool] Permission denied: {result.get('message')}")

            # Filter and format the result if successful
            if result.get('success'):
                all_records = result.get('data', [])

                # Define fields to keep
                fields_to_keep = [
                    'actualstartdate',  # 实际上班日期
                    'actualstarttime',  # 实际上班时间
                    'delaylong',        # 迟到时长(分钟)
                    'actualouttime',    # 实际下班时间
                    'earlylong',        # 早退时长(分钟)
                    'zonename'          # 考勤区域
                ]

                # Take first 10 records and filter fields
                filtered_records = [
                    {field: record.get(field) for field in fields_to_keep}
                    for record in all_records[:10]
                ]

                if self.verbose:
                    print(f"[Tool] Filtered to {len(filtered_records)} records with {len(fields_to_keep)} fields")

                return {
                    "success": True,
                    "data": filtered_records,
                    "total_records": len(all_records),
                    "returned_records": len(filtered_records)
                }

            return result

        except Exception as e:
            if self.verbose:
                print(f"[Tool] Error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _get_manager_style(self) -> Dict:
        """
        Get manager's management style

        Returns:
            Manager style information
        """
        if self.verbose:
            print(f"\n[Tool] get_manager_style")

        # Default return value - will be replaced with real data interface later
        return {
            "success": True,
            "style": "黄牛型,大部分工作都自己亲力亲为"
        }

    def _get_current_time(self) -> Dict:
        """
        Get current time with formatted string and timestamp

        Returns:
            Current time information including:
            - formatted_time: Time string in format "x年x月x日 x时x分x秒"
            - timestamp: Unix timestamp
        """
        if self.verbose:
            print(f"\n[Tool] get_current_time")

        now = datetime.now()
        formatted_time = now.strftime("%Y年%m月%d日 %H时%M分%S秒")
        timestamp = int(time.time())

        if self.verbose:
            print(f"[Tool] Current time: {formatted_time}, timestamp: {timestamp}")

        return {
            "success": True,
            "formatted_time": formatted_time,
            "timestamp": timestamp
        }

    def _get_subordinates(self, email_prefix: Optional[str] = None, current_user_email_prefix: str = None) -> Dict:
        """
        Get subordinates list for a user

        Args:
            email_prefix: Employee's email prefix. If None, use current_user_email_prefix
            current_user_email_prefix: Current user's email prefix (fallback if email_prefix is None)

        Returns:
            Subordinates list or error message
        """
        # If email_prefix is not provided, use current user
        target_email_prefix = email_prefix if email_prefix else current_user_email_prefix

        if self.verbose:
            print(f"\n[Tool] get_subordinates: email_prefix='{target_email_prefix}'")

        try:
            result = self.user_info_service.get_subordinates(target_email_prefix)

            if self.verbose:
                if result.get('success'):
                    subordinates_count = len(result.get('data', []))
                    print(f"[Tool] Retrieved {subordinates_count} subordinates")
                else:
                    print(f"[Tool] Failed: {result}")

            return result

        except Exception as e:
            if self.verbose:
                print(f"[Tool] Error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _get_subordinate_employee_info(self, target_email_prefix: str, current_user_email_prefix: str) -> Dict:
        """
        Get subordinate's employee information with permission verification

        Args:
            target_email_prefix: Target employee's email prefix
            current_user_email_prefix: Current user's email prefix for permission check

        Returns:
            Employee information or permission denied message
        """
        if self.verbose:
            print(f"\n[Tool] get_subordinate_employee_info: target_email_prefix='{target_email_prefix}'")

        try:
            # Use the current user to check permissions
            result = self.user_info_service.get_subordinate_employee_info(
                target_email_prefix=target_email_prefix,
                current_user_email_prefix=current_user_email_prefix
            )

            if self.verbose:
                if result.get('success'):
                    print(f"[Tool] Successfully retrieved employee info")
                else:
                    print(f"[Tool] Permission denied: {result.get('message')}")

            return result

        except Exception as e:
            if self.verbose:
                print(f"[Tool] Error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _get_current_user_info(self, current_user_email_prefix: str) -> Dict:
        """
        Get current user's employee information
        
        Args:
            current_user_email_prefix: Current user's email prefix
            
        Returns:
            Employee information or error message
        """
        if self.verbose:
            print(f"\n[Tool] get_current_user_info: current_user_email_prefix='{current_user_email_prefix}'")
            
        try:
            result = self.user_info_service.get_current_user_info(
                current_user_email_prefix=current_user_email_prefix
            )
            
            if self.verbose:
                if result.get('success'):
                    print(f"[Tool] Successfully retrieved current user info")
                else:
                    print(f"[Tool] Failed: {result}")
                    
            return result
            
        except Exception as e:
            if self.verbose:
                print(f"[Tool] Error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _get_latest_ai_news(self, limit: int = 15) -> Dict:
        """
        Get latest AI news

        Args:
            limit: Number of news items to return

        Returns:
            List of news items
        """
        if self.verbose:
            print(f"\n[Tool] get_latest_ai_news: limit={limit}")

        try:
            # Call get_aibase_news. It returns a list. We slice it.
            # We'll use default pages=2 to get enough news, then slice.
            news_list = get_aibase_news(pages=2)

            if not news_list:
                return {
                    "success": True,
                    "data": [],
                    "message": "No news found"
                }

            # Slice to limit
            returned_news = news_list[:limit]

            if self.verbose:
                print(f"[Tool] Retrieved {len(returned_news)} news items")

            return {
                "success": True,
                "data": returned_news,
                "total": len(returned_news)
            }

        except Exception as e:
            if self.verbose:
                print(f"[Tool] Error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _get_course_list(self, page_index: int = 1, page_size: int = 10) -> Dict:
        """
        Get course list from Beisen system

        Args:
            page_index: Page number, starting from 1
            page_size: Page size, default 10, max 300

        Returns:
            Course list with details
        """
        if self.verbose:
            print(f"\n[Tool] get_course_list: page_index={page_index}, page_size={page_size}")

        try:
            result = get_course_list(page_index=page_index, page_size=page_size)

            if self.verbose:
                if result.get('success'):
                    course_count = len(result.get('data', []))
                    total = result.get('total', 0)
                    print(f"[Tool] Retrieved {course_count} courses (total: {total})")
                else:
                    print(f"[Tool] Failed: {result.get('error')}")

            return result

        except Exception as e:
            if self.verbose:
                print(f"[Tool] Error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def execute_tool(self, tool_name: str, tool_args: Dict[str, Any], current_user: str = None) -> str:
        """
        Execute a tool function

        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments for the tool
            current_user: Current user email prefix (required for permission-based tools)

        Returns:
            JSON string of tool result
        """
        try:
            if tool_name == "search_knowledge":
                result = self._search_knowledge(**tool_args)
            elif tool_name == "get_pages":
                result = self._get_pages(**tool_args)
            elif tool_name == "get_subordinate_attendance":
                if current_user is None:
                    result = {"success": False, "error": "current_user is required for this tool"}
                else:
                    result = self._get_subordinate_attendance(
                        current_user_email_prefix=current_user,
                        **tool_args
                    )
            elif tool_name == "get_manager_style":
                result = self._get_manager_style()
            elif tool_name == "get_current_time":
                result = self._get_current_time()
            elif tool_name == "get_subordinates":
                if current_user is None:
                    result = {"success": False, "error": "current_user is required for this tool"}
                else:
                    result = self._get_subordinates(
                        current_user_email_prefix=current_user,
                        **tool_args
                    )
            elif tool_name == "get_subordinate_employee_info":
                if current_user is None:
                    result = {"success": False, "error": "current_user is required for this tool"}
                else:
                    result = self._get_subordinate_employee_info(
                        current_user_email_prefix=current_user,
                        **tool_args
                    )
            elif tool_name == "get_current_user_info":
                if current_user is None:
                    result = {"success": False, "error": "current_user is required for this tool"}
                else:
                    result = self._get_current_user_info(
                        current_user_email_prefix=current_user
                    )
            elif tool_name == "get_latest_ai_news":
                result = self._get_latest_ai_news(**tool_args)
            elif tool_name == "get_course_list":
                result = self._get_course_list(**tool_args)
            else:
                result = {"success": False, "error": f"Unknown tool: {tool_name}"}

            return json.dumps(result, ensure_ascii=False)

        except Exception as e:
            error_result = {"success": False, "error": str(e)}
            return json.dumps(error_result, ensure_ascii=False)
