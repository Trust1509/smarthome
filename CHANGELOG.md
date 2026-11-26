# Changelog

## [1.2.0] - 2026-11-26
### Added
- Waste collection for Loxone: HA automation `waste_collection_loxone.yaml` writes the next collection dates from a Local Calendar into Loxone virtual text inputs (one tile per waste type plus a today/tomorrow status) and triggers a Loxone push at 18:00 (tomorrow) and 06:00 (today)
- `home-assistant/waste-calendar/waste_calendar.py`: yearly import of an Excel collection plan into the HA Local Calendar ICS (`compare` to find the column mapping, `build` with duplicate, year and PDF cross-checks); column mapping in an ignored `config.json`

---

## [1.1.1] - 2026-06-27
### Fixed
- Somfy Pico-C script no longer re-commands all shades after a Miniserver/Pico restart. It now seeds its baseline from the current TPos inputs without publishing, then only sends genuine changes. Previously every restart re-sent all 8 positions, and because RTS has no position feedback the estimated moves drifted further with each restart (shades ending up fully closed instead of at their target).

---

## [1.1.0] - 2026-06-02
### Added
- UniFi presence detection (`unifi-presence/`): bundles all person states into single MQTT topic `lox/Presence`
- Multi-MAC support per person (OR logic: home if any device connected)
- External `config.json` for secrets and device list (not committed to git)
- Force-publish every 5 min to keep Loxone in sync after restart

### Changed
- `.gitignore` extended with `config.json`

---

## [1.0.0] - 2026-05-30
### Added
- Initial release
- Zigbee2MQTT extensions: loxone-bridge.mjs (sensor bundling), loxone-commander.mjs (device control)
- Home Assistant automations: EV status, Tasmota EP2, Shelly energy meters, Somfy shutters
- Loxone Pico-C script: Somfy shutter position with change detection
- Full documentation in README files for each component
