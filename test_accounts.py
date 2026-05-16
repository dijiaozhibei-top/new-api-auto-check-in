import os, requests, time, sys

BASE_URL = "https://ai.dtony.org"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

suspicious = [
    "mkntki2go6rv",
    "mkntxtlxdmlu",
    "mknuqiu8d3xf",
    "mknuzhqwt286",
    "mknv8i93j9px",
    "mknvfs0zgda5",
    "mknvy0ircq3l",
    "mknwcwsjfbu1",
    "mknwy2ibti7u",
    "mknx4106kkkm",
    "mknxa0bl71lq",
    "mknxg0b1mvmr",
    "mknxly2qr2mn",
    "mknxtmh002oj",
    "mknxzlayk8fg",
    "mko0qxfafe9c",
    "mko0t5jcihng",
    "mko0v9f2kep2",
    "mko0xe8dpb7w",
    "mko0zj8f2lpy",
    "mko11nq8m8og",
    "mko13u2x12pg",
    "mko15yk2zrtm",
    "mko1a92trx2r",
    "mko1ejrf3reb",
    "mko1gojmqf6v",
    "mko1iszmc4kx",
    "mko1kykhu0pc",
    "mko1n2po85mc",
    "mko1p6sz34tu",
    "mko1rboi2uhw",
    "mko1tg1vkz8u",
    "mko1vjxs2q3a",
    "mko1xo08xwsp",
    "mko202430i6g",
    "mko241b913fo",
    "mko265cg4fw6",
    "mko28aknv5ah",
    "mko2aexledw1",
    "mko2cjc3wuue",
    "mkoufd3r5d45",
    "mkouhm5xdvij",
    "mkoujta38xsy",
    "mkoulyp003ws",
    "mkouo3y8ejzg",
]

results = []
oks = 0
fails = 0
consec_fails = 0
max_consec_fails = 0
consec_oks = 0
max_consec_oks = 0

for i, u in enumerate(suspicious, 1):
    try:
        session = requests.Session()
        r = session.post(
            f"{BASE_URL}/api/user/login",
            json={"username": u, "password": u},
            headers={"User-Agent": UA, "Content-Type": "application/json"},
            timeout=(5, 10),
        )
        if r.status_code == 429:
            print(f"[{i:2d}/45] {u}: 429 RATE LIMITED - STOP")
            fails += 1
            consec_fails += 1
            if consec_fails > max_consec_fails:
                max_consec_fails = consec_fails
            consec_oks = 0
            remaining = len(suspicious) - i
            fails += remaining
            results.append((u, "429"))
            for j in range(i, len(suspicious)):
                results.append((suspicious[j], "429_skip"))
                print(f"[{j + 1:2d}/45] {suspicious[j]}: 跳过（限流）")
            break
        data = r.json() if r.text.strip() else {}
        if data.get("success") and data.get("data", {}).get("id"):
            print(f"[{i:2d}/45] {u}: OK (uid={data['data']['id']})")
            results.append((u, "ok"))
            oks += 1
            consec_fails = 0
            consec_oks += 1
            if consec_oks > max_consec_oks:
                max_consec_oks = consec_oks
        else:
            msg = data.get("message", r.text[:80])
            print(f"[{i:2d}/45] {u}: FAIL - {msg}")
            results.append((u, f"fail: {msg}"))
            fails += 1
            consec_oks = 0
            consec_fails += 1
            if consec_fails > max_consec_fails:
                max_consec_fails = consec_fails
    except Exception as e:
        print(f"[{i:2d}/45] {u}: ERROR - {e}")
        results.append((u, f"error: {e}"))
        fails += 1
        consec_oks = 0

    time.sleep(8)

print()
print("=" * 60)
print("TEST RESULTS SUMMARY")
print("=" * 60)
print(f"OK: {oks}  |  FAIL: {fails}")
print(
    f"Max consecutive OK: {max_consec_oks}  |  Max consecutive FAIL: {max_consec_fails}"
)
print("=" * 60)

if fails:
    print(f"\nFailed accounts ({fails}):")
    for u, st in results:
        if st != "ok":
            print(f"  {u:<20} {st}")

step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
if step_summary:
    with open(step_summary, "a", encoding="utf-8") as f:
        f.write(f"## Test Suspicious Accounts\n\n")
        f.write(f"OK: {oks} | Fail: {fails}\n\n")
        f.write(
            f"Max consecutive OK: {max_consec_oks} | Max consecutive FAIL: {max_consec_fails}\n\n"
        )
        for u, st in results:
            emoji = "✅" if st == "ok" else "❌" if st.startswith("fail") else "⏭"
            f.write(f"- {emoji} {u}: {st}\n")
