# Home Assistant Automations

YAML automations that publish device states from Home Assistant to Loxone via MQTT.

## Files

### `automations/ev_mqtt_publish.yaml`

Publishes electric vehicle status every 59 seconds for two cars (Hyundai Ioniq 5 and Renault Zoe) to topic `Z2M/lox/EV`.

**Published fields per vehicle:** `SoC`, `Range`, `Plugged` (0/1), `Charging` (0/1), `Climate` (0/1), `Zone` (numeric location code)

Zone mapping: `home=1`, `Zone1–Zone7` map to custom HA zones (2–8), `not_home=0`, unknown=9. Replace zone names in the YAML with your own HA zone names.

### `automations/ep2_tasmota_mqtt_publish.yaml`

Publishes Tasmota smart plug energy data on state change or every 59 seconds to topic `lox/Tasmota`.

**Devices:** EP2TV, EP2Dreame, EP2Mikrowelle, EP2Pool, EP2BWWP, EP2NWSDaBo, EP2Backrohr

**Published fields per device:** `Power` (W), `State` (0/1), `Total` (kWh)

Format: `DeviceName:Power:X;State:Y;Total:Z|...`

### `automations/shelly_mqtt_publish.yaml`

Publishes Shelly energy meter data on state change or every 59 seconds to topic `lox/Shelly`.

**Devices:** Lueftung, KochfeldL, KochfeldR, Sauger, WP_A, WP_B, WP_C, PM_AZ, PM_SZGZ

**Published fields:** `Power` (W, absolute value), `Total` (kWh)

### `automations/somfy_status_publish.yaml`

Publishes Somfy shutter position/state on cover state change to topic `lox/Somfy` (8 shutters: `espsomfyrts_1` through `espsomfyrts_8`).

**Published fields per shutter:** `State` (0=closed, 1=open, 2=opening, 3=closing), `Pos` (0–100, inverted from HA position)

### `automations/somfy_steuerung.yaml`

Receives commands from Loxone on topic `lox/Somfy/set` and controls the corresponding HA cover entities.

**Supported commands:**
- `{"cmd":"Up","shades":[1,3,5]}` — opens selected shutters
- `{"cmd":"Down","shades":[2,4]}` — closes selected shutters
- `{"cmd":"Stop","shades":[1]}` — stops selected shutters
- `{"cmd":"Position","shades":{"1":30,"2":80}}` — moves shutters to position

## Deployment

1. In Home Assistant, go to **Settings → Automations**.
2. For each YAML file: click **+ Create Automation** → **Edit in YAML** → paste the file content → **Save**.
3. Alternatively, copy the files to your HA `config/automations/` folder and add `- !include_dir_list automations/` to `configuration.yaml`, then reload automations.

**Prerequisites:**
- MQTT integration configured in HA and connected to your broker
- Relevant device integrations active (Hyundai/Kia Connect, Renault/dacia, Tasmota, Shelly, ESPSomfy-RTS)
- Entity IDs in the YAML match your HA setup — adjust if yours differ
