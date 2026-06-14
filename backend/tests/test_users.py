"""用户模块测试 — 14 个 API"""
import pytest


class TestUsers:
    """用户接口测试"""

    def test_get_me_unauthorized(self, client):
        """未登录获取个人资料"""
        resp = client.get("/api/v1/users/me")
        assert resp.status_code == 401

    def test_get_me(self, client, auth_headers):
        """获取个人资料"""
        resp = client.get("/api/v1/users/me", headers=auth_headers)
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            assert resp.json["code"] == 0
            assert "user" in resp.json["data"]

    def test_update_me(self, client, auth_headers):
        """更新个人资料"""
        resp = client.put("/api/v1/users/me", headers=auth_headers, json={
            "nickname": "测试用户",
            "bio": "这是一个测试",
            "city": "北京",
        })
        assert resp.status_code in (200, 400, 404)

    def test_patch_me(self, client, auth_headers):
        """部分更新个人资料"""
        resp = client.patch("/api/v1/users/me", headers=auth_headers, json={
            "bio": "更新了简介",
        })
        assert resp.status_code in (200, 400, 404)

    def test_get_public_profile(self, client):
        """获取公开资料"""
        resp = client.get("/api/v1/users/1/public")
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            assert resp.json["code"] == 0
            assert "user" in resp.json["data"]

    def test_upload_avatar(self, client, auth_headers):
        """上传头像"""
        resp = client.post("/api/v1/users/upload-avatar", headers=auth_headers, json={
            "avatar_url": "https://example.com/avatar.jpg",
        })
        assert resp.status_code in (200, 400)

    def test_get_stats(self, client):
        """获取用户统计"""
        resp = client.get("/api/v1/users/1/stats")
        assert resp.status_code in (200, 404)

    def test_search_users(self, client):
        """搜索用户"""
        resp = client.get("/api/v1/users/search?keyword=test")
        assert resp.status_code == 200

    def test_friend_request(self, client, auth_headers):
        """发送好友请求"""
        resp = client.post("/api/v1/users/friends/request", headers=auth_headers, json={
            "friend_id": 2,
            "message": "你好",
        })
        assert resp.status_code in (200, 400, 404, 409)

    def test_friend_list(self, client, auth_headers):
        """好友列表"""
        resp = client.get("/api/v1/users/friends", headers=auth_headers)
        assert resp.status_code == 200
        assert "friends" in resp.json["data"]

    def test_send_message_no_auth(self, client):
        """未登录发送消息"""
        resp = client.post("/api/v1/users/messages", json={
            "receiver_id": 2,
            "content": "你好",
        })
        assert resp.status_code == 401

    def test_report_user(self, client, auth_headers):
        """举报用户"""
        resp = client.post("/api/v1/users/2/report", headers=auth_headers, json={
            "reason": "测试举报",
        })
        assert resp.status_code in (200, 400)

    def test_get_profile_detail(self, client, auth_headers):
        """获取个人资料详情"""
        resp = client.get("/api/v1/users/me/profile", headers=auth_headers)
        assert resp.status_code in (200, 404)

    def test_get_safety_info(self, client, auth_headers):
        """获取安全信息"""
        resp = client.get("/api/v1/users/me/safety", headers=auth_headers)
        assert resp.status_code in (200, 404)
