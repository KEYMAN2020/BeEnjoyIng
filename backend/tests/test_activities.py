"""活动模块测试 — 关键 API"""
import pytest


class TestActivities:
    """活动接口测试"""

    def test_list_activities(self, client):
        """活动列表"""
        resp = client.get("/api/v1/activities")
        assert resp.status_code == 200
        data = resp.json
        assert data["code"] == 0
        assert "activities" in data["data"]
        assert "total" in data["data"]

    def test_list_activities_with_filters(self, client):
        """活动列表（带筛选）"""
        resp = client.get("/api/v1/activities?city=北京&status=approved&page=1&per_page=10")
        assert resp.status_code == 200
        assert resp.json["code"] == 0

    def test_list_categories(self, client):
        """活动分类"""
        resp = client.get("/api/v1/activities/categories")
        assert resp.status_code == 200
        assert "categories" in resp.json["data"]

    def test_list_tags(self, client):
        """活动标签"""
        resp = client.get("/api/v1/activities/tags")
        assert resp.status_code == 200
        assert "tags" in resp.json["data"]

    def test_get_activity_detail_not_found(self, client):
        """不存在的活动"""
        resp = client.get("/api/v1/activities/99999")
        assert resp.status_code == 404

    def test_create_activity_no_auth(self, client):
        """未登录创建活动"""
        resp = client.post("/api/v1/activities", json={"title": "测试"})
        assert resp.status_code == 401

    def test_create_activity_as_user(self, client, auth_headers):
        """普通用户创建活动（应失败）"""
        resp = client.post("/api/v1/activities", headers=auth_headers, json={
            "title": "测试活动",
            "category_id": 1,
            "location_name": "测试地点",
            "start_time": "2026-07-01 09:00:00",
            "end_time": "2026-07-01 17:00:00",
            "max_participants": 20,
        })
        # 不是领队，应该返回 403
        assert resp.status_code == 403

    def test_nearby_activities_missing_coords(self, client):
        """附近活动缺少坐标"""
        resp = client.get("/api/v1/activities/nearby")
        assert resp.status_code == 400

    def test_nearby_activities(self, client):
        """附近活动"""
        resp = client.get("/api/v1/activities/nearby?lat=39.9&lng=116.4&radius_km=10")
        assert resp.status_code == 200
        assert "activities" in resp.json["data"]

    def test_my_activities_no_auth(self, client):
        """未登录查看我的活动"""
        resp = client.get("/api/v1/activities/my")
        assert resp.status_code == 401

    def test_my_activities(self, client, auth_headers):
        """我的活动"""
        resp = client.get("/api/v1/activities/my", headers=auth_headers)
        assert resp.status_code == 200

    def test_my_favorites(self, client, auth_headers):
        """我收藏的活动"""
        resp = client.get("/api/v1/activities/my-favorites", headers=auth_headers)
        assert resp.status_code == 200

    def test_favorite_no_auth(self, client):
        """未登录收藏"""
        resp = client.post("/api/v1/activities/1/favorite")
        assert resp.status_code == 401

    def test_signup_no_auth(self, client):
        """未登录报名"""
        resp = client.post("/api/v1/activities/1/signup")
        assert resp.status_code == 401
