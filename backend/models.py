# -*- coding: utf-8 -*-
"""
银发活力平台 — 数据模型层
"""

from datetime import datetime
from db import query_one, query_all, execute, commit, rollback
from response import ApiError
from utils import hash_password


# =====================================================
# 用户查询
# =====================================================

def get_user_by_phone(phone):
    """通过手机号查询未删除的用户。"""
    return query_one("SELECT * FROM users WHERE phone=%s AND deleted_at IS NULL LIMIT 1", (phone,))


def get_user_by_id(user_id):
    """通过 ID 查询未删除的用户。"""
    return query_one("SELECT * FROM users WHERE id=%s AND deleted_at IS NULL LIMIT 1", (user_id,))


def get_user_auth(user_id):
    """查询用户的密码认证记录。"""
    return query_one(
        "SELECT * FROM user_auth WHERE user_id=%s AND auth_type=%s LIMIT 1",
        (user_id, "password"),
    )


def get_user_profile(user_id):
    """获取用户完整资料（三表联查）。"""
    sql = (
        "SELECT u.id, u.phone, u.nickname, u.avatar_url, u.role, u.is_banned, u.created_at, "
        "p.gender, p.birth_year, p.city, p.district, p.province_code, p.city_code, "
        "p.district_code, p.bio, p.interests, p.real_name, "
        "p.ghost_mode, p.allow_private_msg, p.allow_profile_view, "
        "s.vitality, s.activity_count, s.activity_streak, s.friends_count, s.last_active_at "
        "FROM users u "
        "LEFT JOIN user_profiles p ON p.user_id = u.id "
        "LEFT JOIN user_stats s ON s.user_id = u.id "
        "WHERE u.id=%s AND u.deleted_at IS NULL "
        "LIMIT 1"
    )
    return query_one(sql, (user_id,))


def public_user_fields(row):
    """将数据库行转换为对外公开的用户资料。"""
    if not row:
        return None
    interests = row.get("interests")
    if isinstance(interests, str):
        interests = [x.strip() for x in interests.split(",") if x.strip()]
    created = row.get("created_at")
    if isinstance(created, datetime):
        created = created.isoformat()
    return {
        "user_id": row["id"],
        "nickname": row.get("nickname"),
        "avatar_url": row.get("avatar_url"),
        "gender": row.get("gender"),
        "birth_year": row.get("birth_year"),
        "city": row.get("city"),
        "district": row.get("district"),
        "bio": row.get("bio"),
        "interests": interests or [],
        "vitality": row.get("vitality") or 0,
        "activity_count": row.get("activity_count") or 0,
        "created_at": created,
    }


def create_user_with_profile(phone, password, basic_info):
    """注册新用户，创建 users / user_auth / user_profiles / user_stats 四条记录。"""
    password_hash = hash_password(password)
    nickname = basic_info.get("nickname") or "用户" + phone[-4:]
    avatar_url = basic_info.get("avatar_url") or basic_info.get("avatar")
    gender = basic_info.get("gender")
    birth_year = basic_info.get("birth_year")
    city = basic_info.get("city")
    district = basic_info.get("district")
    interests = basic_info.get("interests")
    if isinstance(interests, list):
        interests = ",".join([str(x).strip() for x in interests if str(x).strip()])

    try:
        existing = query_one(
            "SELECT id FROM users WHERE phone=%s AND deleted_at IS NOT NULL LIMIT 1", (phone,)
        )
        if existing:
            old_uid = existing["id"]
            execute("DELETE FROM user_auth WHERE user_id=%s", (old_uid,))
            execute("DELETE FROM user_profiles WHERE user_id=%s", (old_uid,))
            execute("DELETE FROM user_stats WHERE user_id=%s", (old_uid,))
            execute("DELETE FROM users WHERE id=%s", (old_uid,))

        user_id, _ = execute(
            "INSERT INTO users (phone, nickname, avatar_url, role, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, NOW(), NOW())",
            (phone, nickname, avatar_url, "user"),
        )
        execute(
            "INSERT INTO user_auth (user_id, auth_type, auth_value, created_at) "
            "VALUES (%s, %s, %s, NOW())",
            (user_id, "password", password_hash),
        )
        execute(
            "INSERT INTO user_profiles (user_id, gender, birth_year, city, district, interests, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, NOW())",
            (user_id, gender, birth_year, city, district, interests),
        )
        execute(
            "INSERT INTO user_stats (user_id, vitality, activity_count, activity_streak, friends_count, updated_at) "
            "VALUES (%s, 0, 0, 0, 0, NOW())",
            (user_id,),
        )
        commit()
        return user_id
    except Exception:
        rollback()
        raise ApiError("注册失败，请稍后重试", http_status=500)


def update_password(user_id, new_password):
    """更新用户密码。"""
    password_hash = hash_password(new_password)
    try:
        row = query_one(
            "SELECT id FROM user_auth WHERE user_id=%s AND auth_type=%s LIMIT 1",
            (user_id, "password"),
        )
        if row:
            execute(
                "UPDATE user_auth SET auth_value=%s WHERE user_id=%s AND auth_type=%s",
                (password_hash, user_id, "password"),
            )
        else:
            execute(
                "INSERT INTO user_auth (user_id, auth_type, auth_value, created_at) "
                "VALUES (%s, %s, %s, NOW())",
                (user_id, "password", password_hash),
            )
        commit()
    except Exception:
        rollback()
        raise ApiError("密码更新失败，请稍后重试", http_status=500)


def update_profile(user_id, payload):
    """更新用户资料（users + user_profiles）。"""
    user_allowed = ["nickname", "avatar_url"]
    profile_allowed = ["gender", "birth_year", "city", "district", "bio", "interests", "real_name"]

    try:
        user_sets = []
        user_vals = []
        for k in user_allowed:
            if k in payload:
                v = payload[k]
                if k == "nickname" and v and len(v) > 50:
                    raise ApiError("昵称不能超过50个字符", 30001)
                user_sets.append("%s=%%s" % k)
                user_vals.append(v)
        if user_sets:
            user_vals.append(user_id)
            execute(
                "UPDATE users SET %s, updated_at=NOW() WHERE id=%%s" % ", ".join(user_sets),
                tuple(user_vals),
            )

        prof_sets = []
        prof_vals = []
        for k in profile_allowed:
            if k in payload:
                v = payload[k]
                if k == "interests" and isinstance(v, list):
                    v = ",".join([str(x).strip() for x in v if str(x).strip()])
                if k == "bio" and v and len(v) > 500:
                    raise ApiError("个人简介不能超过500个字符", 30001)
                if k == "birth_year" and v:
                    v = int(v)
                    if v < 1920 or v > 2010:
                        raise ApiError("出生年份不在合理范围内", 30001)
                prof_sets.append("%s=%%s" % k)
                prof_vals.append(v)
        if prof_sets:
            prof_vals.append(user_id)
            execute(
                "UPDATE user_profiles SET %s, updated_at=NOW() WHERE user_id=%%s"
                % ", ".join(prof_sets),
                tuple(prof_vals),
            )

        commit()
    except ApiError:
        raise
    except Exception:
        rollback()
        raise ApiError("资料更新失败，请稍后重试", http_status=500)
