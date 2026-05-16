# New API Auto Check-in

New API 每日自动批量签到工具。支持多账号并发签到、API Key 自动收集、汇总报告。

## 功能

- 批量签到多个 New API 站点账号
- 自动检测今日是否已签到（避免重复）
- 自动收集/创建各账号的 API Key
- 多 Actions 并行执行（每个独立 IP，绕过登录频率限制）
- 生成 HTML 汇总报告
- 通过 GitHub Actions 定时自动运行

## 快速开始

### 1. Fork 此仓库

点击右上角 Fork 按钮。

### 2. 配置 Secrets

在仓库 **Settings → Secrets and variables → Actions** 添加：

| Secret | 说明 |
|--------|------|
<<<<<<< HEAD
| `ACCOUNTS_DATA` | 账号列表，每行一个用户名（密码与用户名相同） |
=======
| `ACCOUNTS_DATA` | 账号列表，每行一丬用户名（密码与用户名相同） |
>>>>>>> da3e0f309c019f5b5fc5801d76f8ed4b595d0cd2
| `NEW_API_BASE_URL` | New API 站点地址（默认 `https://ai.dtony.org`） |

### 3. 手动触发

进入 **Actions → Daily Check-in → Run workflow** 即可触发签到。

### 4. 查看报告

运行完成后，在 Action 页面底部 **Artifacts** 区域下载 `checkin-summary`，解压后打开 HTML 即可看到完整报告（含签到结果 + API Key 列表）。

### 5. 自动运行

默认每天 **UTC 22:00（北京时间 06:00）** 自动执行。

## 本地运行

```bash
pip install -r requirements.txt
echo "username1" > "DTony API.txt"
python checkin.py
```

## 项目结构

```
├── .github/workflows/checkin.yml   # GitHub Actions 配置
├── checkin.py                       # 主签到脚本
├── merge_reports.py                 # 汇总报告生成脚本
├── requirements.txt                 # Python 依赖
└── DTony API.txt                    # 本地账号文件（已加入 .gitignore）
```

## 注意事项

- `DTony API.txt` 已加入 `.gitignore`，不会上传到仓库
- 账号密码需与用户名相同
<<<<<<< HEAD
- 部分账号可能不可用，脚本会自动跳过
=======
- 部分账号可胹不可用，脚本会自动跳过
>>>>>>> da3e0f309c019f5b5fc5801d76f8ed4b595d0cd2
