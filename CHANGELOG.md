# Changelog

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
