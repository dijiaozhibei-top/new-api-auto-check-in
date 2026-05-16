import os
import sys
import json
import time
import requests
from datetime import datetime


BASE_URL = os.environ.get("NEW_API_BASE_URL") or "https://ai.dtony.org"
ACCOUNTS_FILE = os.environ.get("ACCOUNTS_FILE") or "DTony API.txt"
BATCH_TOTAL = int(os.environ.get("BATCH_TOTAL") or "1")
BATCH_INDEX = int(os.environ.get("BATCH_INDEX") or "0")
TIMEOUT = (3, 5)
DELAY = 3

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


def read_accounts(file_path: str) -> list[str]:
    env_data = os.environ.get("ACCOUNTS_DATA")
    if env_data:
        accounts = []
        for line in env_data.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            accounts.append(line.split(None, 1)[-1].strip())
        return accounts
    accounts = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(None, 1)
                if len(parts) >= 1:
                    username = parts[-1].strip()
                    if username and not username.startswith("#"):
                        accounts.append(username)
    except FileNotFoundError:
        print(f"[ERROR] 账号文件不存在: {file_path}")
    return accounts


def post_json(session, url, data, headers=None):
    h = {
        "User-Agent": UA,
        "Accept": "application/json",
        **({"Content-Type": "application/json"} if isinstance(data, dict) else {}),
    }
    if headers:
        h.update(headers)
    return session.post(
        url,
        json=data if isinstance(data, dict) else None,
        data=data if isinstance(data, str) else None,
        headers=h,
        timeout=TIMEOUT,
    )


def get_json(session, url, headers=None):
    h = {"User-Agent": UA, "Accept": "application/json"}
    if headers:
        h.update(headers)
    return session.get(url, headers=h, timeout=TIMEOUT)


def main():
    print("=" * 60)
    print("New API 自动签到工具")
    print(f"站点: {BASE_URL}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    accounts = read_accounts(ACCOUNTS_FILE)
    if not accounts:
        print("[ERROR] 未读取到任何账号")
        sys.exit(1)

    if BATCH_TOTAL > 1:
        batch_size = (len(accounts) + BATCH_TOTAL - 1) // BATCH_TOTAL
        start = BATCH_INDEX * batch_size
        end = min(start + batch_size, len(accounts))
        accounts = accounts[start:end]
        print(f"批次 {BATCH_INDEX + 1}/{BATCH_TOTAL}，处理账号 {start + 1}-{end}\n")

    print(f"共读取到 {len(accounts)} 个账号\n")

    session = requests.Session()
    results = []
    success_count = 0
    fail_count = 0
    already_checked = 0
    total = len(accounts)

    for idx, username in enumerate(accounts, 1):
        status = "login_failed"
        msg = ""
        awarded = None
        quota_after = None

        try:
            resp = post_json(
                session,
                f"{BASE_URL}/api/user/login",
                {"username": username, "password": username},
            )
            if resp.status_code == 429:
                print(
                    f"  [STOP] [{idx}/{total}] {username}: 达到每日登录上限（429），跳过剩下的账号"
                )
                remaining = total - idx + 1
                fail_count += remaining
                for i in range(remaining):
                    rest_name = accounts[idx - 1 + i]
                    results.append(
                        {
                            "username": rest_name,
                            "status": "rate_limited",
                            "msg": "每日登录上限 429",
                        }
                    )
                break
            data = resp.json() if resp.text.strip() else {}
            if data.get("success") and data.get("data", {}).get("id"):
                uid = data["data"]["id"]

                month = datetime.now().strftime("%Y-%m")
                resp2 = get_json(
                    session,
                    f"{BASE_URL}/api/user/checkin?month={month}",
                    {"New-API-User": str(uid)},
                )
                d2 = resp2.json() if resp2.text.strip() else {}
                if d2.get("success") and d2.get("data", {}).get("stats", {}).get(
                    "checked_in_today", False
                ):
                    status = "already_checked_in"
                    r3 = get_json(
                        session, f"{BASE_URL}/api/user/self", {"New-API-User": str(uid)}
                    )
                    d3 = r3.json() if r3.text.strip() else {}
                    if d3.get("success"):
                        quota_after = d3["data"].get("quota", 0)
                else:
                    resp4 = post_json(
                        session,
                        f"{BASE_URL}/api/user/checkin",
                        "",
                        {"New-API-User": str(uid)},
                    )
                    d4 = resp4.json() if resp4.text.strip() else {}
                    if d4.get("success"):
                        awarded = d4.get("data", {}).get("quota_awarded", 0)
                        status = "success"
                        r5 = get_json(
                            session,
                            f"{BASE_URL}/api/user/self",
                            {"New-API-User": str(uid)},
                        )
                        d5 = r5.json() if r5.text.strip() else {}
                        if d5.get("success"):
                            quota_after = d5["data"].get("quota", 0)
                    else:
                        msg = d4.get("message", "") or f"HTTP {resp4.status_code}"
                        status = "checkin_failed"
            else:
                status_code = resp.status_code
                msg = data.get("message", "") or (
                    f"HTTP {status_code}"
                    if status_code != 200
                    else f"响应: {resp.text[:100]}"
                )
        except Exception as e:
            msg = f"{type(e).__name__}: {str(e)[:80]}"

        result = {"username": username, "status": status, "msg": msg}
        if awarded is not None:
            result["awarded"] = awarded
        if quota_after is not None:
            result["quota"] = quota_after
        results.append(result)

        time.sleep(DELAY)

        if status == "success":
            print(
                f"  [OK]   [{idx}/{total}] {username}: 签到成功 +{awarded}，当前 {quota_after}"
            )
            success_count += 1
        elif status == "already_checked_in":
            q = f"，当前 {quota_after}" if quota_after else ""
            print(f"  [SKIP] [{idx}/{total}] {username}: 今日已签到{q}")
            already_checked += 1
        else:
            print(f"  [FAIL] [{idx}/{total}] {username}: {msg}")
            fail_count += 1

    print(f"\n{'=' * 60}")
    print(f"签到完成！")
    print(f"  成功签到: {success_count}")
    print(f"  今日已签到: {already_checked}")
    print(f"  失败: {fail_count}")
    print(f"  总计: {total}")
    print(f"{'=' * 60}")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = ""
    for r in results:
        u, st = r["username"], r["status"]
        if st == "success":
            badge = '<span style="background:#22c55e;color:white;padding:2px 8px;border-radius:4px;font-size:12px">成功</span>'
            detail = f"签到 +{r['awarded']}，当前 {r['quota']}"
        elif st == "already_checked_in":
            badge = '<span style="background:#3b82f6;color:white;padding:2px 8px;border-radius:4px;font-size:12px">已签到</span>'
            detail = f"当前额度 {r['quota']}" if r.get("quota") else ""
        elif st == "rate_limited":
            badge = '<span style="background:#f59e0b;color:white;padding:2px 8px;border-radius:4px;font-size:12px">限流跳过</span>'
            detail = r.get("msg", "")
        else:
            badge = '<span style="background:#ef4444;color:white;padding:2px 8px;border-radius:4px;font-size:12px">失败</span>'
            detail = r.get("msg", "")
        rows += f"<tr><td>{u}</td><td>{badge}</td><td>{detail}</td></tr>\n"

    html = f"""<!DOCTYPE html>
<html lang="zh">
<head><meta charset="utf-8"><title>New API 签到报告</title></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f5f5;margin:20px">
<div style="max-width:800px;margin:auto;background:white;border-radius:12px;padding:24px;box-shadow:0 1px 3px rgba(0,0,0,.1)">
<h2 style="margin-top:0">New API 自动签到报告</h2>
<p style="color:#666;font-size:14px">站点: {BASE_URL} | 时间: {now}</p>
<div style="display:flex;gap:16px;margin:20px 0">
  <div style="flex:1;background:#f0fdf4;border-radius:8px;padding:16px;text-align:center"><div style="font-size:24px;font-weight:bold;color:#16a34a">{success_count}</div><div style="font-size:12px;color:#666">签到成功</div></div>
  <div style="flex:1;background:#eff6ff;border-radius:8px;padding:16px;text-align:center"><div style="font-size:24px;font-weight:bold;color:#2563eb">{already_checked}</div><div style="font-size:12px;color:#666">今日已签到</div></div>
  <div style="flex:1;background:#fef2f2;border-radius:8px;padding:16px;text-align:center"><div style="font-size:24px;font-weight:bold;color:#dc2626">{fail_count}</div><div style="font-size:12px;color:#666">失败</div></div>
  <div style="flex:1;background:#fafafa;border-radius:8px;padding:16px;text-align:center"><div style="font-size:24px;font-weight:bold;color:#525252">{total}</div><div style="font-size:12px;color:#666">总计</div></div>
</div>
<table style="width:100%;border-collapse:collapse;font-size:13px">
<thead><tr style="background:#fafafa"><th style="text-align:left;padding:8px 12px;border-bottom:2px solid #e5e5e5">账号</th><th style="text-align:left;padding:8px 12px;border-bottom:2px solid #e5e5e5">状态</th><th style="text-align:left;padding:8px 12px;border-bottom:2px solid #e5e5e5">详情</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</div></body></html>"""

    out_name = f"checkin_report_{BATCH_INDEX}.html"
    with open(out_name, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"报告已保存至: {out_name}")

    sys.exit(0)


if __name__ == "__main__":
    main()
