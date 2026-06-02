# UniFi Presence Detection

Detects which household members are home by checking their device MAC addresses against the UniFi controller's active client list. Publishes a single bundled MQTT message for Loxone.

## How it works

Every 60 seconds (configurable) the script queries the UniFi Network API for all currently connected clients. For each configured person it checks whether **any** of their registered MAC addresses appears in that list. If anything changed since the last cycle, a single MQTT message is published containing all presence states.

**Output topic:** `lox/Presence`
**Payload format:**
```
Person1:1|Person2:0
```

`1` = at least one device connected (home), `0` = no device connected (away).

A force-publish fires every 5 minutes (configurable) even without changes — this keeps Loxone in sync after a restart.

## Why one topic for all persons?

The Loxone MQTT Extension supports only **16 subscriptions**. Bundling all presence states into one topic uses exactly one subscription slot. Loxone uses the Command Recognition block to extract individual values:

| Person | Pattern | Result |
|--------|---------|--------|
| Person1 present | `\iPerson1:\i\v` | `1` or `0` |
| Person2 present | `\iPerson2:\i\v` | `1` or `0` |

## Multiple MACs per person

A person is considered **home** if **any** of their devices is connected. Add all devices (phone, tablet, laptop) to the `macs` list in `config.json` — no code changes needed.

```json
{
  "name": "Person1",
  "macs": [
    "aa:bb:cc:dd:ee:ff",
    "11:22:33:44:55:66"
  ]
}
```

## Adding a new person

1. Find the device MAC address in your UniFi controller (Clients list).
2. Add a new entry to `devices` in `config.json`:
   ```json
   { "name": "Guest", "macs": ["xx:xx:xx:xx:xx:xx"] }
   ```
3. Restart the container: `docker restart unifi_presence`

No code changes required.

## Configuration

Copy `config.example.json` to `config.json` and fill in your values. **Never commit `config.json`** — it contains API keys and passwords (it is listed in `.gitignore`).

| Key | Description |
|-----|-------------|
| `unifi.host` | IP of your UniFi Dream Machine / controller |
| `unifi.api_key` | UniFi API key (Settings → Control Plane → API Keys) |
| `unifi.site_id` | Site UUID (visible in the API or browser URL) |
| `mqtt.host` | MQTT broker IP |
| `mqtt.port` | MQTT broker port (default 1883) |
| `mqtt.user` / `mqtt.pass` | MQTT credentials |
| `mqtt.topic` | Target topic for Loxone (default `lox/Presence`) |
| `interval` | Poll interval in seconds (default 60) |
| `force_publish_interval` | Force full publish even without changes (default 300 s) |

## Deployment

1. Copy `presence.py` and `config.json` to `/mnt/VMs/Data/unifi_presence/` on TrueNAS.
2. Deploy with `docker compose up -d` using the provided `docker-compose.yml`.
3. Check logs: `docker logs -f unifi_presence`

Expected log output:
```
[INFO] Starting presence detection, publishing to lox/Presence
[INFO] Tracking 2 person(s): ['Person1', 'Person2']
[INFO] 47 clients connected
[PUBLISH/changed] lox/Presence → Person1:1|Person2:0
[INFO] No change: Person1:1 | Person2:0
```

## Loxone setup

1. Add a **Virtual Input** in the MQTT Extension subscribed to `lox/Presence` (type: Text).
2. For each person, add a **Command Recognition block** connected to that input.
3. Set the pattern: `\iPerson1:\i\v` → returns `1` (home) or `0` (away).
4. Connect the output to your Loxone logic (presence-based automations, lighting, heating, etc.).
