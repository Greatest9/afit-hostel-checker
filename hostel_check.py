"""Check the AFIT hostel booking page and alert you when a bed opens.

Env vars:
  AFIT_EMAIL, AFIT_PASSWORD   portal login (required)
Alert (set ONE pair):
  WA_PHONE, CALLMEBOT_APIKEY  WhatsApp via CallMeBot (phone with country code, e.g. +234...)
  NTFY_TOPIC                  or ntfy.sh push (use a long random topic name)

Test the parsers without logging in:
  python hostel_check.py --html-file saved_page.html

Run the full flow but don't send anything:
  python hostel_check.py --dry-run
"""
import argparse
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

BASE = "https://student.afit.edu.ng/portal/public/"
HOSTEL_URL = BASE + "student/hostel_booking"


def parse_hostels(html):
    """Return [(hostel_id, name, exhausted)] from the tab pills at the top of the page."""
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for a in soup.select("ul.nav-pills a.nav-link"):
        m = re.search(r"hostel_id=(\d+)", a.get("href", ""))
        if not m:
            continue
        badge = a.select_one(".badge")
        exhausted = bool(badge and "exhausted" in badge.get_text(strip=True).lower())
        name = a.get_text(" ", strip=True)
        if badge:
            name = name.replace(badge.get_text(strip=True), "").strip()
        out.append((m.group(1), name, exhausted))
    return out


def count_beds(html):
    """Return (available, held, occupied) for the hostel grid on this page."""
    soup = BeautifulSoup(html, "html.parser")
    available = held = occupied = 0
    for b in soup.select("button.bed-btn"):
        classes = b.get("class", [])
        if "bg-seat-occupied" in classes:
            occupied += 1
        elif "bg-seat-held" in classes:
            held += 1
        elif not b.has_attr("disabled"):
            available += 1
        else:
            held += 1  # disabled but not marked occupied: treat as locked
    return available, held, occupied


def login(session, email, password):
    r = session.post(
        BASE + "login_process.php",
        data={"email": email, "password": password},
        timeout=30,
    )
    r.raise_for_status()
    r = session.get(HOSTEL_URL, timeout=30)
    r.raise_for_status()
    if "Sign In to Portal" in r.text or "/login" in r.url:
        sys.exit("Login failed: got the login page back. Check the secrets.")
    return r.text


def notify(title, message):
    if os.environ.get("CALLMEBOT_APIKEY"):
        r = requests.get(
            "https://api.callmebot.com/whatsapp.php",
            params={
                "phone": os.environ["WA_PHONE"],
                "text": f"{title}\n{message}\n{HOSTEL_URL}",
                "apikey": os.environ["CALLMEBOT_APIKEY"],
            },
            timeout=30,
        )
        print("whatsapp:", r.status_code)
        return
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        sys.exit("Set NTFY_TOPIC (or CALLMEBOT_APIKEY + WA_PHONE) so the alert has somewhere to go.")
    requests.post(
        f"https://ntfy.sh/{topic}",
        data=message.encode("utf-8"),
        headers={"Title": title, "Priority": "high", "Click": HOSTEL_URL},
        timeout=30,
    )


def main():
    parser = argparse.ArgumentParser(description="Check AFIT hostel for open beds.")
    parser.add_argument("--html-file", help="Parse a saved HTML file instead of logging in (offline test).")
    parser.add_argument("--dry-run", action="store_true", help="Do everything except sending the alert.")
    parser.add_argument("--test-alert", action="store_true", help="Send one test alert and exit.")
    args = parser.parse_args()

    if args.test_alert:
        notify("AFIT hostel checker test", "If you can read this, ntfy alerts work.")
        print("Test alert sent.")
        return

    if args.html_file:
        with open(args.html_file, encoding="utf-8") as f:
            html = f.read()
        print("hostels:", parse_hostels(html))
        print("beds: available=%d held=%d occupied=%d" % count_beds(html))
        return

    email = os.environ.get("AFIT_EMAIL")
    password = os.environ.get("AFIT_PASSWORD")
    if not email or not password:
        sys.exit("Set AFIT_EMAIL and AFIT_PASSWORD first.")

    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0"
    first_page = login(s, email, password)

    hostels = parse_hostels(first_page)
    if not hostels:
        sys.exit("No hostel tabs found. The page layout may have changed.")

    open_lines = []
    for hid, name, exhausted in hostels:
        html = s.get(f"{HOSTEL_URL}?hostel_id={hid}", timeout=30).text
        avail, held, occ = count_beds(html)
        print(f"{name} (id {hid}): exhausted_badge={exhausted} available={avail} held={held} occupied={occ}")
        if avail > 0:
            open_lines.append(f"{name}: {avail} bed(s) available")
        elif not exhausted:
            open_lines.append(f"{name}: no longer marked Exhausted")

    if open_lines:
        if args.dry_run:
            print("DRY RUN - would alert:\n" + "\n".join(open_lines))
        else:
            notify("AFIT hostel space open", "\n".join(open_lines))
            print("ALERT SENT")
    else:
        print("All full.")


if __name__ == "__main__":
    main()
