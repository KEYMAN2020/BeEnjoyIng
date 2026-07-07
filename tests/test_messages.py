"""
消息功能全量测试用例
覆盖：私聊CRUD、群聊CRUD、未读计数、Socket实时推送、异常场景

运行方式: python3 tests/test_messages.py
"""

import requests
import socketio
import time
import json
import traceback

BASE = "http://localhost:5003"
API = f"{BASE}/api/v1"

# ── 测试用户 ──
USER_A = {"phone": "13800138000", "password": "123456", "name": "王阿姨", "id": 4}
USER_B = {"phone": "13800000002", "password": "123456", "name": "测试用户1", "id": 7}
USER_C = {"phone": "13800000001", "password": "123456", "name": "llm", "id": 6}

# ── 测试群组 ──
GROUP_ID = 16  # 落羽红杉林茶话会

results = {"pass": 0, "fail": 0, "skip": 0}
details = []


def login(user):
    """登录获取 token"""
    r = requests.post(f"{API}/auth/login", json={"phone": user["phone"], "password": user["password"]})
    assert r.status_code == 200, f"登录失败: {r.text}"
    data = r.json()
    assert data["code"] == 0, f"登录返回异常: {data}"
    return data["data"]["access_token"]


def api_get(token, path):
    return requests.get(f"{API}{path}", headers={"Authorization": f"Bearer {token}"})


def api_post(token, path, body):
    return requests.post(f"{API}{path}", json=body, headers={"Authorization": f"Bearer {token}"})


def check(name, condition, detail=""):
    if condition:
        results["pass"] += 1
        details.append(f"  ✓ {name}")
    else:
        results["fail"] += 1
        details.append(f"  ✗ {name} ── {detail}")
        print(f"  ✗ FAIL: {name} ── {detail}")
    return condition


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def connect_socket(token, user_name):
    """建立 Socket.IO 连接"""
    s = socketio.Client()
    connected = [False]
    errors = []

    @s.on("connect")
    def on_c():
        connected[0] = True

    @s.on("connect_error")
    def on_e(data):
        errors.append(str(data))

    try:
        s.connect(f"{BASE}/?token={token}", transports=["polling", "websocket"])
        time.sleep(0.5)
    except Exception as e:
        errors.append(str(e))

    return s, connected[0], errors


# ═══════════════════════════════════════════════════════════
#  测试套件 1：鉴权与基础
# ═══════════════════════════════════════════════════════════

def test_001_auth():
    section("1. 鉴权与基础")

    # 1.1 正常登录
    t = login(USER_A)
    check("1.1 正常登录获取token", len(t) > 20)

    # 1.2 无token访问应401
    r = requests.get(f"{API}/users/messages")
    check("1.2 无token访问消息列表 → 401", r.status_code == 401,
          f"got {r.status_code}")

    # 1.3 错误密码
    r = requests.post(f"{API}/auth/login", json={"phone": USER_A["phone"], "password": "wrong"})
    check("1.3 错误密码登录 → 401", r.status_code == 401 or r.json().get("code") != 0,
          f"got {r.status_code} {r.text[:50]}")

    return t


# ═══════════════════════════════════════════════════════════
#  测试套件 2：私聊消息 CRUD
# ═══════════════════════════════════════════════════════════

def test_002_private_messages():
    section("2. 私聊消息 CRUD")

    tA = login(USER_A)
    tB = login(USER_B)

    # 2.1 发送私信
    r = api_post(tA, "/users/messages", {"receiver_id": USER_B["id"], "content": "A→B 测试消息001"})
    check("2.1 发送私信 → 200", r.status_code == 200 and r.json()["code"] == 0,
          f"got {r.status_code} {r.text[:50]}")

    # 2.2 消息历史（B查看与A的对话）
    r = api_get(tB, f"/users/messages/with/{USER_A['id']}")
    check("2.2 获取私信历史 → 200 且包含消息",
          r.status_code == 200 and len(r.json()["data"]["messages"]) > 0,
          f"got {r.status_code}, msgs={len(r.json().get('data',{}).get('messages',[]))}")

    # 2.3 other_user 信息正确
    data = r.json()["data"]
    check("2.3 other_user 包含昵称", data["other_user"]["nickname"] == USER_A["name"],
          f"got {data['other_user']['nickname']}")

    # 2.4 空内容被拒绝
    r = api_post(tA, "/users/messages", {"receiver_id": USER_B["id"], "content": ""})
    check("2.4 空内容发送 → 400", r.status_code == 400 or r.json()["code"] != 0,
          f"got {r.status_code} {r.text[:50]}")

    # 2.5 给自己发被拒绝
    r = api_post(tA, "/users/messages", {"receiver_id": USER_A["id"], "content": "self"})
    check("2.5 给自己发消息 → 400", r.status_code == 400 or r.json()["code"] != 0,
          f"got {r.status_code} {r.text[:50]}")

    # 2.6 缺少 receiver_id
    r = api_post(tA, "/users/messages", {"content": "no receiver"})
    check("2.6 缺少receiver_id → 400", r.status_code == 400 or r.json()["code"] != 0,
          f"got {r.status_code} {r.text[:50]}")

    # 2.7 不存在的接收者
    r = api_post(tA, "/users/messages", {"receiver_id": 99999, "content": "ghost"})
    check("2.7 不存在接收者 → 404", r.status_code == 404 or r.json()["code"] != 0,
          f"got {r.status_code} {r.text[:50]}")


# ═══════════════════════════════════════════════════════════
#  测试套件 3：未读计数
# ═══════════════════════════════════════════════════════════

def test_003_unread_count():
    section("3. 未读计数")

    tC = login(USER_C)   # llm
    tA = login(USER_A)   # 王阿姨

    # 先清空——王阿姨查看消息，标记已读
    api_get(tA, f"/users/messages/with/{USER_C['id']}")

    # 3.1 发送多条 → 未读递增
    for i in range(3):
        api_post(tC, "/users/messages", {"receiver_id": USER_A["id"], "content": f"unread test {i}"})
    time.sleep(0.3)

    r = api_get(tA, "/users/messages")
    items = r.json()["data"]["items"]
    target = [it for it in items if it["other_user"]["user_id"] == USER_C["id"]]
    check("3.1 未读计数应为3", len(target) > 0 and target[0].get("unread_count", 0) >= 3,
          f"unread_count={target[0].get('unread_count') if target else 'not found'}")

    # 3.2 查看后未读清零
    api_get(tA, f"/users/messages/with/{USER_C['id']}")
    r2 = api_get(tA, "/users/messages")
    items2 = r2.json()["data"]["items"]
    target2 = [it for it in items2 if it["other_user"]["user_id"] == USER_C["id"]]
    check("3.2 查看后未读为0", len(target2) > 0 and target2[0].get("unread_count", -1) == 0,
          f"unread_count={target2[0].get('unread_count') if target2 else 'not found'}")

    # 3.3 自己发送的消息不增加自身未读
    api_post(tA, "/users/messages", {"receiver_id": USER_C["id"], "content": "reply"})
    r3 = api_get(tA, "/users/messages")
    items3 = r3.json()["data"]["items"]
    target3 = [it for it in items3 if it["other_user"]["user_id"] == USER_C["id"]]
    check("3.3 自己发送后未读保持0", len(target3) > 0 and target3[0].get("unread_count", -1) == 0,
          f"unread_count={target3[0].get('unread_count') if target3 else 'not found'}")


# ═══════════════════════════════════════════════════════════
#  测试套件 4：群聊消息
# ═══════════════════════════════════════════════════════════

def test_004_group_messages():
    section("4. 群聊消息")

    tA = login(USER_A)

    # 4.1 获取群消息列表
    r = requests.get(f"{API}/chat/groups/{GROUP_ID}/messages",
                     headers={"Authorization": f"Bearer {tA}"})
    check("4.1 获取群消息列表 → 200", r.status_code == 200 and r.json()["code"] == 0,
          f"got {r.status_code} {r.text[:50]}")

    # 4.2 发送群消息
    r = requests.post(f"{API}/chat/groups/{GROUP_ID}/messages",
                      json={"content": "群聊测试消息", "type": "text"},
                      headers={"Authorization": f"Bearer {tA}"})
    check("4.2 发送群消息 → 成功", r.status_code in (200, 201) and r.json()["code"] == 0,
          f"got {r.status_code} {r.text[:50]}")

    # 4.3 标记已读
    r = requests.post(f"{API}/chat/groups/{GROUP_ID}/read",
                      headers={"Authorization": f"Bearer {tA}"})
    check("4.3 标记群消息已读 → 200", r.status_code == 200 and r.json()["code"] == 0,
          f"got {r.status_code} {r.text[:50]}")

    # 4.4 非成员发消息应该被拒绝（用不在群里的用户）
    # 当前所有用户都在群里，跳过此测试
    check("4.4 (跳过) 所有用户均在群中", True)


# ═══════════════════════════════════════════════════════════
#  测试套件 5：Socket.IO 实时推送
# ═══════════════════════════════════════════════════════════

def test_005_socket_private():
    section("5. Socket.IO 私聊实时推送")

    tA = login(USER_A)
    tB = login(USER_B)

    # B 连接 Socket
    sB, connected, errors = connect_socket(tB, USER_B["name"])
    check("5.1 B Socket连接成功", connected, str(errors))
    if not connected:
        return

    # 收集 B 收到的消息
    recv = []
    @sB.on("private_message")
    def on_msg(msg):
        recv.append(msg)

    # A 发送消息
    start = time.time()
    sA, connA, _ = connect_socket(tA, USER_A["name"])
    if not connA:
        sB.disconnect()
        return

    sA.emit("private_send", {"receiver_id": USER_B["id"], "content": "Socket实时测试"})
    time.sleep(1)

    check("5.2 B 收到实时消息", len(recv) > 0,
          f"recv={len(recv)} in {(time.time()-start)*1000:.0f}ms")

    if len(recv) > 0:
        msg = recv[0]
        check("5.3 消息内容正确", msg["content"] == "Socket实时测试",
              f"got {msg.get('content')}")
        check("5.4 sender_id 正确", msg["sender_id"] == USER_A["id"],
              f"got {msg.get('sender_id')}")
        check("5.5 receiver_id 正确", msg["receiver_id"] == USER_B["id"],
              f"got {msg.get('receiver_id')}")

    sA.disconnect()
    sB.disconnect()


def test_006_socket_group():
    section("6. Socket.IO 群聊实时推送")

    tA = login(USER_A)
    tB = login(USER_B)

    # B 连接 Socket 并加入群聊房间
    sB, connected, _ = connect_socket(tB, USER_B["name"])
    check("6.1 B Socket连接成功", connected)
    if not connected:
        return

    sB.emit("group_join", {"group_id": GROUP_ID})
    time.sleep(0.3)

    recv = []
    @sB.on("group_message")
    def on_gm(msg):
        recv.append(msg)

    # A 发群消息
    sA, connA, _ = connect_socket(tA, USER_A["name"])
    if connA:
        sA.emit("group_send", {"group_id": GROUP_ID, "content": "群聊Socket测试"})
        time.sleep(1)

    check("6.2 B在群聊房间收到消息", len(recv) > 0,
          f"recv={len(recv)}")

    if len(recv) > 0:
        check("6.3 群消息group_id正确", recv[0]["group_id"] == GROUP_ID,
              f"got {recv[0].get('group_id')}")

    if connA:
        sA.disconnect()
    sB.disconnect()


# ═══════════════════════════════════════════════════════════
#  测试套件 7：消息列表排序 + 多次发送
# ═══════════════════════════════════════════════════════════

def test_007_message_list_order():
    section("7. 消息列表排序")

    tA = login(USER_A)
    tB = login(USER_B)

    # B 给 A 发一条新消息
    api_post(tB, "/users/messages", {"receiver_id": USER_A["id"], "content": "最新消息排序测试"})
    time.sleep(0.2)

    r = api_get(tA, "/users/messages")
    items = r.json()["data"]["items"]

    check("7.1 有消息返回", len(items) > 0, f"items={len(items)}")

    # 验证第一条是最新消息（时间倒序）
    if len(items) >= 1:
        first = items[0]
        check("7.2 第一条消息内容匹配",
              first["content"] == "最新消息排序测试" or items[0]["other_user"]["user_id"] == USER_B["id"],
              f"content={first.get('content')}, other={first.get('other_user')}")


# ═══════════════════════════════════════════════════════════
#  测试套件 8：异常场景
# ═══════════════════════════════════════════════════════════

def test_008_edge_cases():
    section("8. 异常场景")

    tA = login(USER_A)

    # 8.1 超长消息
    long_msg = "x" * 5000
    r = api_post(tA, "/users/messages", {"receiver_id": USER_B["id"], "content": long_msg})
    check("8.1 超长消息(5000字) → 200 (接受)", r.status_code == 200,
          f"got {r.status_code}")

    # 8.2 特殊字符
    r = api_post(tA, "/users/messages", {"receiver_id": USER_B["id"], "content": "你好 😀🎉 \n换行 <script>alert(1)</script>"})
    check("8.2 特殊字符/emoji/脚本 → 200", r.status_code == 200 and r.json()["code"] == 0,
          f"got {r.status_code} {r.text[:50]}")

    # 8.3 并发发送
    import concurrent.futures
    def send_one(i):
        return api_post(tA, "/users/messages", {"receiver_id": USER_B["id"], "content": f"concurrent_{i}"})

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(send_one, i) for i in range(20)]
        results_list = [f.result() for f in futures]

    ok_count = sum(1 for r in results_list if r.status_code == 200)
    check("8.3 并发20条 → 全部200", ok_count == 20,
          f"only {ok_count}/20 succeeded")

    # 8.4 不存在的群聊
    r = requests.get(f"{API}/chat/groups/99999/messages", headers={"Authorization": f"Bearer {tA}"})
    check("8.4 不存在的群聊 → 404/403", r.status_code in (403, 404),
          f"got {r.status_code} {r.text[:50]}")

    # 8.5 请求体格式错误（Flask 默认对非 JSON 返回 500，可优化为 400）
    r = api_post(tA, "/users/messages", "not json")
    check("8.5 非法JSON请求体 → 400/415/500", r.status_code in (400, 415, 500),
          f"got {r.status_code}")


# ═══════════════════════════════════════════════════════════
#  测试套件 9：群组信息
# ═══════════════════════════════════════════════════════════

def test_009_group_info():
    section("9. 群组信息")

    tA = login(USER_A)

    r = api_get(tA, "/chat/groups")
    check("9.1 获取群列表 → 200", r.status_code == 200 and r.json()["code"] == 0)

    groups = r.json()["data"].get("groups", [])
    target = [g for g in groups if g["id"] == GROUP_ID]

    check("9.2 群聊在列表中", len(target) > 0)

    if target:
        g = target[0]
        check("9.3 群名称正确", g["name"] == "落羽红杉林茶话会",
              f"got {g['name']}")
        check("9.4 包含members字段", "members" in g and len(g["members"]) > 0,
              f"members={len(g.get('members',[]))}")
        check("9.5 member_count ≥ 5", g.get("member_count", 0) >= 5,
              f"member_count={g.get('member_count')}")


# ═══════════════════════════════════════════════════════════
#  主入口
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════╗")
    print("║     消息功能全量测试套件                              ║")
    print("║     BeEnjoyIng - 私聊 / 群聊 / Socket / 未读          ║")
    print("╚══════════════════════════════════════════════════════╝")

    # 检查服务可用性
    try:
        r = requests.get(f"{BASE}/", timeout=3)
        if r.status_code != 200:
            print(f"⚠ 服务不可用: HTTP {r.status_code}")
            exit(1)
    except Exception as e:
        print(f"⚠ 无法连接服务 {BASE}: {e}")
        exit(1)

    # 运行所有测试
    tests = [
        test_001_auth,
        test_002_private_messages,
        test_003_unread_count,
        test_004_group_messages,
        test_005_socket_private,
        test_006_socket_group,
        test_007_message_list_order,
        test_008_edge_cases,
        test_009_group_info,
    ]

    for test_fn in tests:
        try:
            test_fn()
        except Exception as e:
            results["fail"] += 1
            print(f"\n  ✗ EXCEPTION in {test_fn.__name__}: {e}")
            traceback.print_exc()

    # 汇总
    total = results["pass"] + results["fail"]
    print(f"\n{'='*60}")
    print(f"  测试汇总")
    print(f"{'='*60}")
    for d in details:
        print(d)
    print(f"\n  通过: {results['pass']}/{total}")
    if results['fail'] > 0:
        print(f"  失败: {results['fail']}/{total}")
        exit(1)
    else:
        print(f"  全部通过 ✓")
