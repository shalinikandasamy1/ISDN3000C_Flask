# HKUST Photo Booth AI Project

This project builds an AI-powered photo booth experience for HKUST Information Day using the RDK X5 development board. It combines image capture, custom AI filters, and AI-based image sorting with a simple Flask web interface.

## Project Overview

- **Photo Capture:** Use the RDK X5 camera to take photos, saving with date- and time-stamped filenames in a `photos` folder.
- **Wi-Fi Hotspot:** The RDK acts as a Wi-Fi hotspot named "**Sunrise**" broadcasting on `wlan0` with static IP `10.5.5.1`. Connected devices receive IPs via DHCP.
- **Image Filtering:**
  - Black & White filter (`bw_filter.py`) converts photos and saves filtered images as `<original>_bw.jpg` in `photos_bw`.
  - Vintage filter (`vintage_filter.py`) applies a sepia tone effect saving as `<original>_vintage.jpg` in `photos_vintage`.
- **AI-Based Sorting:** Images can be tagged and sorted based on AI-generated labels (under development).
- **Web Gallery (Planned):** Simple Flask app UI to navigate from “Begin” screen to photo capture and applying filters pages.
- **Service Autostart:** Configured `hostapd` and `isc-dhcp-server` services to run at boot for automatic Wi-Fi hotspot setup.

## Implementation Details

### Camera Capture (`capture_photos.py`)
- Uses OpenCV to capture photos from the RDK camera.
- Filenames use date and time plus a sequence number for uniqueness.
- Saves photos in `photos` directory.

### Filters
- Black & White and Vintage filters implemented as standalone Python scripts.
- Process images by filename and save filtered results with suffix `_bw` or `_vintage`.

### Hotspot & Networking
- `hostapd` config broadcasts Wi-Fi network SSID "Sunrise" on `wlan0`.
- Static IP `10.5.5.1` on `wlan0` configured in `/etc/network/interfaces`.
- DHCP server provides IPs in range `10.5.5.100`-`254`.
- NetworkManager configured to ignore `wlan0` for manual management.

## Running the Project

- Connect to the RDK’s “Sunrise” Wi-Fi hotspot.
- Use Python scripts to capture photos and apply filters.
- Web interface under development to enable simplified user interaction.

## Next Steps

- Complete AI-based multi-class image sorting and tagging.
- Integrate filters and capture with Flask web server.
- Enhance UI for live preview and better gallery management.
- Optimize AI Ghibli-style filter with your custom trained model.

***

