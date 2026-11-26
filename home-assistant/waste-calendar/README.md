# Waste collection: calendar import + Loxone display

Shows the next waste collection dates in the Loxone app and sends a Loxone push the evening before (18:00) and on the morning of the collection (06:00). Home Assistant holds the dates in a *Local Calendar*. The automation [`../automations/waste_collection_loxone.yaml`](../automations/waste_collection_loxone.yaml) pushes them to Loxone.

The waste association publishes no API or ICS feed, only a yearly plan as PDF and Excel. `waste_calendar.py` turns that Excel file into calendar events once a year.

## Data flow

```
Excel plan ──waste_calendar.py──▶ HA Local Calendar ──automation──▶ Loxone virtual text inputs
                                                                     ├─ one Virtual State tile per waste type
                                                                     ├─ "today & tomorrow" status (favourite)
                                                                     └─ message input ─▶ Loxone Notification (push)
```

## Loxone side

- One **Virtual Text Input** per waste type, plus one for the today/tomorrow status and one for the push text.
- Each display input feeds a **Virtual State** block. That block is what the app shows, because a Virtual Text Input itself is not visualised.
- The message input feeds a **Notification** object with the message `<v>` on change and an empty message on "off". The push title is the name of the Notification object, so create a dedicated one, for example "Müllabfuhr".
- HA writes to the inputs with the PyLoxone service `loxone.event_websocket_command` (`uuid` = UUID of the Virtual Text Input). Texts must not contain `/` because they are sent as part of a URL path.

## Automation

- Triggers: 00:05, 06:00 and 18:00, plus HA start (with a 90 s delay so PyLoxone is connected).
- Every run updates all tiles, e.g. `Di 01.12. (in 5 Tagen)`, `Morgen (…)`, `Heute (…)` or `kein Termin`, and the status `Heute: … · Morgen: …`.
- Push at 18:00 only if something is collected tomorrow, and at 06:00 only if something is collected today.
- Replace the `<LOXONE_UUID_…>` placeholders and the calendar entity before importing it. Deploy it like the other automations (see [`../README.md`](../README.md)).

## Yearly import

1. Download the new Excel plan (and the PDF for cross-checking) from the association's website.
2. Copy the calendar file from HA, for example `/config/.storage/local_calendar.<name>.ics`.
3. The first time, or if the layout changed: run `python waste_calendar.py compare <calendar.ics> <last-year.xlsx>` to see which Excel column matches which calendar title. Put the result into `config.json`, copied from `config.example.json`.
4. `python waste_calendar.py build <calendar.ics> <plan.xlsx> <year> <out.ics> --pdf <plan.pdf>`. The tool aborts if a column header changed, a date is outside the year, an event already exists, or a date is missing from the PDF.
5. On HA: back up the current file, replace it with `out.ics`, then reload the Local Calendar config entry. This works from the UI (*Settings → Devices & services → Local Calendar → Reload*) or via the API (`POST /api/config/config_entries/entry/<entry_id>/reload`).
6. Run the automation once. The tiles then show the new dates.

`config.json` is ignored by git. Keep your own column mapping and UID domain there.

Requirements: Python 3, `openpyxl`, and `pypdf` (only for `--pdf`).
