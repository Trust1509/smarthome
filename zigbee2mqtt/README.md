# Zigbee2MQTT Extensions

Custom Zigbee2MQTT extensions that bridge Zigbee device events to Loxone via MQTT.

## Why custom extensions?

The Loxone MQTT Extension supports only **16 subscriptions**. With many Zigbee sensors of different types, a 1:1 mapping (one topic per device) would use up all slots. Instead, sensors are grouped by type into a single topic each (e.g. all door contacts → `lox/FK`). Loxone then uses the Command Recognition block to filter out individual device values by name.

## Payload strategy: partial updates

Zigbee sensors rarely change multiple values at the same time. When a door contact triggers, only `contact` is sent — `battery` only arrives on its own periodic update. The extension maintains a per-device cache and merges incoming fields before publishing. This means:

- **Loxone only ever receives changed fields** — not the full device state every time
- The payload is always valid JSON with the device name included so Loxone can match it
- Each device type goes to its own topic, so Loxone needs only one subscription per sensor class

## Files

### `loxone-bridge.mjs`

Listens to all Zigbee2MQTT entity state publications and forwards relevant sensor/actor data to Loxone MQTT topics. Device name prefixes determine the target topic:

| Prefix | Devices | MQTT topic | Published fields |
|--------|---------|------------|-----------------|
| `FK/`, `TK/` | Window/door contacts | `lox/FK`, `lox/TK` | `contact` (0/1), `battery` |
| `BM/` | Motion sensors | `lox/BM` | `occupancy`, `illuminance`, `battery`, `temperature` |
| `PM/` | Presence sensors | `lox/PM` | `presence`, `movement`, `target_distance`, `temperature` |
| `SS/` | Smart plugs | `lox/SS` | batched: `State`, `Power`, `Temp` per device |
| `AQ/` | Air quality sensors | `lox/AQ` | `humidity`, `temperature`, `pm25`, `voc_index` |
| `WL/` | Water leak sensors | `lox/WL` | `water_leak`, `battery` |
| `WV/` | Water valves | `lox/WV` | `state`, `flow`, `battery` |

Smart plugs (`SS/`) are batched with a 2-second debounce to reduce MQTT traffic. The combined message uses the format `Name:State:1;Power:100;Temp:45|...`.

### `loxone-commander.mjs`

Subscribes to `lox/#` and translates Loxone set-commands back to Zigbee2MQTT device commands:

| Topic | Payload | Action |
|-------|---------|--------|
| `lox/WV/set` | `{"name":"Valve1","state":"ON"}` | Opens/closes water valve |
| `lox/SS/set` | `{"name":"Plug1","state":"ON"}` | Switches smart plug on/off |
| `lox/LED/set` | `{"name":"Bulb1","state":"ON","brightness":200,"color":{"r":255,...}}` | Controls LED bulb |
| `lox/LED/Group/set` | `{"name":"GroupA","state":"ON","brightness":150}` | Controls LED group |

## Deployment

1. Copy `loxone-bridge.mjs` and `loxone-commander.mjs` to your Zigbee2MQTT `data/external_extensions/` directory.
2. Restart Zigbee2MQTT.
3. The extensions load automatically. Check the Z2M log for `LoxoneBridge started` and `LoxoneCommander started`.

**Naming convention:** Name your Zigbee devices in Z2M using the prefix scheme above (e.g. `FK/Wohnzimmer`, `BM/Flur`). The prefix determines which MQTT topic receives the data.
