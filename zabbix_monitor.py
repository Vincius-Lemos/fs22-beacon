"""Flash the beacon while a Zabbix Disaster problem is active.

Polls the Zabbix API (outbound HTTPS only) every 60 seconds.
Usage: python zabbix_monitor.py [--once]
  --once  check a single time and print the result, without touching the light.
"""
import json
import os
import sys
import time
import urllib.request

import beacon

HERE = os.path.dirname(os.path.abspath(__file__))
DISASTER = 5
INTERVAL = 60


def read_setting(name):
    with open(os.path.join(HERE, name), encoding="ascii") as f:
        return f.read().strip()


def disaster_problems(url, token):
    body = json.dumps({
        "jsonrpc": "2.0",
        "method": "problem.get",
        "params": {"output": ["eventid", "name", "severity"], "severities": [DISASTER]},
        "id": 1,
    }).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json-rpc",
        "Authorization": f"Bearer {token}",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        reply = json.load(resp)
    if "error" in reply:
        raise RuntimeError(reply["error"])
    return reply["result"]


def main():
    url = read_setting("zabbix_url.txt")
    token = read_setting("zabbix_token.txt")

    if "--once" in sys.argv:
        problems = disaster_problems(url, token)
        print(f"Active Disaster problems: {len(problems)}")
        for p in problems:
            print(" -", p["name"])
        return 0

    handle = None
    flashing = False
    effect = "flash"
    while True:
        try:
            problems = disaster_problems(url, token)
            if problems and not flashing:
                handle = beacon.find_beacon_path()
                if handle is None:
                    print("Beacon not found; will retry.")
                else:
                    flashing = True
                    beacon.write(handle, beacon.MAGIC["flash"])
                    print(f"Disaster active ({len(problems)}): flashing and spinning.")
            elif not problems and flashing:
                beacon.write(handle, beacon.MAGIC["stop"])
                beacon.k32.CloseHandle(handle)
                handle, flashing = None, False
                print("No Disaster problems: stopped.")
            elif flashing:
                # Alternate flash and spin; resending also keeps the beacon awake.
                effect = "spin" if effect == "flash" else "flash"
                beacon.write(handle, beacon.MAGIC[effect])
        except Exception as exc:
            print("Check failed:", exc)
        time.sleep(INTERVAL if not flashing else 5)


if __name__ == "__main__":
    sys.exit(main())
