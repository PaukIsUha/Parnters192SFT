

import requests
from configs import GSHEET_CONFIGS, SpyLogBID
import xrequests as db
from apscheduler.schedulers.blocking import BlockingScheduler


def send_to_apps_script(date_str: str, started: int, registered: int, clicks_arr: list) -> None:
    payload = {
        "date": date_str,
        "users_started": started,
        "users_registered": registered,
    }

    for click_group, click_count in clicks_arr:
        payload[SpyLogBID[click_group]] = click_count

    r = requests.post(GSHEET_CONFIGS.link, json=payload, timeout=10, allow_redirects=False)
    if r.status_code not in (200, 302):
        r.raise_for_status()

# ---------------------------------------------------------------
#  Job
# ---------------------------------------------------------------


def push_yesterday() -> None:
    day = db._yesterday()
    started = db.get_yesterday_users_started()
    registered = db.get_yesterday_users_registered()
    clicks = db.get_today_clicks_by_button()
    send_to_apps_script(day.isoformat(), started, registered, clicks)
    print(f"[✓] {day}: started={started}, registered={registered}")

# ---------------------------------------------------------------
#  Entrypoint
# ---------------------------------------------------------------


def main() -> None:
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "once":
        push_yesterday()
        return

    sched = BlockingScheduler(timezone=db.PARIS)
    # 00:05 Moscow/Paris (UTC+3) daily
    sched.add_job(push_yesterday, "cron", hour=0, minute=5)
    print("Sync daily‑stats service started … (Ctrl‑C to stop)")
    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == "__main__":
    main()
