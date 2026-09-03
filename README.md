# 🎛️ DAW Studio Controller

A **Progressive Web App (PWA)** that turns your Android phone into a wireless MIDI controller for **REAPER** DAW, using **Bluetooth Low Energy (BLE)**.

![PWA Interface](screenshots/pwa-interface.png)
*Replace with screenshot of the PWA interface on your phone*

---

## ✨ Features

- 📱 **Wireless MIDI control** via Bluetooth Low Energy
- 🎹 **Transport controls**: Play, Stop, Record, Pause, Loop, Go to Start/End
- ↩️ **Edit controls**: Undo, Redo
- 🖥️ **Native Windows server** (no additional drivers needed)
- 📲 **Installable PWA** — works like a native app
- 🌐 **Fullscreen mode** for maximum control space
- 🔄 **Auto-updates** via service worker

---

## 📋 Requirements

### PC (Server)
- **Windows 10/11** with **Bluetooth 4.0+ (BLE)**
- **REAPER DAW** (v6.0 or later recommended)
- [DAW-MIDI-Server.exe](dist/DAW-MIDI-Server.exe) (pre-built, no installation needed)

### Phone (Client)
- **Android** with **Bluetooth 4.0+ (BLE)**
- **Chrome** browser (or any browser supporting Web Bluetooth)
- **HTTPS** connection (or localhost for testing)

---

## 🚀 Quick Setup

### Step 1: Start the Server on PC

1. Download `DAW-MIDI-Server.exe` from the [dist/](dist/) folder
2. Run the executable (no installation required)
3. Click **AVVIA** to start the BLE MIDI server

![Server Interface](screenshots/server-interface.png)
*Replace with screenshot of the server GUI showing "AVVIA" button*

> **Note:** Run as Administrator if you encounter Bluetooth permission issues.

### Step 2: Configure REAPER for OSC

This controller uses **OSC (Open Sound Control)** to communicate with REAPER. No virtual MIDI drivers needed!

1. Open **REAPER**
2. Go to **Options → Preferences → Audio → Control/websockets**
3. Click **Add** → Select **OSC**
4. Configure:
   - **Mode:** Accept incoming OSC messages
   - **Port:** `8000`
   - **IP:** `127.0.0.1` (localhost)
5. Click **OK**

![REAPER OSC Settings](screenshots/reaper-osc.png)
*Replace with screenshot of REAPER OSC preferences*

### Step 3: Map OSC Actions

The PWA sends OSC messages based on note numbers. Here's the default mapping:

| Button | Note | OSC Address | REAPER Action ID | Action |
|--------|------|-------------|------------------|--------|
| START | 59 | `/action/40042` | 40042 | Transport: Go to start of project |
| END | 66 | `/action/40043` | 40043 | Transport: Go to end of project |
| REC | 60 | `/action/1013` | 1013 | Transport: Record |
| PLAY | 61 | `/action/1007` | 1007 | Transport: Play |
| STOP | 62 | `/action/1016` | 1016 | Transport: Stop |
| PAUSE | 67 | `/action/1008` | 1008 | Transport: Pause |
| LOOP | 63 | `/action/1068` | 1068 | Transport: Toggle repeat |
| UNDO | 64 | `/action/40029` | 40029 | Edit: Undo |
| REDO | 65 | `/action/40030` | 40030 | Edit: Redo |

> **To find Action IDs in REAPER:** Open **Actions (?)** → search for the action → right-click → **Copy selected command ID**

### Step 4: Install & Connect the PWA

1. Open **Chrome** on your Android phone
2. Navigate to your PWA URL (or use the hosted version)
3. Tap **INSTALLA** to install the PWA (or use Chrome's "Add to Home Screen")
4. Open the PWA
5. Tap **CONNETTI** and select your PC from the Bluetooth device list

![Connection](screenshots/connection.png)
*Replace with screenshot of the connection flow*

---

## 🎮 Controls Layout

```
┌─────────┬─────────┬─────────┐
│  START  │   END   │  LOOP   │  ← Navigation
├─────────┼─────────┼─────────┼─────────┤
│   REC   │  PLAY   │  STOP   │ PAUSE   │  ← Transport (larger buttons)
├─────────┴─────────┴─────────┴─────────┤
│  UNDO   │  REDO   │         │         │  ← Edit
└───────────────────────────────────────┘
```

---

## 🔧 Troubleshooting

### Phone doesn't see the PC
- Ensure PC Bluetooth is **ON** and supports **BLE** (not just Classic Bluetooth)
- The PC appears with its **Windows name** (e.g., `DESKTOP-XXX`), not "DAW MIDI Server"
- Try using **nRF Connect** app to verify the PC is visible as a BLE device

### Connection fails
- Run `DAW-MIDI-Server.exe` as **Administrator**
- Check Windows Firewall isn't blocking the app
- Ensure the server shows "In attesa di connessioni..." before connecting

### REAPER doesn't respond
- Verify OSC is enabled in REAPER preferences (port 8000)
- Check that Action IDs match your REAPER version
- Ensure the server log shows `OSC-REAPER: nota XX -> azione YYYY (OK)`

### PWA doesn't install
- Must be served over **HTTPS** (or `localhost`)
- Requires a valid `manifest.json` and service worker

---

## 📁 Repository Structure

```
dawcontroller/
├── index.html          # PWA main file
├── manifest.json       # PWA manifest
├── sw.js               # Service worker (auto-updates)
├── remote.png          # App icon
├── dist/
│   └── DAW-MIDI-Server.exe   # Pre-built Windows server
├── screenshots/        # Documentation images (add your own)
└── README.md           # This file
```

---

## ⚠️ Important Notes

- **REAPER only:** This controller is designed specifically for REAPER DAW. It will not work with other DAWs without modification.
- **Windows only:** The server requires Windows 10/11 with BLE support.
- **OSC required:** REAPER must be configured to accept OSC messages (see Step 2).
- **No MIDI drivers:** Unlike traditional MIDI controllers, this uses OSC over BLE — no virtual MIDI cables needed.

---

## 🛠️ Building from Source (Optional)

If you want to modify the server:

```bash
# Install dependencies
pip install bleak pyinstaller

# Build EXE
pyinstaller --onefile --noconsole --icon=remote.png --name "DAW-MIDI-Server" ble_midi_server.py
```

---

## 📜 License

MIT License — feel free to modify and distribute.

---

## 🙏 Credits

- Built with [Bleak](https://github.com/hbldh/bleak) (BLE library)
- PWA powered by vanilla JavaScript
- Tested with REAPER v7 on Windows 11
