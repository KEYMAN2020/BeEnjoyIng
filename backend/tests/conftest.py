"""pytest 配置 — Flask 测试客户端 + 测试用 JWT"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app as flask_app
from jwt_helper import generate_access_token
from db import execute_insert, execute_query_one, execute_update

# ── 测试用的用户 ID（需先在数据库中准备） ─────────────────
# 这些测试用户需要在运行测试前手动创建
TEST_USER_ID = 1         # 替换为你的测试用户 ID
TEST_USER_PHONE = "13800138001"
TEST_CAPTAIN_ID = 2      # 替换为领队用户 ID


@pytest.fixture
def app():
    flask_app.config["TESTING"] = True
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers():
    """普通用户认证头"""
    token = generate_access_token(TEST_USER_ID, "user")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def captain_headers():
    """领队用户认证头"""
    token = generate_access_token(TEST_CAPTAIN_ID, "captain")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers():
    """管理员认证头"""
    token = generate_access_token(1, "admin")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def setup_teardown():
    """每个测试前后的公共逻辑"""
    # ── setup ──
    yield
    # ── teardown（清理测试数据） ──
    # 注意：默认不清除，防止误删生产数据
    # 各测试模块自行清理
    pass
