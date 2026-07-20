import json
import pytest
from pathlib import Path
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app


@pytest.fixture
def client():
    """创建测试客户端"""
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-key"
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


@pytest.fixture
def logged_in_client(client):
    """登录后的测试客户端"""
    client.post(
        "/login",
        data={"username": "student", "password": "day07"},
        follow_redirects=True
    )
    return client


def test_health_endpoint(client):
    """测试 /health 返回 200（不需要登录）"""
    response = client.get("/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["ok"] is True
    assert data["service"] == "day08-flask-upgrade"


def test_dashboard_requires_login(client):
    """测试未登录访问 /dashboard 被拦截"""
    response = client.get("/dashboard", follow_redirects=True)
    assert response.status_code == 200
    # 应该重定向到登录页面
    content = response.data.decode('utf-8', errors='ignore')
    assert "login" in content.lower() or "登录" in content


def test_dashboard_logged_in(logged_in_client):
    """测试登录后访问 /dashboard 成功"""
    response = logged_in_client.get("/dashboard")
    assert response.status_code == 200
    # 应该返回 HTML 页面
    content = response.data.decode('utf-8', errors='ignore')
    assert "<!DOCTYPE html" in content or "<html" in content.lower()


def test_assistant_requires_login(client):
    """测试未登录访问 /assistant 被拦截"""
    response = client.get("/assistant", follow_redirects=True)
    assert response.status_code == 200
    content = response.data.decode('utf-8', errors='ignore')
    assert "login" in content.lower() or "登录" in content


def test_assistant_logged_in(logged_in_client):
    """测试登录后访问 /assistant 成功"""
    response = logged_in_client.get("/assistant")
    assert response.status_code == 200
    # 应该返回 HTML 页面
    content = response.data.decode('utf-8', errors='ignore')
    assert "<!DOCTYPE html" in content or "<html" in content.lower()


def test_metrics_api_requires_login(client):
    """测试未登录访问 /api/metrics 被拦截"""
    response = client.get("/api/metrics", follow_redirects=True)
    assert response.status_code == 200
    content = response.data.decode('utf-8', errors='ignore')
    assert "login" in content.lower() or "登录" in content


def test_metrics_api_logged_in(logged_in_client):
    """测试登录后访问 /api/metrics 返回正确数据"""
    response = logged_in_client.get("/api/metrics")
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data["ok"] is True
    assert "metrics" in data
    assert isinstance(data["metrics"], list)
    assert len(data["metrics"]) == 4
    
    expected_labels = ["总用户数", "流失用户", "总体流失率", "平均订单数"]
    actual_labels = [m["label"] for m in data["metrics"]]
    assert set(actual_labels) == set(expected_labels)
    
    for metric in data["metrics"]:
        assert "label" in metric
        assert "value" in metric
        assert "note" in metric
        assert metric["value"] != ""


def test_categories_api_requires_login(client):
    """测试未登录访问 /api/categories 被拦截"""
    response = client.get("/api/categories", follow_redirects=True)
    assert response.status_code == 200
    content = response.data.decode('utf-8', errors='ignore')
    assert "login" in content.lower() or "登录" in content


def test_categories_api_all(logged_in_client):
    """测试登录后访问 /api/categories 返回所有品类"""
    response = logged_in_client.get("/api/categories")
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data["ok"] is True
    assert data["category"] == "全部"
    assert "rows" in data
    assert isinstance(data["rows"], list)
    assert len(data["rows"]) > 0


def test_categories_api_filter_fashion(logged_in_client):
    """测试登录后访问 /api/categories?category=Fashion 返回筛选结果"""
    response = logged_in_client.get("/api/categories?category=Fashion")
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data["ok"] is True
    assert data["category"] == "Fashion"
    assert "rows" in data
    assert isinstance(data["rows"], list)
    
    # 验证筛选结果只包含 Fashion 品类
    if len(data["rows"]) > 0:
        for row in data["rows"]:
            if "偏好品类" in row:
                assert row["偏好品类"] == "Fashion"


def test_metrics_value_format(logged_in_client):
    """测试指标数值格式是否正确"""
    response = logged_in_client.get("/api/metrics")
    data = json.loads(response.data)
    
    for metric in data["metrics"]:
        value = metric["value"]
        label = metric["label"]
        
        if label == "总用户数":
            assert "," in value
        elif label == "总体流失率":
            assert "%" in value
        elif label == "平均订单数":
            assert "." in value or value.isdigit()


if __name__ == "__main__":
    pytest.main(["-v"])