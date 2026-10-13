# AFIT hostel checker

Logs into the AFIT student portal, counts open beds per hostel, and pings you
(the phone) when a bed opens. Alerts go out through **ntfy.sh** or **CallMeBot
WhatsApp**.

## Files

| File | Purpose |
| --- | --- |
| `hostel_check.py` | The checker |
| `requirements.txt` | Dependencies |
| `.github/workflows/hostel-check.yml` | Runs the check every 10 minutes |

## Test locally (no credentials needed)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python hostel_check.py --html-file tests\sample.html
```

That prints the parsed hostels and bed counts, so you can confirm the parsers
work before touching the real site.

## Run for real, locally

Credentials live in `.env` (gitignored). Fill it in, then use the helper, which
loads `.env` and runs the checker with any args you pass. Start with
`--dry-run` (does everything except send the alert):

```powershell
.\run_local.ps1 --dry-run
```

Drop `--dry-run` once the output looks right and you want a real ping.

## Alert setup (ntfy.sh)

1. Install the **ntfy** app (Android/iOS) or open `https://ntfy.sh/<topic>` in a
   browser.
2. Subscribe to your topic - a long random name, e.g.
   `afit-hostel-4fe7412d30ca3f9ee4d79922`. Anyone who knows the topic can read
   it, so keep it random.
3. Set `NTFY_TOPIC` in `.env` locally and as a GitHub **Secret** for Actions
   (settings -> Secrets and variables -> Actions -> New repository secret).

> WhatsApp via CallMeBot still works if you set `WA_PHONE` +
> `CALLMEBOT_APIKEY` instead - it takes priority when set.

## GitHub Actions

1. Push this folder to a **private** repo.
2. Repo -> Settings -> Secrets and variables -> Actions -> add `AFIT_EMAIL`,
   `AFIT_PASSWORD`, and `NTFY_TOPIC` (or the WhatsApp pair).
3. Actions tab -> **AFIT hostel check** -> **Run workflow** to test once.
4. It then runs on schedule every 10 minutes.

### Things to know

- GitHub cron is UTC and **best-effort** - runs can be delayed a few minutes
  or skipped under load. "Every 10 min" is approximate.
- Scheduled workflows are **disabled after 60 days** with no repo activity.
  Push a commit now and then to keep it alive.
- A cloud IP logging into the portal every 10 minutes may eventually get
  rate-limited or blocked. Watch the Actions log for login failures.
- Each run is independent, so while a bed is open you'll get a ping **every
  10 minutes** until it's taken. Ask if you want change-only alerts.
