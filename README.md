# Beacon Luz

Control the Farming Simulator 22 USB beacon light from Windows, and flash/spin it when Zabbix reports a **Disaster** problem.

## Contents

- `beacon.py`: controls the light (spin, flash, stop). Uses only the Python standard library, nothing to install.
- `zabbix_monitor.py`: polls the Zabbix API every 60 seconds. While a Disaster problem is active, the light alternates between flashing and spinning. When the problem is resolved, the light turns off.

## Requirements

- Windows 10 or 11
- Python 3.x (tested with 3.12)
- The Farming Simulator 22 USB beacon connected to the PC (VID `340D`, PID `1710`)
- For the monitor: a Zabbix server (tested with 8.0) and an API token with **read-only** permission

## Controlling the light

```
python beacon.py spin 10    # spin for 10 seconds
python beacon.py flash 10   # flash for 10 seconds
python beacon.py stop       # turn off
```

## Using it with Zabbix

1. Copy `zabbix_url.example.txt` to `zabbix_url.txt` and put in your API URL, for example `https://your-server/zabbix/api_jsonrpc.php`.
2. Copy `zabbix_token.example.txt` to `zabbix_token.txt` and put in your API token. Create the token in *Administration → API tokens*, using a user with read-only access.
3. Test the connection without touching the light:

   ```
   python zabbix_monitor.py --once
   ```

4. Run the monitor:

   ```
   python zabbix_monitor.py
   ```

`zabbix_url.txt` and `zabbix_token.txt` are listed in `.gitignore`, so your URL and token are never published.

## How it works

- The monitor only makes outbound HTTPS connections to the Zabbix API. It opens no ports on your PC.
- The light is controlled over USB HID with the same command bytes the game uses. The byte sequences come from the [blinkybeacon](https://github.com/duckfullstop/blinkybeacon) project.
- The light expects 65-byte output reports; the script pads each command with zeros to that size.

## Limitations

- Only reacts to **Disaster** severity problems.
- There can be up to 60 seconds of delay between a problem appearing and the light reacting.
- The monitor only works while it is running and the PC is on with the light connected.
- Not tested with other beacon models.

## Security

Never publish your `zabbix_token.txt`. If a token leaks, revoke it in Zabbix and create a new one.
