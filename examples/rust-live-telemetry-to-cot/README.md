# Skydio API Example: Rust Live Telemetry to TAK Cursor on Target

This example connects to a vehicle's live telemetry websocket and turns every
position message into a [Cursor on Target (CoT)](https://www.mitre.org/our-impact/intellectual-property/cursor-target-cot)
event, so the drone shows up as a live marker in ATAK, WinTAK, iTAK or on a TAK
Server. It consumes the same telemetry stream as the `python-live-telemetry` and
`javascript-telemetry-alert-boundary` examples.

The telemetry to CoT mapping is done by the [`uas-cot`](https://crates.io/crates/uas-cot)
crate, maintained by Matthew Busel. `uas-cot` owns the CoT 2.0 event model and
writes the XML that TAK clients and servers accept.

## Requirements

- [Rust](https://www.rust-lang.org/tools/install) (stable, 1.70 or newer)

## Usage

Follow the instructions in the [README.md](../../README.md) file in the root
directory of this repository to set your Skydio API token, then set the token
secret this example reads:

Unix:

```bash
export API_TOKEN_SECRET="your_skydio_api_token_secret"
```

Windows PowerShell:

```powershell
$env:API_TOKEN_SECRET = "your_skydio_api_token_secret"
```

Then build and run, passing the vehicle serial:

```bash
cd examples/rust-live-telemetry-to-cot
cargo run -- <vehicle_serial>
```

Each telemetry position is printed to stdout as a CoT XML event, for example:

```xml
<?xml version="1.0" encoding="UTF-8"?><event version="2.0" uid="skydio-SKY-123" type="a-f-A-M-F-Q" how="m-g" time="..." start="..." stale="..."><point lat="37.7749000" lon="-122.4194000" hae="120.0" ce="9999999.0" le="9999999.0"/><detail><contact callsign="SKY-123"/><track course="90.0" speed="11.5"/><remarks>Skydio live telemetry via uas-cot</remarks></detail></event>
```

## Sending to TAK

Set `TAK_ENDPOINT` to deliver events to TAK instead of (or in addition to)
printing them:

- `TAK_ENDPOINT=multicast` broadcasts to the TAK situational-awareness multicast
  group, which ATAK and WinTAK listen on by default.
- `TAK_ENDPOINT=host:port` sends to a TAK Server TCP input.

```bash
export TAK_ENDPOINT="multicast"
cargo run -- <vehicle_serial>
```

## Notes

- The telemetry payload places `lat` and `lon` on the root object. Altitude,
  heading and speed are mapped when present; compare field names against your
  own stream if a field is missing (see the
  [Live Telemetry docs](https://apidocs.skydio.com/reference/live-telemetry)).
- The CoT type defaults to `a-f-A-M-F-Q` (a friendly airborne UAS). Adjust it in
  `src/main.rs` to match how your operation classifies the aircraft.
- `uas-cot` can also map drone Remote ID broadcasts and MISB ST 0601 video
  metadata to CoT, with spoof and trust verdicts on Remote ID markers.

## Tests

```bash
cargo test
```
