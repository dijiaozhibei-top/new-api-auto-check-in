import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Optional


BASE_URL = os.environ.get("NEW_API_BASE_URL") or "https://ai.dtony.org"
ACCOUNTS_FILE = os.environ.get("ACCOUNTS_FILE") or "DTony API.txt"
REQUEST_TIMEOUT = 15
REQUEST_DELAY = 1.5


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


def login(session: requests.Session, username: str, password: str) -> Optional[int]:
    try:
        resp = session.post(
            f"{BASE_URL}/api/user/login",
            json={"username": username, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 429:
            print(f"    [WARN] 请求过于频繁，等待 30 秒后重试...")
            time.sleep(30)
            return login(session, username, password)
        data = resp.json()
        if data.get("success") and data.get("data", {}).get("id"):
            return data["data"]["id"]
        return None
    except requests.RequestException:
        return None


def has_checked_in(session: requests.Session, user_id: int) -> bool:
    try:
        month = datetime.now().strftime("%Y-%m")
        resp = session.get(
            f"{BASE_URL}/api/user/checkin?month={month}",
            headers={"New-API-User": str(user_id)},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 429:
            print(f"    [WARN] 请求过于频繁，等待 30 秒后重试...")
            time.sleep(30)
            return has_checked_in(session, user_id)
        data = resp.json()
        if data.get("success"):
            stats = data.get("data", {}).get("stats", {})
            return stats.get("checked_in_today", False)
        return False
    except requests.RequestException:
        return False


def do_checkin(session: requests.Session, user_id: int) -> Optional[int]:
    try:
        resp = session.post(
            f"{BASE_URL}/api/user/checkin",
            headers={
                "New-API-User": str(user_id),
                "Content-Type": "application/json",
            },
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 429:
            print(f"    [WARN] 请求过于频繁，等待 30 秒后重试...")
            time.sleep(30)
            return do_checkin(session, user_id)
        data = resp.json()
        if data.get("success"):
            return data.get("data", {}).get("quota_awarded", 0)
        return None
    except requests.RequestException:
        return None


def main():
    print("=" * 60)
    print(f"New API 自动签到工具")
    print(f"站点: {BASE_URL}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    accounts = read_accounts(ACCOUNTS_FILE)
    if not accounts:
        print("[ERROR] 未读取到任何账号，请检查账号文件")
        sys.exit(1)

    print(f"共读取到 {len(accounts)} 个账号\n")

    success_count = 0
    fail_count = 0
    already_checked = 0
    results = []

    for idx, username in enumerate(accounts, 1):
        password = username
        print(f"[{idx}/{len(accounts)}] 正在处理: {username}")

        session = requests.Session()
        user_id = login(session, username, password)
        if user_id is None:
            fail_count += 1
            results.append({"username": username, "status": "login_failed"})
            print(f"    [FAIL] 账号不可用（登录失败）")
            time.sleep(REQUEST_DELAY)
            continue

        if has_checked_in(session, user_id):
            print(f"    [SKIP] 今日已签到，跳过")
            already_checked += 1
            results.append({"username": username, "status": "already_checked_in"})
            time.sleep(REQUEST_DELAY)
            continue

        awarded = do_checkin(session, user_id)
        if awarded is not None:
            print(f"    [OK]   签到成功 +{awarded} 额度")
            success_count += 1
            results.append(
                {"username": username, "status": "success", "quota_awarded": awarded}
            )
        else:
            fail_count += 1
            results.append({"username": username, "status": "checkin_failed"})
            print(f"    [FAIL] 签到失败")
        time.sleep(REQUEST_DELAY)

    print("\n" + "=" * 60)
    print(f"签到完成！结果统计:")
    print(f"  成功签到: {success_count}")
    print(f"  今日已签到: {already_checked}")
    print(f"  失败: {fail_count}")
    print(f"  总计: {len(accounts)}")
    print("=" * 60)

    summary_path = "checkin_result.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "time": datetime.now().isoformat(),
                "total": len(accounts),
                "success": success_count,
                "already_checked_in": already_checked,
                "failed": fail_count,
                "results": results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"详细结果已保存至: {summary_path}")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
