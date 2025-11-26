#!/usr/bin/env python3
"""
测试考勤服务功能

该脚本测试ks_infrastructure模块中的考勤相关服务
"""

import os
import sys
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def test_get_subordinates():
    """测试获取下属列表功能"""
    print("=== 测试获取下属列表功能 ===")
    try:
        from ks_infrastructure import ks_user_info
        from ks_infrastructure.services.user_info_service import get_current_user

        # 获取用户信息服务
        user_info_service = ks_user_info()
        print("✓ 成功初始化用户信息服务")

        # 获取当前用户
        current_user = get_current_user()
        print(f"\n当前用户: {current_user}")

        # 测试获取下属列表
        print(f"测试获取用户 {current_user} 的下属列表")
        result = user_info_service.get_subordinates(current_user)

        if result.get('success'):
            subordinates = result.get('data', [])
            print(f"✓ 成功获取下属列表，共 {len(subordinates)} 人:")

            for idx, subordinate in enumerate(subordinates, 1):
                print(f"\n  下属 {idx}:")
                print(f"    用户ID: {subordinate.get('userId')}")
                print(f"    用户名: {subordinate.get('userName')}")
                print(f"    工号: {subordinate.get('userNo')}")
                print(f"    部门: {subordinate.get('deptName')}")
                print(f"    职位: {subordinate.get('positionName')}")

            return True, subordinates
        else:
            print("✗ 获取下属列表失败")
            return False, []

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, []


def test_get_attendance():
    """测试获取考勤记录功能"""
    print("\n=== 测试获取考勤记录功能 ===")
    try:
        from ks_infrastructure import ks_user_info

        # 获取用户信息服务
        user_info_service = ks_user_info()

        # 测试邮箱前缀（可以根据实际情况修改）
        test_email_prefix = "lihaoze2"
        print(f"测试获取用户 {test_email_prefix} 的考勤记录")

        result = user_info_service.get_attendance(test_email_prefix)

        if result.get('success'):
            attendance_records = result.get('data', [])
            print(f"✓ 成功获取考勤记录，共 {len(attendance_records)} 条:")

            # 显示前5条记录
            for idx, record in enumerate(attendance_records[:5], 1):
                print(f"\n  记录 {idx}:")
                print(f"    日期: {record.get('date')}")
                print(f"    状态: {record.get('status')}")
                print(f"    签到: {record.get('checkIn')}")
                print(f"    签退: {record.get('checkOut')}")

            if len(attendance_records) > 5:
                print(f"\n  ... 还有 {len(attendance_records) - 5} 条记录")

            return True
        else:
            print("✗ 获取考勤记录失败")
            return False

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_subordinate_attendance_with_permission():
    """测试获取下属考勤记录（有权限）"""
    print("\n=== 测试获取下属考勤记录（有权限） ===")
    try:
        from ks_infrastructure import ks_user_info
        from ks_infrastructure.services.user_info_service import get_current_user

        # 获取用户信息服务
        user_info_service = ks_user_info()

        # 获取当前用户
        current_user = get_current_user()
        print(f"当前用户: {current_user}")

        # 先获取下属列表
        subordinates_result = user_info_service.get_subordinates(current_user)

        if not subordinates_result.get('success'):
            print("✗ 无法获取下属列表，跳过测试")
            return None

        subordinates = subordinates_result.get('data', [])

        if not subordinates:
            print("⚠ 当前用户没有下属，无法测试有权限场景")
            return None

        # 选择第一个下属进行测试
        target_subordinate = subordinates[0]
        target_email_prefix = target_subordinate.get('userId')
        target_name = target_subordinate.get('userName')

        print(f"测试获取下属 {target_name} ({target_email_prefix}) 的考勤记录")

        result = user_info_service.get_subordinate_attendance(
            target_email_prefix=target_email_prefix,
            current_user_email_prefix=current_user
        )

        if result.get('success'):
            attendance_records = result.get('data', [])
            print(f"✓ 成功获取下属考勤记录，共 {len(attendance_records)} 条")

            # 显示前3条记录
            for idx, record in enumerate(attendance_records[:3], 1):
                print(f"\n  记录 {idx}:")
                print(f"    日期: {record.get('date')}")
                print(f"    状态: {record.get('status')}")

            if len(attendance_records) > 3:
                print(f"\n  ... 还有 {len(attendance_records) - 3} 条记录")

            return True
        else:
            message = result.get('message', '未知错误')
            print(f"✗ 获取下属考勤记录失败: {message}")
            return False

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_subordinate_attendance_without_permission():
    """测试获取非下属考勤记录（无权限）"""
    print("\n=== 测试获取非下属考勤记录（无权限） ===")
    try:
        from ks_infrastructure import ks_user_info
        from ks_infrastructure.services.user_info_service import get_current_user

        # 获取用户信息服务
        user_info_service = ks_user_info()

        # 获取当前用户
        current_user = get_current_user()
        print(f"当前用户: {current_user}")

        # 先获取下属列表
        subordinates_result = user_info_service.get_subordinates(current_user)
        subordinates = subordinates_result.get('data', []) if subordinates_result.get('success') else []
        subordinate_ids = [sub.get('userId') for sub in subordinates]

        # 使用当前用户自己作为测试目标（自己肯定不在自己的下属列表中）
        non_subordinate_email_prefix = current_user

        print(f"当前用户的下属列表: {subordinate_ids}")
        print(f"测试获取非下属用户 {non_subordinate_email_prefix} 的考勤记录（使用自己作为测试）")

        result = user_info_service.get_subordinate_attendance(
            target_email_prefix=non_subordinate_email_prefix,
            current_user_email_prefix=current_user
        )

        if not result.get('success'):
            message = result.get('message', '')
            print(f"✓ 正确拦截了无权限访问: {message}")
            return True
        else:
            print("✗ 应该拦截无权限访问，但请求成功了")
            return False

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def save_test_results(results):
    """保存测试结果到JSON文件"""
    try:
        output_file = os.path.join(
            os.path.dirname(__file__),
            '..',
            '..',
            'attendance_test_results.json'
        )

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n测试结果已保存到: {output_file}")

    except Exception as e:
        print(f"保存测试结果失败: {e}")


def main():
    """主测试函数"""
    print("开始测试考勤服务功能...")
    print("=" * 50)

    test_results = {}
    detailed_results = {}

    # 测试1: 获取下属列表
    success, subordinates = test_get_subordinates()
    test_results['获取下属列表'] = success
    detailed_results['subordinates'] = [
        {
            'userId': sub.get('userId'),
            'userName': sub.get('userName'),
            'deptName': sub.get('deptName')
        }
        for sub in subordinates
    ] if success else []

    # 测试2: 获取考勤记录
    test_results['获取考勤记录'] = test_get_attendance()

    # 测试3: 获取下属考勤记录（有权限）
    has_permission_result = test_get_subordinate_attendance_with_permission()
    if has_permission_result is not None:
        test_results['获取下属考勤记录（有权限）'] = has_permission_result
    else:
        test_results['获取下属考勤记录（有权限）'] = '跳过'

    # 测试4: 获取非下属考勤记录（无权限）
    test_results['获取非下属考勤记录（无权限）'] = test_get_subordinate_attendance_without_permission()

    # 输出测试总结
    print("\n" + "=" * 50)
    print("测试结果总结:")
    print("=" * 50)

    passed_tests = 0
    total_tests = 0

    for test_name, result in test_results.items():
        if result == '跳过':
            status = "⊘ 跳过"
        else:
            total_tests += 1
            status = "✓ 通过" if result else "✗ 失败"
            if result:
                passed_tests += 1

        print(f"{test_name:>25}: {status}")

    print("-" * 50)
    print(f"总计: {passed_tests}/{total_tests} 项测试通过")

    # 保存测试结果
    detailed_results['summary'] = {
        'total': total_tests,
        'passed': passed_tests,
        'failed': total_tests - passed_tests,
        'test_results': test_results
    }
    save_test_results(detailed_results)

    if passed_tests == total_tests:
        print("\n🎉 所有测试均通过!")
        return 0
    else:
        print(f"\n⚠ {total_tests - passed_tests} 项测试失败，请检查相关配置。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
