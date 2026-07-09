"""其他模块综合测试"""
import pytest


class TestChat:
    """聊天接口测试"""

    def test_list_groups_no_auth(self, client):
        resp = client.get("/api/v1/chat/groups")
        assert resp.status_code == 401

    def test_list_groups(self, client, auth_headers):
        resp = client.get("/api/v1/chat/groups", headers=auth_headers)
        assert resp.status_code == 200
        assert "groups" in resp.json["data"]


class TestCaptain:
    """领队接口测试"""

    def test_apply_no_auth(self, client):
        resp = client.post("/api/v1/captain/apply", json={"real_name": "测试", "phone": "13800138001"})
        assert resp.status_code == 401

    def test_get_application_no_auth(self, client):
        resp = client.get("/api/v1/captain/application")
        assert resp.status_code == 401


class TestPartner:
    """合作伙伴接口测试"""

    def test_list_streets(self, client):
        resp = client.get("/api/v1/partner/streets")
        assert resp.status_code == 200
        assert "streets" in resp.json["data"]

    def test_list_profiles(self, client):
        resp = client.get("/api/v1/partner/profiles")
        assert resp.status_code == 200

    def test_get_profile(self, client):
        resp = client.get("/api/v1/partner/profiles/1")
        assert resp.status_code in (200, 404)


class TestPayment:
    """支付接口测试"""

    def test_create_no_auth(self, client):
        resp = client.post("/api/v1/payment/create", json={
            "signup_id": 1, "activity_id": 1, "amount": 100, "payment_method": "wechat",
        })
        assert resp.status_code == 401

    def test_list_records_no_auth(self, client):
        resp = client.get("/api/v1/payment/records")
        assert resp.status_code == 401


class TestHealth:
    """健康模块测试"""

    def test_declare_no_auth(self, client):
        resp = client.post("/api/v1/health/declare", json={
            "activity_id": 1, "health_status": "good",
        })
        assert resp.status_code == 401


class TestNotification:
    """通知模块测试"""

    def test_list_no_auth(self, client):
        resp = client.get("/api/v1/notifications")
        assert resp.status_code == 401

    def test_list(self, client, auth_headers):
        resp = client.get("/api/v1/notifications", headers=auth_headers)
        assert resp.status_code == 200


class TestSystem:
    """系统模块测试"""

    def test_regions(self, client):
        resp = client.get("/api/v1/regions")
        assert resp.status_code == 200

    def test_config_not_found(self, client):
        resp = client.get("/api/v1/system/config/nonexistent")
        assert resp.status_code == 404


class TestUpload:
    """文件上传测试"""

    def test_upload_no_file(self, client):
        resp = client.post("/api/v1/upload")
        assert resp.status_code == 400

    def test_upload_no_auth_needed(self, client):
        """上传接口不需要认证"""
        resp = client.post("/api/v1/upload")
        assert resp.status_code == 400  # 没文件所以400，不是401


class TestCORS:
    """CORS 测试"""

    def test_cors_headers(self, client):
        resp = client.options("/api/v1/activities", headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "GET",
        })
        assert resp.status_code == 200
        # flask-cors 会镜像 Origin 返回
        assert resp.headers.get("Access-Control-Allow-Origin") == "http://example.com"


class TestSwagger:
    """Swagger 文档测试"""

    def test_swagger_ui(self, client):
        resp = client.get("/apidocs/")
        assert resp.status_code in (200, 301, 302)

    def test_swagger_json(self, client):
        resp = client.get("/apispec_1.json")
        assert resp.status_code in (200, 404)
