"""
高德地图地址搜索接口
提供输入提示（POI suggestion）和地理编码功能
"""
import requests
from flask import Blueprint, request
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
AMAP_KEY = config.AMAP_KEY
AMAP_POI_SEARCH_URL = config.AMAP_POI_SEARCH_URL
AMAP_GEOCODE_URL = config.AMAP_GEOCODE_URL

geo_bp = Blueprint("geo", __name__, url_prefix="/api/v1/geo")

def _success(data, msg="ok"):
    return {"code": 0, "data": data, "message": msg}

@geo_bp.get("/search")
def search_poi():
    """地址输入提示"""
    keyword = request.args.get("keyword", "").strip()
    if not keyword or len(keyword) < 1:
        return _success([])
    city = request.args.get("city", "").strip() or ""
    try:
        params = {"key": AMAP_KEY, "keywords": keyword, "datatype": "all", "output": "JSON"}
        if city: params["city"] = city
        else: params["citylimit"] = "false"
        resp = requests.get(AMAP_POI_SEARCH_URL, params=params, timeout=5)
        data = resp.json()
        if data.get("status") == "1" and data.get("tips"):
            results = []
            for tip in data["tips"]:
                item = {"name": tip.get("name", ""), "district": tip.get("district", ""), "adcode": tip.get("adcode", "")}
                if tip.get("location"): item["location"] = tip["location"]
                if tip.get("address"): item["address"] = tip.get("address")
                results.append(item)
            return _success(results)
        return _success([])
    except Exception as e:
        return {"code": -1, "data": [], "message": str(e)}, 500

@geo_bp.get("/geocode")
def geocode():
    address = request.args.get("address", "").strip()
    if not address: return _success(None)
    try:
        params = {"key": AMAP_KEY, "address": address, "output": "JSON"}
        resp = requests.get(AMAP_GEOCODE_URL, params=params, timeout=5)
        data = resp.json()
        if data.get("status") == "1" and data.get("geocodes"):
            geo = data["geocodes"][0]
            return _success({"location": geo.get("location",""), "formatted_address": geo.get("formatted_address",""), "adcode": geo.get("adcode",""), "city": geo.get("city",""), "district": geo.get("district","")})
        return _success(None)
    except Exception as e:
        return {"code": -1, "data": None, "message": str(e)}, 500
