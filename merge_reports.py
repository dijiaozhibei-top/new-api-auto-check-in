import os, re, glob
from datetime import datetime

files = sorted(glob.glob("checkin_report_*.html") + glob.glob("checkin_result.html"))

all_rows = ""
total_success = 0
total_skipped = 0
total_failed = 0
total_all = 0

for fname in files:
    content = open(fname, "r", encoding="utf-8").read()
    rows = re.findall(r"<tr>(.*?)</tr>", content, re.DOTALL)
    for row in rows:
        cols = re.findall(r"<td>(.*?)</td>", row)
        if len(cols) >= 3:
            username, badge, detail = cols[0], cols[1], cols[2]
            all_rows += (
                f"<tr><td>{username}</td><td>{badge}</td><td>{detail}</td></tr>\n"
            )
            if "22c55e" in badge:
                total_success += 1
            elif "3b82f6" in badge:
                total_skipped += 1
            else:
                total_failed += 1
        total_all += 1

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

SUCCESS = total_success
SKIPPED = total_skipped
FAILED = total_failed
TOTAL = total_all

html = f"""<!DOCTYPE html>
<html lang="zh">
<head><meta charset="utf-8"><title>New API Check-in Summary</title></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f5f5;margin:20px">
<div style="max-width:900px;margin:auto;background:white;border-radius:12px;padding:24px;box-shadow:0 1px 3px rgba(0,0,0,.1)">
<h2 style="margin-top:0">New API Check-in Summary</h2>
<p style="color:#666;font-size:14px">Generated at: {now}</p>
<div style="display:flex;gap:16px;margin:20px 0">
  <div style="flex:1;background:#f0fdf4;border-radius:8px;padding:16px;text-align:center"><div style="font-size:24px;font-weight:bold;color:#16a34a">{SUCCESS}</div><div style="font-size:12px;color:#666">Success</div></div>
  <div style="flex:1;background:#eff6ff;border-radius:8px;padding:16px;text-align:center"><div style="font-size:24px;font-weight:bold;color:#2563eb">{SKIPPED}</div><div style="font-size:12px;color:#666">Already Checked</div></div>
  <div style="flex:1;background:#fef2f2;border-radius:8px;padding:16px;text-align:center"><div style="font-size:24px;font-weight:bold;color:#dc2626">{FAILED}</div><div style="font-size:12px;color:#666">Failed / Rate Limited</div></div>
  <div style="flex:1;background:#fafafa;border-radius:8px;padding:16px;text-align:center"><div style="font-size:24px;font-weight:bold;color:#525252">{TOTAL}</div><div style="font-size:12px;color:#666">Total</div></div>
</div>
<table style="width:100%;border-collapse:collapse;font-size:13px">
<thead><tr style="background:#fafafa"><th style="text-align:left;padding:8px 12px;border-bottom:2px solid #e5e5e5">Account</th><th style="text-align:left;padding:8px 12px;border-bottom:2px solid #e5e5e5">Status</th><th style="text-align:left;padding:8px 12px;border-bottom:2px solid #e5e5e5">Detail</th></tr></thead>
<tbody>{all_rows}</tbody>
</table>
</div></body></html>"""

with open("checkin_summary.html", "w", encoding="utf-8") as f:
    f.write(html)
print(f"Summary: {SUCCESS} success, {SKIPPED} skipped, {FAILED} failed, total {TOTAL}")
