"""
UniFi Presence Detection → Loxone MQTT
Bundles all person presence states into a single MQTT topic.

Config: config.json (see config.example.json)
Output: lox/Presence  →  Person1:1|Person2:0|...
"""

import httpx
import paho.mqtt.client as mqtt
import time
import json
import os
import sys

os.environ['PYTHONUNBUFFERED'] = '1'

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def get_connected_macs(cfg):
    """Return set of lowercase MAC addresses currently connected to UniFi."""
    host = cfg["unifi"]["host"]
    site = cfg["unifi"]["site_id"]
    url = f"https://{host}/proxy/network/integration/v1/sites/{site}/clients?limit=200"
    headers = {"X-API-KEY": cfg["unifi"]["api_key"], "Accept": "application/json"}
    try:
        with httpx.Client(verify=False) as client:
            r = client.get(url, headers=headers, timeout=10)
            data = r.json()
            return {d["macAddress"].lower() for d in data.get("data", [])}
    except Exception as e:
        print(f"[ERROR] UniFi API: {e}", flush=True)
        return None


def build_payload(devices, states):
    """Build pipe-separated payload for Loxone: Person1:1|Person2:0|..."""
    return "|".join(
        f"{d['name']}:{1 if states.get(d['name'], False) else 0}"
        for d in devices
    )


def main():
    cfg = load_config()
    mqtt_cfg = cfg["mqtt"]
    devices = cfg["devices"]
    interval = cfg.get("interval", 60)
    force_interval = cfg.get("force_publish_interval", 300)

    mq = mqtt.Client()
    if mqtt_cfg.get("user"):
        mq.username_pw_set(mqtt_cfg["user"], mqtt_cfg.get("pass", ""))
    mq.connect(mqtt_cfg["host"], mqtt_cfg.get("port", 1883))
    mq.loop_start()

    topic = mqtt_cfg["topic"]
    last_states = {d["name"]: None for d in devices}
    last_force_publish = 0

    print(f"[INFO] Starting presence detection, publishing to {topic}", flush=True)
    print(f"[INFO] Tracking {len(devices)} person(s): {[d['name'] for d in devices]}", flush=True)

    while True:
        connected_macs = get_connected_macs(cfg)

        if connected_macs is None:
            print("[WARN] Empty/failed API response, skipping cycle", flush=True)
            time.sleep(interval)
            continue

        print(f"[INFO] {len(connected_macs)} clients connected", flush=True)

        # Determine presence per person (present if ANY of their MACs is connected)
        current_states = {}
        for device in devices:
            macs = {m.lower() for m in device["macs"]}
            present = bool(macs & connected_macs)
            current_states[device["name"]] = present

        # Publish if anything changed or force-publish interval elapsed
        changed = any(current_states[d["name"]] != last_states[d["name"]] for d in devices)
        force_due = (time.time() - last_force_publish) >= force_interval

        if changed or force_due:
            payload = build_payload(devices, current_states)
            mq.publish(topic, payload, retain=True)
            reason = "changed" if changed else "force"
            print(f"[PUBLISH/{reason}] {topic} → {payload}", flush=True)
            last_states = current_states.copy()
            last_force_publish = time.time()
        else:
            states_str = " | ".join(f"{n}:{1 if v else 0}" for n, v in current_states.items())
            print(f"[INFO] No change: {states_str}", flush=True)

        time.sleep(interval)


if __name__ == "__main__":
    main()
