"""测试变量解析功能"""
import re

def test_variable_resolution():
    """测试变量解析"""
    
    # 模拟全局变量
    global_vars = {
        "version": "1.0.0",
        "app_name": "MyPostMan",
        "port": "8080"
    }
    
    # 模拟环境变量（可以引用全局变量）
    env_vars = {
        "base_url": "http://localhost:{{port}}/api",
        "api_endpoint": "{{base_url}}/users",
        "timeout": "30"
    }
    
    # 合并变量（环境变量优先级高）
    all_vars = {}
    all_vars.update(global_vars)
    all_vars.update(env_vars)
    
    # 变量解析函数
    def resolve_variables(text):
        if not text:
            return text
        
        def replace_var(match):
            var_name = match.group(1)
            return all_vars.get(var_name, match.group(0))
        
        # 多轮解析，处理变量中引用变量的情况
        resolved_text = text
        for _ in range(10):  # 最多10轮
            new_text = re.sub(r'\{\{(\w+)\}\}', replace_var, resolved_text)
            if new_text == resolved_text:
                break
            resolved_text = new_text
        
        return resolved_text
    
    # 测试用例
    test_cases = [
        # (输入, 期望输出)
        ("{{base_url}}", "http://localhost:8080/api"),
        ("{{api_endpoint}}", "http://localhost:8080/api/users"),
        ("{{version}}", "1.0.0"),
        ("API地址: {{base_url}}/test", "API地址: http://localhost:8080/api/test"),
        ("应用: {{app_name}}, 版本: {{version}}", "应用: MyPostMan, 版本: 1.0.0"),
        ("{{unknown_var}}", "{{unknown_var}}"),  # 未知变量保留原文
    ]
    
    print("开始测试变量解析功能...")
    print("=" * 60)
    
    all_passed = True
    for i, (input_text, expected) in enumerate(test_cases, 1):
        result = resolve_variables(input_text)
        passed = result == expected
        all_passed = all_passed and passed
        
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"测试 {i}: {status}")
        print(f"  输入:   {input_text}")
        print(f"  期望:   {expected}")
        print(f"  实际:   {result}")
        print()
    
    print("=" * 60)
    if all_passed:
        print("所有测试通过！✓")
    else:
        print("部分测试失败！✗")

if __name__ == "__main__":
    test_variable_resolution()
