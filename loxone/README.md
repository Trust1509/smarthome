# Loxone Configuration

This folder covers everything needed on the Loxone side: Pico-C scripts, Virtual Input/Output setup, and how to wire the Command Recognition blocks that extract values from the bundled MQTT payloads.

## Background: why bundled payloads?

The Loxone MQTT Extension supports **max 16 subscriptions and 16 publishes**. Since this integration covers dozens of devices, multiple device values are packed into a single MQTT topic. Loxone then uses the **Befehlserkennungsbaustein** (Command Recognition block) to extract individual values from the payload.

---

## Receiving data: Virtual Inputs + Command Recognition

### Setup

1. In Loxone Config, add a **Virtual Input** (Virtueller Eingang) for each MQTT topic you want to subscribe to.
2. Set the input type to **Text** and enter the MQTT topic (e.g. `lox/FK`).
3. For each value you want to read, add a **Command Recognition block** and connect it to that Virtual Input.
4. Enter the extraction pattern in the block.

### Pattern syntax

| Syntax | Meaning |
|--------|---------|
| `\i...\i` | Match literal text |
| `\v` | Capture the value that follows |

### Example: Zigbee door/window contacts (`lox/FK`)

Payload received:
```json
{"name":"FK/WZ_Fenster_L","contact":1,"battery":62}
```

| Value | Pattern | Result |
|-------|---------|--------|
| Contact state | `\iWZ_Fenster_L\i\icontact":\i\v` | `1` (closed) or `0` (open) |
| Battery % | `\iWZ_Fenster_L\i\ibattery":\i\v` | `62` |

One Command Recognition block per value, all fed from the same Virtual Input `lox/FK`. Add one block per sensor — the device name in the pattern (`WZ_Fenster_L`) acts as the filter.

> **Note:** The Z2M extension only sends the fields that changed in the current event. If a sensor only updates battery, only `battery` arrives — `contact` is not re-sent. Loxone retains the last known value from the previous message.

### Example: Shelly energy meters (`lox/Shelly`)

Payload received:
```
Lueftung:Power:0.0;Total:24.458|KochfeldL:Power:0.0;Total:95.637|WP_A:Power:7.5;Total:2493.421|...
```

| Value | Pattern | Result |
|-------|---------|--------|
| Lueftung power | `\iLueftung:Power:\i\v` | `0.0` |
| WP_A power | `\iWP_A:Power:\i\v` | `7.5` |

> **Note:** To read Total, use a separate Command Recognition block with pattern `\iWP_A:Total:\i\v`. Each block can only extract one value — do not chain `\v` twice in one pattern.

All devices are always included in every message (not just changed ones), so Loxone always reads a consistent snapshot regardless of timing.

---

## Files

### `pico_scripts/somfy_position.c`

Reads up to 8 analog inputs (0–100%) representing shutter positions from ESPSomfy-RTS, inverts the coordinate system (Loxone: 0 = open, 100 = closed vs. ESPSomfy: 0 = closed, 100 = open), and publishes a JSON change-set whenever any position changes.

**Output format:**
```json
{"cmd":"Position","shades":{"1":30,"3":80}}
```

Only shades that changed since the last cycle are included — this minimises MQTT publish usage. On startup all 8 positions are published once to sync state.

**Inputs:** Analog inputs 0–7 (shutter position 0–100 from ESPSomfy-RTS Virtual Inputs)

**Output:** Text output 0 → connect to a Virtual Output (MQTT publish to `lox/Somfy/set`)

**Why the 500 ms delay on the receiving end:** ESPSomfy-RTS cannot process multiple position commands simultaneously. The Home Assistant automation `somfy_steuerung.yaml` therefore adds a 500 ms delay between each shade command. Sending all 8 positions in one burst without delay results in dropped commands.

---

## Deployment

### Pico-C script

1. In Loxone Config, create a new **Program Block** → type **Pico-C**.
2. Paste the content of `somfy_position.c` into the editor.
3. Connect analog inputs AI1–AI8 to the ESPSomfy-RTS shutter position outputs (from Virtual Inputs subscribed to the ESPSomfy MQTT topics).
4. Connect text output AQ1 to a **Virtual Output** with MQTT topic `lox/Somfy/set`.

### Virtual Inputs (MQTT subscriptions)

Add one Virtual Input per topic in the MQTT Extension settings:

| Topic | Type | Used for |
|-------|------|---------|
| `lox/FK` | Text | Door/window contacts |
| `lox/TK` | Text | Door/window contacts (second group) |
| `lox/BM` | Text | Motion sensors |
| `lox/PM` | Text | Presence sensors |
| `lox/SS` | Text | Smart plugs (state + power) |
| `lox/AQ` | Text | Air quality sensors |
| `lox/WL` | Text | Water leak sensors |
| `lox/WV` | Text | Water valves |
| `lox/Shelly` | Text | Shelly energy meters |
| `lox/Tasmota` | Text | Tasmota smart plugs (EP2) |
| `lox/Somfy` | Text | Somfy shutter state + position |
| `Z2M/lox/EV` | Text | EV status (Ioniq 5 + Zoe) |

### Virtual Outputs (MQTT publishes)

| Topic | Used for |
|-------|---------|
| `lox/Somfy/set` | Send shutter position commands to HA |
| `lox/WV/set` | Open/close water valves |
| `lox/SS/set` | Switch smart plugs on/off |
| `lox/LED/set` | Control LED bulbs |
| `lox/LED/Group/set` | Control LED groups |
