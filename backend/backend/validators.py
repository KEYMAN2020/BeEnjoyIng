"""输入校验模块 — 基于 marshmallow

使用方式:
  from validators import validate_json, CreateActivitySchema

  data, err = validate_json(request.json, CreateActivitySchema())
  if err:
      return err
  # data 是校验后的干净数据
"""

from marshmallow import Schema, fields, validate, ValidationError
from response import error


def validate_json(json_data: dict | None, schema: Schema) -> tuple:
    """校验 JSON 请求体

    返回 (cleaned_data, None) 或 (None, error_response)
    """
    if json_data is None:
        return None, error("请求体不能为空", 400)

    try:
        result = schema.load(json_data)
        return result, None
    except ValidationError as e:
        # 取第一条错误信息
        messages = e.messages
        first_field = list(messages.keys())[0]
        first_msg = messages[first_field]
        if isinstance(first_msg, list):
            first_msg = first_msg[0]
        return None, error(f"{first_field}: {first_msg}", 400)


# ── 认证 ────────────────────────────────────────────────

class SendCodeSchema(Schema):
    phone = fields.String(required=True, validate=validate.Length(min=7, max=20))


class RegisterSchema(Schema):
    phone = fields.String(required=True, validate=validate.Length(min=7, max=20))
    code = fields.String(required=True, validate=validate.Length(equal=6))
    password = fields.String(required=True, validate=validate.Length(min=6, max=128))
    nickname = fields.String(required=False, validate=validate.Length(max=50))


class LoginSchema(Schema):
    phone = fields.String(required=True, validate=validate.Length(min=7, max=20))
    password = fields.String(required=True)


class RefreshSchema(Schema):
    refresh_token = fields.String(required=True)


class ResetPasswordSchema(Schema):
    phone = fields.String(required=True, validate=validate.Length(min=7, max=20))
    code = fields.String(required=True, validate=validate.Length(equal=6))
    new_password = fields.String(required=True, validate=validate.Length(min=6, max=128))


class ChangePasswordSchema(Schema):
    old_password = fields.String(required=True)
    new_password = fields.String(required=True, validate=validate.Length(min=6, max=128))


# ── 用户 ────────────────────────────────────────────────

class UpdateUserSchema(Schema):
    nickname = fields.String(validate=validate.Length(max=50))
    avatar_url = fields.URL(relative=True)
    real_name = fields.String(validate=validate.Length(max=50))
    gender = fields.String(validate=validate.OneOf(["male", "female", "other"]))
    birth_year = fields.Integer(validate=validate.Range(min=1900, max=2026))
    city = fields.String(validate=validate.Length(max=50))
    district = fields.String(validate=validate.Length(max=50))
    bio = fields.String(validate=validate.Length(max=500))
    interests = fields.String(validate=validate.Length(max=500))


class AvatarSchema(Schema):
    avatar_url = fields.URL(required=True, relative=True)


# ── 活动 ────────────────────────────────────────────────

class CreateActivitySchema(Schema):
    title = fields.String(required=True, validate=validate.Length(min=2, max=200))
    category_id = fields.Integer(required=True)
    description = fields.String(validate=validate.Length(max=5000))
    cover_image = fields.String()
    location_name = fields.String(required=True, validate=validate.Length(max=200))
    location_address = fields.String(validate=validate.Length(max=500))
    location_lat = fields.Float()
    location_lng = fields.Float()
    city = fields.String(validate=validate.Length(max=50))
    district = fields.String(validate=validate.Length(max=50))
    start_time = fields.String(required=True)
    end_time = fields.String(required=True)
    signup_deadline = fields.String()
    max_participants = fields.Integer(required=True, validate=validate.Range(min=1, max=10000))
    min_participants = fields.Integer(validate=validate.Range(min=1))
    price = fields.Float(validate=validate.Range(min=0))
    safety_level = fields.String(validate=validate.OneOf(["green", "yellow", "red"]))
    age_min = fields.Integer(validate=validate.Range(min=0))
    age_max = fields.Integer(validate=validate.Range(min=0))
    has_waitlist = fields.Boolean()


class ReviewActivitySchema(Schema):
    action = fields.String(required=True, validate=validate.OneOf(["approve", "reject"]))
    comment = fields.String()


class RateActivitySchema(Schema):
    rating = fields.String(required=True, validate=validate.OneOf(["好评", "中评", "差评"]))


class SignupSchema(Schema):
    user_id = fields.Integer()


class SitePhotoSchema(Schema):
    image_url = fields.String(required=True)


# ── 领队 ────────────────────────────────────────────────

class ApplyCaptainSchema(Schema):
    real_name = fields.String(required=True, validate=validate.Length(max=100))
    phone = fields.String(required=True, validate=validate.Length(max=20))
    id_card_last4 = fields.String(validate=validate.Length(equal=4))
    bio = fields.String(validate=validate.Length(max=2000))
    experience = fields.String(validate=validate.Length(max=5000))
    preferred_categories = fields.String(validate=validate.Length(max=500))


class TrainingSchema(Schema):
    training_type = fields.String(required=True, validate=validate.Length(max=50))
    content = fields.String(validate=validate.Length(max=5000))
    score = fields.Integer(validate=validate.Range(min=0, max=100))
    trainer = fields.String(validate=validate.Length(max=100))
    expire_at = fields.String()


# ── 合作伙伴 ────────────────────────────────────────────

class ApplyPartnerSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(max=200))
    city = fields.String(required=True, validate=validate.Length(max=50))
    district = fields.String(required=True, validate=validate.Length(max=50))
    address = fields.String(validate=validate.Length(max=500))
    contact_name = fields.String(required=True, validate=validate.Length(max=100))
    contact_phone = fields.String(required=True, validate=validate.Length(max=20))
    contact_position = fields.String(validate=validate.Length(max=100))
    venues = fields.String()
    partner_street = fields.String(validate=validate.Length(max=200))


# ── 支付 ────────────────────────────────────────────────

class CreatePaymentSchema(Schema):
    signup_id = fields.Integer(required=True)
    activity_id = fields.Integer(required=True)
    amount = fields.Float(required=True, validate=validate.Range(min=0.01))
    payment_method = fields.String(required=True, validate=validate.OneOf(["wechat", "alipay", "card"]))


class SubscriptionSchema(Schema):
    plan_type = fields.String(required=True, validate=validate.OneOf(["monthly", "yearly"]))
    amount = fields.Float(required=True, validate=validate.Range(min=0.01))
    payment_method = fields.String(required=True)
    auto_renew = fields.Boolean()


# ── 健康 ────────────────────────────────────────────────

class HealthDeclareSchema(Schema):
    activity_id = fields.Integer(required=True)
    health_status = fields.String(validate=validate.OneOf(["good", "fair", "poor"]))
    note = fields.String(validate=validate.Length(max=1000))


# ── 聊天 ────────────────────────────────────────────────

class CreateGroupSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=200))
    avatar = fields.String()
    activity_id = fields.Integer()
    member_ids = fields.List(fields.Integer())


class SendMessageSchema(Schema):
    msg_type = fields.String(validate=validate.OneOf(["text", "voice", "image"]))
    content = fields.String(validate=validate.Length(max=5000))
    voice_url = fields.String()
    voice_duration = fields.Integer()
    image_url = fields.String()


# ── 通知 ────────────────────────────────────────────────

class FriendRequestSchema(Schema):
    friend_id = fields.Integer(required=True)
    message = fields.String(validate=validate.Length(max=200))


class ReportUserSchema(Schema):
    reason = fields.String(required=True, validate=validate.Length(min=1, max=500))
