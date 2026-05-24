---
name: epd-display
description: >-
  Control EPD e-ink display devices via BLE on the home NUC server.
  Use epd-tool commands through mars-cli to scan devices, send images,
  manage image slots, sync time, clear screen, and set slideshow mode.
  Trigger when user asks about: e-ink screen, EPD display, sending image
  to screen, ink screen slots, slideshow, clear screen, calendar mode,
  or any operation related to the home e-ink display device.
compatibility: Requires mars-cli configured with access to mars-sandbox server, and epd-tool installed on the NUC node.
metadata:
  author: orbit-mind
  version: "1.0"
---

# EPD Display - E-Ink Screen Remote Control

Control BLE e-ink display devices on the home NUC by executing `epd-tool` commands remotely via `mars-cli exec`.

## Architecture

```
Hermes Agent → mars-cli (HTTP) → mars-sandbox → WebSocket → home-agent (NUC) → epd-tool (BLE) → E-Ink Device
```

## Prerequisites

- `mars-cli` installed and configured (env vars `MARS_SANDBOX_URL` and `MARS_SANDBOX_API_KEY`)
- NUC node online with `epd-tool` installed
- NUC has a Bluetooth adapter and the e-ink device is within BLE range

Verify:

```bash
mars-cli nodes                              # Confirm NUC node is online
mars-cli exec <nuc_id> 'epd-tool --help'    # Confirm epd-tool is available
```

## Core Workflow

### Step 1: Find the NUC node

```bash
mars-cli nodes
```

Find the NUC node with `status: "online"` and note its `node_id`.

### Step 2: Scan for e-ink devices (first time only)

```bash
mars-cli exec <nuc_id> 'epd-tool scan --json' -t 30
```

Look for devices with `is_epd: true` in the output. Note the `address` (BLE MAC).
If only one EPD device is found, epd-tool remembers it automatically — you can omit `-a` in later commands.

### Step 3: Execute epd-tool commands

General format:

```bash
mars-cli exec <nuc_id> 'epd-tool <command> [options] --json' -t <timeout>
```

**Always add `--json` for machine-parseable output.**

### Step 4: Report results

Parse the JSON output and present results in a human-readable format. If `exit_code != 0`, explain the failure using `stderr`.

## Command Reference

### Device Discovery

| Command | Description | Timeout |
|---------|-------------|---------|
| `epd-tool scan --json` | Scan nearby EPD devices (`-d 5` for scan duration) | 30s |
| `epd-tool connect -a <addr> --json` | Connect and read device info | 30s |
| `epd-tool info -a <addr> --json` | Read firmware version | 30s |
| `epd-tool list-drivers --json` | List all supported screen models | 15s |
| `epd-tool list-adapters --json` | List Bluetooth adapters (Linux only) | 15s |

### Screen Operations

| Command | Description | Timeout |
|---------|-------------|---------|
| `epd-tool clear -a <addr> --json` | Clear screen to white | 30s |
| `epd-tool time -a <addr> --mode calendar --json` | Set calendar display mode | 30s |
| `epd-tool time -a <addr> --mode clock --json` | Set clock display mode | 30s |
| `epd-tool week-start <day> -a <addr> --json` | Set week start day (0=Sun, 1=Mon, ..., 6=Sat) | 30s |
| `epd-tool reset -a <addr> --json` | System reset | 30s |
| `epd-tool sleep -a <addr> --json` | Deep sleep (preserves display) | 30s |

### Image Operations (Most Common)

| Command | Description | Timeout |
|---------|-------------|---------|
| `epd-tool send-image <path> -a <addr> --json` | Send image to screen | 120s |
| `epd-tool send-image <path> -a <addr> --slot <n> --json` | Save image to slot | 120s |
| `epd-tool slots -a <addr> --json` | View slot status | 30s |
| `epd-tool show-slot <n> -a <addr> --json` | Display image from slot | 60s |
| `epd-tool free-slot <n> -a <addr> --json` | Delete slot image | 30s |
| `epd-tool slide <minutes> -a <addr> --json` | Start slideshow from slots | 30s |

### send-image Advanced Options

```bash
mars-cli exec <nuc_id> 'epd-tool send-image /path/to/image.png -a <addr> --json \
  --driver 0x06 \
  --contrast 1.2 \
  --brightness 1.0 \
  --dither floyd_steinberg \
  --strength 1.0 \
  --fit stretch \
  --slot 0 \
  --no-sleep' -t 180
```

Parameters:
- `--driver 0xNN` — Screen driver ID (auto-detected if omitted)
- `--contrast` — 0.5 to 2.0 (default 1.2)
- `--brightness` — 0.5 to 1.5 (default 1.0)
- `--dither` — Dithering algorithm (default: floyd_steinberg)
- `--strength` — Dither strength 0-5 (default 1.0)
- `--fit` — stretch / contain / cover (default: stretch)
- `--slot <n>` — Save to image slot instead of direct display
- `--no-sleep` — Skip deep sleep after sending

## Common Use Cases

### Send a URL image to the e-ink screen

```bash
# Download image on NUC
mars-cli exec <nuc_id> 'curl -sL -o /tmp/screen.png "https://example.com/image.png"' -t 60

# Send to e-ink display
mars-cli exec <nuc_id> 'epd-tool send-image /tmp/screen.png -a <addr> --json' -t 120
```

### Set up image slots and slideshow

```bash
# Check current slot status
mars-cli exec <nuc_id> 'epd-tool slots -a <addr> --json'

# Upload images to slots
mars-cli exec <nuc_id> 'epd-tool send-image /tmp/img1.png -a <addr> --slot 0 --json' -t 120
mars-cli exec <nuc_id> 'epd-tool send-image /tmp/img2.png -a <addr> --slot 1 --json' -t 120

# Start slideshow (switch every 30 minutes)
mars-cli exec <nuc_id> 'epd-tool slide 30 -a <addr> --json' -t 30
```

### Set calendar mode

```bash
mars-cli exec <nuc_id> 'epd-tool time -a <addr> --mode calendar --json' -t 30
```

### Clear screen

```bash
mars-cli exec <nuc_id> 'epd-tool clear -a <addr> --json' -t 30
```

## Supported Screen Models

| ID | Model | Mode | Resolution |
|----|-------|------|------------|
| 0x01 | 4.2" B&W (UC8176) | bw | 400x300 |
| 0x03 | 4.2" 3-color (UC8176) | 3color | 400x300 |
| 0x05 | 4.2" 4-color (JD79668) | 4color | 400x300 |
| 0x06 | 7.5" B&W (UC8179) | bw | 800x480 |
| 0x07 | 7.5" 3-color (UC8179) | 3color | 800x480 |
| 0x0C | 7.5" 4-color (JD79665) | 4color | 800x480 |
| 0x0A | 7.5" HD B&W (SSD1677) | bw | 880x528 |

Color modes: `bw` = black & white, `3color` = black/white/red, `4color` = black/white/red/yellow

## Timeout Guide

BLE operations are inherently slow. Use appropriate timeouts:

| Operation Type | Recommended `-t` |
|----------------|-------------------|
| scan | 30 |
| connect / info | 30 |
| clear | 30 |
| send-image (no slot) | 120 |
| send-image (with slot) | 180 |
| show-slot | 60 (includes 20s screen refresh) |
| time / week-start / reset / sleep | 30 |
| slots / free-slot / slide | 30 |

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `epd-tool: command not found` | Not installed on NUC | `pip install epd-tool` |
| No devices found | No device in BLE range | Check device power and proximity |
| Connection timeout | BLE connection failed | Retry or check adapter |
| Cannot read driver | Device config issue | Specify `--driver 0xNN` manually |
| SID ECC verification failed | Firmware mismatch | Upgrade firmware or use epdiy.cn |
| Command timeout | BLE transfer slow | Increase `-t` value |

## Notes

- Always use `--json` for parseable output
- `-a <addr>` specifies the BLE device address; obtain via `scan` first time
- Device address is auto-saved after first scan; subsequent commands can omit `-a`
- `send-image` is the most commonly used command — it handles color adaptation and dithering automatically
- After sending an image, the device enters deep sleep by default to preserve the display; use `--no-sleep` to skip
- BLE operations are naturally slow — always set sufficient timeout
