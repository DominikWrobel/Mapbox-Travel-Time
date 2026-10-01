# Mapbox Travel Time for Home Assistant

<img width="1254" height="1254" alt="mapbox" src="https://github.com/user-attachments/assets/6ec7be4c-6849-4fc9-9001-80345e1fd7ee" />


Custom Home Assistant integration that exposes traffic-aware car travel time using the Mapbox Directions API and the `mapbox/driving-traffic` profile.

Designed as a replacement for travel-time integrations that depend on Waze endpoints.

## Features

- Live/typical traffic-aware ETA from Mapbox Directions API.
- One config entry = one route.
- Origin and destination may be:
  - a Home Assistant entity with `latitude` and `longitude` attributes, e.g. `zone.home`, `person.someone`, `device_tracker.car`;
  - static coordinates written as `latitude,longitude`.
- Dynamic locations are resolved again on every poll.
- Default update interval: **300 seconds / 5 minutes**.
- Update interval configurable from **60 to 3600 seconds**.
- Polish and English UI translations.
- Reauthentication when Mapbox rejects the access token.
- Privacy-safe diagnostics: token and configured locations are redacted.
- Optional INFO log for every successful update; normal successful polling uses DEBUG.

## Entities created for every route

For a route named `Car → Home` the integration creates one Home Assistant device with four sensors:

- **Travel time** — current traffic-aware ETA in minutes.
- **Typical travel time** — typical ETA returned by Mapbox.
- **Traffic delay** — current ETA minus typical ETA.
- **Distance** — selected route length in km.

The main travel-time sensor additionally exposes:

- origin label;
- destination label;
- distance;
- typical duration;
- traffic delay;
- last successful update;
- routing profile.

## Mapbox token

Create a Mapbox account and obtain a public access token from your Mapbox account. Public tokens normally start with `pk.`.

This integration calls:

`https://api.mapbox.com/directions/v5/mapbox/driving-traffic/...`

Always check the current Mapbox pricing/usage limits for your account.

## Installation with HACS

### Custom repository

1. Put this repository on GitHub.
2. In Home Assistant open **HACS → Integrations**.
3. Open the HACS menu and choose **Custom repositories**.
4. Paste the GitHub repository URL.
5. Select category **Integration**.
6. Install **Mapbox Travel Time**.
7. Restart Home Assistant.
8. Open **Settings → Devices & services → Add integration**.
9. Search for **Mapbox Travel Time**.

### Manual installation

Copy:

`custom_components/mapbox_travel_time`

to:

`/config/custom_components/mapbox_travel_time`

and restart Home Assistant.

## Configuration

Add a new integration instance for every route.

### Fixed route using zones

Example:

- Route name: `Home → Work`
- Origin: `zone.home`
- Destination: `zone.work`

### Dynamic vehicle route

Example:

- Route name: `Car → Home`
- Origin: `device_tracker.car`
- Destination: `zone.home`

The vehicle coordinates are read from the entity again every 5 minutes, so the route automatically follows the vehicle.

### Static coordinates

Use latitude first, longitude second:

`51.7592,19.4560`

Do not use the Mapbox API order here. The integration converts the values internally to the longitude/latitude order expected by Mapbox.

## Polling interval

Open:

**Settings → Devices & services → Mapbox Travel Time → Configure**

The default is:

`300 s`

which equals 5 minutes.

## Logging

Normal operation is intentionally quiet.

On startup you will see a concise INFO entry similar to:

```text
[Car → Home] Starting Mapbox Travel Time (device_tracker.car -> zone.home, every 300s)
```

Errors are logged at WARNING/ERROR level without exposing the access token.

To log every successful refresh at INFO level, open the integration options and enable:

**Log every successful update at INFO level**

Example:

```text
[Car → Home] Updated: 24.3 min, 18.6 km, traffic delay +5.8 min | Car -> Home
```

For full DEBUG logging add to `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.mapbox_travel_time: debug
```

Then restart Home Assistant or change logger settings using Home Assistant developer tools if appropriate for your installation.

## Failure handling

- Temporary network/API failure: coordinator keeps using Home Assistant's normal unavailable/update-failed behavior and retries on the next scheduled refresh.
- Missing GPS attributes: update fails with a clear location-resolution warning.
- HTTP 401/403: Home Assistant starts a reauthentication flow for a new token.
- HTTP 429: a rate-limit warning is logged and the next regular update retries.
- API timeout: the request is aborted after 15 seconds.

## Diagnostics

Home Assistant diagnostics are supported. The following are deliberately redacted:

- Mapbox access token;
- origin configuration;
- destination configuration.

The diagnostics include only non-sensitive route metrics and coordinator state.

## Notes

The `mapbox/driving-traffic` routing profile uses current and historical traffic conditions where Mapbox traffic data is available. When live traffic is not available, Mapbox may rely on typical traffic conditions.

## License

MIT
