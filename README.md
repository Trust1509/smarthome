# 🏠 Smarthome

Smart Home automation code integrating Loxone, Zigbee2MQTT, and Home Assistant.

> This project was vibe coded with [Claude Sonnet 4.6](https://www.anthropic.com/claude) by Anthropic.

**License:** CC BY-NC 4.0 - Free for personal/non-commercial use. Attribution required. Commercial use prohibited.
**Copyright:** Manuel Wagner (GitHub: Trust1509)

---

## Why this architecture exists

The Loxone Miniserver MQTT Extension supports a maximum of **16 subscriptions and 16 publishes**. With dozens of Zigbee sensors, energy meters, EVs, and shutters, a 1:1 mapping (one MQTT topic per device) would exhaust that limit immediately.

The solution: **bundle multiple devices into a single MQTT topic** using structured payloads, and extract individual values inside Loxone using the [Command Recognition block](https://www.loxone.com/help/command-recognition) (`Befehlserkennungsbaustein`).

This repo implements that bundling at three levels:

| Layer | What it bundles | How |
|-------|----------------|-----|
| **Zigbee2MQTT extensions** | All Zigbee sensors by type (contacts, motion, plugs, …) into one topic per device class | Custom JS extensions in Z2M |
| **Home Assistant automations** | EV status, energy meters (Tasmota/Shelly), Somfy shutter positions | YAML automations with MQTT publish |
| **Loxone Pico-C** | Up to 8 shutter positions in one publish | Pico-C script, publishes only changed values |

---

## Repository Structure

```
smarthome/
├── zigbee2mqtt/          # Z2M extensions: bundle Zigbee events → lox/* topics
├── home-assistant/       # HA automations: bundle device states → lox/* topics
└── loxone/               # Pico-C scripts + Loxone config notes
```

## Payload strategy: partial vs. full updates

Two different strategies are used depending on how fast a sensor changes:

### Slow/event-driven sensors → partial payload (only what changed)

Zigbee sensors (door contacts, motion, leaks, …) rarely update multiple values at the same time. The Z2M extension sends only the fields that arrived in the current event, merged with a per-device cache. Loxone receives a compact JSON per device:

```
{"name":"FK/WZ_Fenster_L","contact":1,"battery":62}
```

Loxone processes this at its own pace — since updates are infrequent, there is no risk of values overwriting each other before Loxone reads them.

### Fast/polling sensors → full payload (all devices every cycle)

Energy meters (Shelly, Tasmota) and EV status change constantly. If only deltas were sent, Loxone might read a mix of old and new values from different cycles. Instead, **every publish contains all devices**, so Loxone always sees a consistent snapshot:

```
Lueftung:Power:0.0;Total:24.458|KochfeldL:Power:0.0;Total:95.637|KochfeldR:Power:0.0;Total:157.523|...
```

This is also why these automations have a 59-second time-pattern fallback — to keep Loxone in sync even when no state change fires.

---

## Reading values in Loxone: Command Recognition block

Loxone's **Befehlserkennungsbaustein** (Command Recognition) extracts values from a received MQTT payload using a search pattern. The block finds the pattern in the incoming string and returns the value (`\v`) that follows.

### Example: JSON payload (Z2M sensors)

Incoming topic `lox/FK`, payload:
```json
{"name":"FK/WZ_Fenster_L","contact":1,"battery":62}
```

| What to extract | Pattern | Result |
|----------------|---------|--------|
| Contact state | `\iWZ_Fenster_L\i\icontact":\i\v` | `1` |
| Battery level | `\iWZ_Fenster_L\i\ibattery":\i\v` | `62` |

`\i...\i` matches the literal text inside, `\v` captures the value that follows.

### Example: Pipe-separated payload (Shelly/Tasmota)

Incoming topic `lox/Shelly`, payload:
```
Lueftung:Power:0.0;Total:24.458|KochfeldL:Power:0.0;Total:95.637|...
```

| What to extract | Pattern | Result |
|----------------|---------|--------|
| Lueftung power | `\iLueftung:Power:\i\v` | `0.0` |
| WP_A total | `\iWP_A:Power:\i\v` | `7.5` |

One Command Recognition block per value. Each block subscribes to the same Virtual Input (the single MQTT subscription for that topic).

---

## Prerequisites

- Zigbee2MQTT running (Docker or native)
- Home Assistant with MQTT integration configured
- Loxone Miniserver with MQTT Extension (max 16 subs / 16 publishes)
- MQTT broker (e.g. Mosquitto) reachable by all three systems

## Getting Started

See the README in each subfolder for deployment instructions:

- [zigbee2mqtt/README.md](zigbee2mqtt/README.md)
- [home-assistant/README.md](home-assistant/README.md)
- [loxone/README.md](loxone/README.md)

---

*Versioning via Git — each change is saved as a commit with date and description. When making future changes with a different Claude version, note the version in the commit message.*
