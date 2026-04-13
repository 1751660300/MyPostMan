"""测试请求列表数据库迁移功能"""
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from managers.request_list_manager import RequestListManager

def test_request_list():
    print("=" * 50)
    print("测试请求列表数据库功能")
    print("=" * 50)
    
    try:
        # 初始化管理器
        manager = RequestListManager()
        print("✓ RequestListManager 初始化成功")
        
        # 获取所有请求
        requests = manager.get_all_requests()
        print(f"✓ 当前请求数量: {len(requests)}")
        
        # 添加测试请求
        print("\n添加测试请求...")
        new_req = manager.add_request(
            url="https://api.example.com/test",
            method="POST",
            name="测试API",
            params={"key1": "value1"},
            headers={"Content-Type": "application/json"}
        )
        print(f"✓ 添加成功: {new_req.name} (ID: {new_req.id})")
        
        # 再次获取所有请求
        requests = manager.get_all_requests()
        print(f"✓ 更新后请求数量: {len(requests)}")
        
        # 获取单个请求
        retrieved = manager.get_request(new_req.id)
        if retrieved:
            print(f"✓ 成功获取请求: {retrieved.name}")
            print(f"  - URL: {retrieved.url}")
            print(f"  - Method: {retrieved.method}")
            print(f"  - Params: {retrieved.params}")
            print(f"  - Headers: {retrieved.headers}")
        
        # 删除测试请求
        print("\n删除测试请求...")
        deleted = manager.remove_request(new_req.id)
        if deleted:
            print(f"✓ 删除成功")
        
        # 验证删除
        requests = manager.get_all_requests()
        print(f"✓ 删除后请求数量: {len(requests)}")
        
        print("\n" + "=" * 50)
        print("所有测试通过! ✓")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_request_list()
