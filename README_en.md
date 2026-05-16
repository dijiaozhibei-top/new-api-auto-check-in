# New API Auto Check-in

Daily batch check-in tool for New API sites. Supports multi-account concurrent check-in, automatic API key collection, and summary reports.

## Features

- Batch check-in for multiple New API accounts
- Auto-detect today's check-in status (avoid duplicates)
- Auto-collect/create API keys for each account
- Parallel execution via GitHub Actions matrix strategy (independent IPs, bypass rate limits)
- Generate HTML summary report
- Scheduled daily execution via GitHub Actions

## Quick Start

### 1. Fork this repo

Click the Fork button on the top right.

### 2. Configure Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|--------|-------------|
| `ACCOUNTS_DATA` | Account list, one username per line (password = username) |
| `NEW_API_BASE_URL` | New API site URL (default `https://ai.dtony.org`) |

### 3. Manual Trigger

Go to **Actions → Daily Check-in → Run workflow**.

### 4. View Report

After completion, download `checkin-summary` from the **Artifacts** section at the bottom of the Action page. Extract the zip and open the HTML file to see the full report (check-in results + API keys).

### 5. Scheduled Run

Runs daily at **UTC 22:00 (Beijing 06:00)** by default.

## Run Locally

```bash
pip install -r requirements.txt
echo "username1" > "DTony API.txt"
python checkin.py
```

## Project Structure

```
├── .github/workflows/checkin.yml   # GitHub Actions workflow
├── checkin.py                       # Main check-in script
├── merge_reports.py                 # Summary report generator
├── requirements.txt                 # Python dependencies
└── DTony API.txt                    # Local account file (in .gitignore)
```

## Notes

- `DTony API.txt` is in `.gitignore` and will not be uploaded
- Account password must be same as username
- Some accounts may be invalid; the script will skip them automatically
