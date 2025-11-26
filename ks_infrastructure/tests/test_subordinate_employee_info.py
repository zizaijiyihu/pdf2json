#!/usr/bin/env python3
"""
测试获取下属员工信息功能（带权限验证）

该脚本测试 get_subordinate_employee_info 方法
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def test_get_subordinate_employee_info():
    """测试获取下属员工信息功能"""
    print("=== 测试获取下属员工信息功能 ===")
    try:
        from ks_infrastructure import ks_user_info

        # 获取用户信息服务
        user_info_service = ks_user_info()
        print("✓ 成功初始化用户信息服务")

        # 测试目标：zhangqiushi1
        target_email_prefix = "zhangqiushi1"
        # 当前用户会从 get_current_user() 获取，默认是 huxiaoxiao
        
        print(f"\n测试获取下属员工信息: {target_email_prefix}")
        print("当前用户: huxiaoxiao (从 get_current_user() 获取)")

        # 调用新方法
        result = user_info_service.get_subordinate_employee_info(target_email_prefix)

        if result.get('success'):
            data = result.get('data', {})
            print("\n✓ 成功获取下属员工信息:")
            print(f"  用户ID: {data.get('userId')}")
            print(f"  用户名: {data.get('userName')}")
            print(f"  工号: {data.get('userNo')}")
            print(f"  部门: {data.get('deptName')}")
            print(f"  完整部门路径: {data.get('deptFullName')}")
            print(f"  职位: {data.get('positionName')}")
            print(f"  职级: {data.get('rank')}")
            print(f"  地点: {data.get('location')}")
            print(f"  性别: {data.get('sex')}")
            print(f"  年龄: {data.get('age')}")
            print(f"  生日: {data.get('birthday')}")
            print(f"  学历: {data.get('education')}")
            print(f"  毕业院校: {data.get('graduationInstitution')}")
            print(f"  专业: {data.get('speciality')}")
            print(f"  入职日期: {data.get('joinedDate')}")
            print(f"  工龄: {data.get('workAge')}年")
            print(f"  合同到期: {data.get('contractExpire')}")
            return True
        else:
            message = result.get('message', '未知错误')
            print(f"\n✗ 获取员工信息失败: {message}")
            return False

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_unauthorized_access():
    """测试无权限访问（访问非下属员工）"""
    print("\n=== 测试无权限访问 ===")
    try:
        from ks_infrastructure import ks_user_info

        # 获取用户信息服务
        user_info_service = ks_user_info()

        # 测试访问一个不是下属的用户
        # 假设 lihaoze2 不是 huxiaoxiao 的下属
        target_email_prefix = "lihaoze2"
        
        print(f"测试访问非下属员工信息: {target_email_prefix}")
        print("当前用户: huxiaoxiao")

        result = user_info_service.get_subordinate_employee_info(target_email_prefix)

        if not result.get('success'):
            message = result.get('message', '')
            print(f"✓ 正确拒绝了无权限访问: {message}")
            return True
        else:
            print("✗ 预期应该拒绝访问，但返回了成功")
            return False

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_explicit_current_user():
    """测试显式指定当前用户"""
    print("\n=== 测试显式指定当前用户 ===")
    try:
        from ks_infrastructure import ks_user_info

        # 获取用户信息服务
        user_info_service = ks_user_info()

        # 显式指定当前用户
        current_user = "huxiaoxiao"
        target_email_prefix = "zhangqiushi1"
        
        print(f"测试显式指定当前用户: {current_user}")
        print(f"查询目标: {target_email_prefix}")

        result = user_info_service.get_subordinate_employee_info(
            target_email_prefix=target_email_prefix,
            current_user_email_prefix=current_user
        )

        if result.get('success'):
            data = result.get('data', {})
            print(f"✓ 成功获取员工信息: {data.get('userName')} ({data.get('userId')})")
            return True
        else:
            message = result.get('message', '未知错误')
            print(f"✗ 获取员工信息失败: {message}")
            return False

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("开始测试获取下属员工信息功能...")
    print("=" * 60)

    test_results = {}

    # 测试正常获取下属员工信息
    test_results['获取下属员工信息'] = test_get_subordinate_employee_info()

    # 测试无权限访问
    test_results['无权限访问拒绝'] = test_unauthorized_access()

    # 测试显式指定当前用户
    test_results['显式指定当前用户'] = test_explicit_current_user()

    # 输出测试总结
    print("\n" + "=" * 60)
    print("测试结果总结:")
    print("=" * 60)

    passed_tests = 0
    total_tests = len(test_results)

    for test_name, result in test_results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name:>20}: {status}")
        if result:
            passed_tests += 1

    print("-" * 60)
    print(f"总计: {passed_tests}/{total_tests} 项测试通过")

    if passed_tests == total_tests:
        print("\n🎉 所有测试均通过!")
        return 0
    else:
        print(f"\n⚠ {total_tests - passed_tests} 项测试失败，请检查相关配置。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
