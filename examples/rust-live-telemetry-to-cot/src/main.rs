//! Skydio live telemetry to TAK Cursor on Target (CoT).
//!
//! This example connects to a vehicle's live telemetry websocket (the same
//! stream the `python-live-telemetry` and `javascript-telemetry-alert-boundary`
//! examples consume) and turns every position message into a CoT 2.0 event
//! that ATAK, WinTAK, iTAK or a TAK Server will draw as a moving marker.
//!
//! The telemetry to CoT mapping is done by the `uas-cot` crate
//! (https://crates.io/crates/uas-cot), maintained by Matthew Busel. The crate
//! owns the CoT event model and writes the XML that TAK clients accept.
//!
//! By default each CoT event is printed to stdout. Set `TAK_ENDPOINT` to also
//! send events to a TAK Server TCP input (`host:port`), or set it to `multicast`
//! to broadcast to the TAK situational-awareness multicast group.

use std::env;
use std::time::{SystemTime, UNIX_EPOCH};

use futures_util::StreamExt;
use serde::Deserialize;
use tokio_tungstenite::connect_async;
use tokio_tungstenite::tungstenite::Message;

use uas_cot::net::{TcpSender, UdpSender};
use uas_cot::{Event, Point, Track};

/// A single Skydio telemetry message. Only the position fields are required;
/// everything else is optional so partial frames still map to a point.
///
/// Field names follow the Skydio live telemetry payload, where `lat` and `lon`
/// sit on the root object. Compare against your own stream if a field is
/// missing: https://apidocs.skydio.com/reference/live-telemetry
#[derive(Debug, Deserialize)]
struct Telemetry {
    lat: f64,
    lon: f64,
    #[serde(default, alias = "altitude", alias = "alt_m", alias = "height")]
    alt: Option<f64>,
    #[serde(default, alias = "heading", alias = "yaw")]
    course: Option<f64>,
    #[serde(default, alias = "ground_speed", alias = "speed_mps")]
    speed: Option<f64>,
}

/// Map one telemetry frame to a CoT event for `vehicle_serial`.
///
/// This is the real dependency on `uas-cot`: [`Event`], [`Point`] and
/// [`Track`] are the crate's CoT 2.0 model, and [`Event::to_xml`] produces the
/// TAK-accepted XML.
fn telemetry_to_cot(vehicle_serial: &str, t: &Telemetry) -> Event {
    let now_us = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_micros() as u64)
        .unwrap_or(0);

    // "a-f-A-M-F-Q": a friendly airborne UAS marker. Adjust the CoT type to
    // match how your operation classifies the aircraft.
    let mut event = Event::new(
        format!("skydio-{vehicle_serial}"),
        "a-f-A-M-F-Q",
        now_us,
        10,
    );
    event.point = Point::new(t.lat, t.lon, t.alt.unwrap_or(0.0));
    event.callsign = Some(vehicle_serial.to_string());
    if let (Some(course), Some(speed)) = (t.course, t.speed) {
        event.track = Some(Track { course, speed });
    }
    event.remarks = Some("Skydio live telemetry via uas-cot".to_string());
    event
}

/// Where to deliver each CoT event, from the `TAK_ENDPOINT` environment var.
enum Sink {
    Stdout,
    Multicast(UdpSender),
    Tcp(TcpSender),
}

impl Sink {
    fn from_env() -> std::io::Result<Self> {
        match env::var("TAK_ENDPOINT").ok().as_deref() {
            None | Some("") => Ok(Sink::Stdout),
            Some("multicast") => Ok(Sink::Multicast(UdpSender::sa_multicast()?)),
            Some(addr) => Ok(Sink::Tcp(TcpSender::connect(addr)?)),
        }
    }

    fn deliver(&mut self, event: &Event) -> std::io::Result<()> {
        match self {
            Sink::Stdout => {
                println!("{}", event.to_xml());
                Ok(())
            }
            Sink::Multicast(s) => s.send(event),
            Sink::Tcp(s) => s.send(event),
        }
    }
}

/// Build the telemetry websocket URL, matching the other examples in this repo.
fn build_ws_url(vehicle_serial: &str) -> String {
    match env::var("API_TOKEN_SECRET").ok().filter(|s| !s.is_empty()) {
        Some(token) => format!("wss://stream.skydio.com/data/{vehicle_serial}?token={token}"),
        None => {
            eprintln!("API_TOKEN_SECRET is not set; using the URL without a token.");
            format!("wss://stream.skydio.com/data/{vehicle_serial}")
        }
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let vehicle_serial = env::args()
        .nth(1)
        .or_else(|| env::var("VEHICLE_SERIAL").ok())
        .ok_or("usage: rust-live-telemetry-to-cot <vehicle_serial> (or set VEHICLE_SERIAL)")?;

    let mut sink = Sink::from_env()?;
    let url = build_ws_url(&vehicle_serial);
    eprintln!("Connecting to telemetry websocket for {vehicle_serial}...");

    let (ws_stream, _resp) = connect_async(&url).await?;
    eprintln!("Connected. Streaming CoT events (Ctrl+C to stop).");
    let (_write, mut read) = ws_stream.split();

    while let Some(message) = read.next().await {
        let text = match message? {
            Message::Text(t) => t,
            Message::Binary(b) => String::from_utf8_lossy(&b).into_owned(),
            Message::Close(_) => break,
            _ => continue,
        };

        match serde_json::from_str::<Telemetry>(&text) {
            Ok(telemetry) => {
                let event = telemetry_to_cot(&vehicle_serial, &telemetry);
                if let Err(e) = sink.deliver(&event) {
                    eprintln!("Failed to deliver CoT event: {e}");
                }
            }
            // Not every telemetry frame carries a position; skip those quietly.
            Err(_) => continue,
        }
    }

    eprintln!("Telemetry stream closed.");
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn maps_telemetry_to_valid_cot_xml() {
        let telemetry = Telemetry {
            lat: 37.7749,
            lon: -122.4194,
            alt: Some(120.0),
            course: Some(90.0),
            speed: Some(11.5),
        };
        let event = telemetry_to_cot("SKY-123", &telemetry);
        let xml = event.to_xml();

        assert!(xml.contains("uid=\"skydio-SKY-123\""));
        assert!(xml.contains("type=\"a-f-A-M-F-Q\""));
        assert!(xml.contains("lat=\"37.7749000\""));
        assert!(xml.contains("lon=\"-122.4194000\""));
        assert!(xml.contains("<contact callsign=\"SKY-123\"/>"));
    }

    #[test]
    fn position_only_frame_still_maps() {
        let telemetry: Telemetry =
            serde_json::from_str(r#"{"lat": 45.5470818, "lon": -122.9668346}"#).unwrap();
        let event = telemetry_to_cot("SKY-456", &telemetry);
        assert!(event.track.is_none());
        assert!(event.to_xml().contains("lat=\"45.5470818\""));
    }
}
