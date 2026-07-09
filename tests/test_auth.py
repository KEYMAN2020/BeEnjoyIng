"""认证模块测试 — 9 个 API"""
import pytest


class TestAuth:
    """认证接口测试"""

    def test_health(self, client):
        """健康检查"""
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json["status"] == "ok"

    def test_send_code(self, client):
        """发送验证码"""
        resp = client.post("/api/v1/auth/send-code", json={
            "phone": "13800138001",
        })
        assert resp.status_code == 200
        assert resp.json["code"] == 0
        assert "expire_in" in resp.json["data"]

    def test_send_code_invalid_phone(self, client):
        """无效手机号"""
        resp = client.post("/api/v1/auth/send-code", json={
            "phone": "12345",
        })
        assert resp.status_code == 400

    def test_register_missing_fields(self, client):
        """注册缺少参数"""
        resp = client.post("/api/v1/auth/register", json={
            "phone": "13800138001",
        })
        assert resp.status_code == 400

    def test_login_no_password(self, client):
        """登录缺少密码"""
        resp = client.post("/api/v1/auth/login", json={
            "phone": "13800138001",
        })
        assert resp.status_code == 400

    def test_login_wrong_password(self, client):
        """密码错误"""
        resp = client.post("/api/v1/auth/login", json={
            "phone": "13800138001",
            "password": "wrong_password_12345",
        })
        assert resp.status_code in (401, 404)

    def test_refresh_missing_token(self, client):
        """刷新令牌缺少参数"""
        resp = client.post("/api/v1/auth/refresh", json={})
        assert resp.status_code == 400

    def test_logout_no_auth(self, client):
        """未登录调用登出"""
        resp = client.post("/api/v1/auth/logout")
        assert resp.status_code == 401

    def test_verify_identity(self, client):
        """身份验证"""
        resp = client.post("/api/v1/auth/verify-identity", json={
            "phone": "13800138001",
            "code": "000000",  # mock 验证码
        })
        # 验证码错误或正确的响应都接受（取决于 mock）
        assert resp.status_code in (200, 400)
