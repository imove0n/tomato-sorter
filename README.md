# 🍅 Tomato Sorter v2.0 — User Manual

> **A simple guide for operating the AI tomato sorting machine.**
> No technical knowledge required.

---

## 👋 Hi there!

This machine looks at tomatoes with a camera, decides if each one is
**RIPE**, **UNRIPE**, or **ROTTEN**, then automatically pushes it into
the correct bin. You don't need to type commands or know how computers
work — just follow the buttons on the screen.

---

## 📋 What's inside the box

When you receive the system, you should have:

- 🍓 A **Raspberry Pi 5** computer (small black box)
- 🖥️ A **7-inch touchscreen** (the display you'll look at)
- 📦 A **conveyor belt** with a tomato chute
- 🎥 A **camera** pointing at the conveyor
- 🌡️ **Two small sensors** (DHT22) — one per bin (measures temperature)
- 💨 **Two fans** — for cooling the bins
- 🤖 An **Arduino** (small green/blue board, hidden inside)
- 🔌 **Power supplies** (USB-C for Pi, 12V for the conveyor, 5V for servos)
- 🍅 **Three collection bins**: Bin 1 (Ripe), Bin 2 (Unripe), Bin 3 (Rotten)

---

## ⚡ How to start it (3 steps)

### Step 1: Plug it in
- Plug the **USB-C cable** into the Pi (the small computer)
- Plug the **12V power supply** into the wall
- Plug the **5V servo power** into the wall
- A red light on the Pi will turn on. The screen will start glowing.

### Step 2: Wait 30 seconds
- The screen will be black for a bit, then show the Pi logo
- After about half a minute, the **dashboard appears automatically**
- You'll see the tomato sorter dashboard fullscreen — dark theme, with
  buttons and panels

### Step 3: Press START CYCLE
- Look for the **green "START CYCLE" button** at the bottom-left
- Press it
- The conveyor will start moving forward
- Drop a tomato onto the conveyor — the machine takes care of the rest!

That's literally it. Press **STOP** (red button) when you're done.

---

## 🎯 What you'll see on the dashboard

```
┌──────────────────────────────────────────────────────────────────┐
│ TOMATO SORTER v2.0 — CONTROL DASHBOARD     📱  Exit  Reboot  ✕  │  ← Top header
├──────────────────────────────────────────────────────────────────┤
│                                       │ 🍅 Bin Counters         │
│   🎥 Live Detection                   │  Bin 1 (Ripe):    5     │  ← Right side panels
│      RIPE  92%                        │  Bin 2 (Unripe):  3     │
│      ████████░░  FPS: 6.0             │  Bin 3 (Rotten):  1     │
│   [View Live Camera →]                │                         │
│                                       │ 🌡️ Bin 1: 28°C / 65%    │
│                                       │ 🌡️ Bin 2: 27°C / 62%    │
│                                       │                         │
│                                       │ System Status:          │
│                                       │  Conveyor: FORWARD      │
│                                       │  IR: CLEAR              │
│                                       │  Fan 1: ON  Fan 2: ON   │
│                                       │                         │
│                                       │ Conveyor Speed: 60%     │
│                                       │ ───●─────────           │
├──────────────────────────────────────────────────────────────────┤
│  [START CYCLE]  [STOP]  [RESET]    Manual: [Sort Ripe] [Fwd]... │  ← Bottom controls
└──────────────────────────────────────────────────────────────────┘
```

### What each thing means (don't worry, just glance at this):

- **Bin Counters** — how many tomatoes of each type have been sorted so far
- **Live Detection** — what the camera is seeing right now, with a percentage confidence
- **Conveyor Speed** — how fast the belt is moving. You can drag the slider!
- **IR Sensor** — the little sensor at the sort point. Says `TRIGGERED` when a tomato passes it
- **Fan 1 / Fan 2** — air fans inside the bins to cool the tomatoes
- **Activity Timeline** — list of recently sorted tomatoes (scroll on the right)

---

## 🎬 Running a demo — step by step

**Before you start:**
- ✅ Make sure all power cables are plugged in
- ✅ Make sure the bins are positioned under the sorter chute
- ✅ Make sure the camera can see the conveyor clearly
- ✅ Have some tomatoes ready (ripe, unripe, and rotten if you want to test all 3)

**The demo:**

1. **Press the green `START CYCLE` button** (bottom-left of the screen)
   - The conveyor will start moving forward
   - You'll see "Watching conveyor — waiting for IR sensor" at the bottom
2. **Drop ONE tomato** onto the start of the conveyor
   - The camera will see it and identify it (you'll see RIPE/UNRIPE/ROTTEN on the screen)
3. **Watch the tomato travel** down the conveyor
   - When it reaches the sort point, the IR sensor catches it
   - The sorter flap moves to push it into the right bin
4. **Wait ~2 seconds**, then drop the NEXT tomato
   - One at a time! Don't dump them all at once.
5. **Bin counter goes up** — Bin 1, 2, or 3 increments by 1
6. **When done, press the red `STOP` button**

### 🐢 Tips for a clean demo

- **Slow down the conveyor** if tomatoes go too fast. Drag the speed slider to **60%** or **30%**. Lower speed = more reliable detection.
- **Wait between tomatoes** — give the sorter ~2 seconds to finish before dropping the next one.
- **Good lighting helps the camera**. If the room is dim, add a desk lamp.
- **Wipe the camera lens** if detection seems off (use a soft cloth).

---

## 📱 Showing the dashboard on your phone

The dashboard works on phones too! There are **3 ways**, depending on your situation:

### 🤔 Which one should you use?

```
Do you have WiFi where you're demoing?
│
├─ YES — and Pi is connected to it
│       └─→ Use Method A (LAN)            ← simplest
│       └─→ AND/OR Method C (Tunnel)      ← shareable to anyone online
│
└─ NO  — no WiFi available
        └─→ Use Method B (Hotspot)        ← Pi makes its own WiFi
```

### Method A: Same WiFi (easiest)

If your phone is on the same WiFi as the Pi:
1. On the dashboard, press **📱 Phone Access** (top-right button)
2. A window pops up with QR codes
3. Open your **phone camera**, point it at the QR code labeled "② Open the Dashboard"
4. Tap the link that pops up
5. The dashboard appears on your phone!

### Method B: Pi's own WiFi (no router needed) — *needs setup once*

Use this when there's NO WiFi available at your venue. The Pi creates
its own WiFi network for phones to join.

**To turn it on** (only one person needs to do this once):
- Have Herson run this once:
  ```
  sudo bash /home/bacadasa/tomato-sorter/deploy/hotspot-on.sh
  ```
- After that, the Pi broadcasts a WiFi network called **"TomatoSorter"**
- Password is **"tomato123"**

**To connect your phone:**
1. Press **📱 Phone Access** on the dashboard
2. **Scan QR #1** (① Join the WiFi) with your phone camera
3. Your phone auto-joins the TomatoSorter WiFi
4. **Scan QR #2** (② Open the Dashboard)
5. Done!

> ⚠️ While the hotspot is ON, the Pi can't reach the internet. Method C
> (below) won't work at the same time.

### Method C: Anyone in the world (needs internet)

Use this when you want to share the dashboard online — for example,
let your panel members watch the demo from home, or share progress
remotely.

> 🚨 **The Pi MUST be connected to the internet for this to work.**
> Without internet, this method does nothing.

**To turn it on** (only one person needs to do this once):
- Have Herson run this once:
  ```
  bash /home/bacadasa/tomato-sorter/deploy/install-tunnel.sh
  ```
- After that, the Pi will **automatically** create a public web link
  every time it boots — as long as it has internet.

**To share the link:**
1. Press **📱 Phone Access** on the dashboard
2. Scroll down to "Anywhere on the Internet"
3. The URL is shown — something like `https://random-words.trycloudflare.com`
4. Either:
   - Share the URL directly via chat / SMS
   - Have the other person scan the QR code with their phone camera

> 📝 The URL **changes every time the Pi restarts**. Always check the
> dashboard for the current URL before sharing.

---

## 🛑 How to turn it off

**To stop sorting** (but keep the system on):
- Press the red **STOP** button on the dashboard

**To shut down the Pi completely:**
- Press the **Shutdown** button at the top-right of the dashboard
- Confirm "Yes"
- Wait until the screen turns black
- **Then** unplug the power cables

> ⚠️ **Don't just yank the plug!** It can corrupt the SD card and ruin
> the system. Always use the Shutdown button first.

**To restart the Pi:**
- Press the **Reboot** button at the top-right
- Confirm "Yes"
- Wait ~30 seconds — the dashboard comes back automatically

**To use the Pi as a regular computer** (browse files, etc.):
- Press **Exit Kiosk** at the top-right
- The fullscreen dashboard closes, and you see the Pi's normal desktop
- The sorting system keeps running in the background — open any browser
  and go to `http://localhost:5000` to come back to the dashboard
- Or **double-click the "Tomato Sorter Kiosk" icon** on the desktop to
  return to fullscreen mode

---

## 🆘 If something goes wrong

### 🔴 "The dashboard didn't open after I plugged in the Pi"

**Wait 60 seconds first** — the Pi takes time to boot. The screen will
be black, then show the Pi logo, then a desktop, then the dashboard.

If after 1 full minute it's still not showing:
- Look for a **"Tomato Sorter Kiosk"** icon on the desktop. Double-click it.
- Or open the file manager → Desktop → double-click the icon
- If you can't see anything at all on the screen, the Pi may not be
  powered. Check that the USB-C cable is fully plugged in.

### 🟡 "The dashboard is frozen or stuck"

1. Try pressing **Reboot** at the top-right of the dashboard
2. Wait ~30 seconds
3. If that doesn't work, ask Herson

### 🟡 "I dropped a tomato but nothing happened"

- Is the conveyor actually moving? (You should hear a soft whirring)
- Did you press **START CYCLE** first?
- Did the camera see the tomato? (Watch the "Live Detection" panel — it should show RIPE/UNRIPE/ROTTEN with a percentage)
- Wait a bit longer — sometimes the IR sensor takes a moment to detect

### 🟡 "The sorter flap isn't moving"

The sorter (Servo 2 and 3) only moves when:
1. The cycle is running (you pressed START CYCLE), AND
2. The IR sensor catches the tomato

If you see numbers in the **Live Detection** panel (e.g. "RIPE 92%") but
no sorting happens after a few seconds, the IR sensor likely missed the
tomato. Check:
- Is the tomato actually passing in front of the IR sensor?
- Look at the IR sensor — does its red light blink when the tomato passes?

### 🟡 "Wrong tomato went into the wrong bin"

This usually means the camera misclassified it. Possible reasons:
- **Lighting too dim** — add more light on the conveyor
- **Tomato angle bad** — try rotating it
- **Tomato is partially blocked** by something on the conveyor

The accuracy depends on the YOLO model — it's not 100% perfect. For
borderline cases (e.g. half-ripe), errors are expected.

### 🟡 "I want to clear the bin counters"

Press the **Reset** button (gray, next to STOP). Confirm "Yes". All
counters go back to 0 and the timeline is cleared. This doesn't break
anything — it just clears the history.

### 🟡 "I clicked Exit Kiosk and now I don't know how to get back"

Look for the **"Tomato Sorter Kiosk"** icon on the desktop (probably
top-left). Double-click it. The dashboard fullscreen comes back.

### 🔴 "It says SERVO is UNKNOWN somewhere / not responding"

This is a deeper technical issue — the wrong software is loaded on the
Arduino. Ask Herson to run:
```
bash /home/bacadasa/tomato-sorter/deploy/flash-production.sh
```

### 🔴 "Conveyor doesn't move at all"

1. Is the 12V power supply plugged in and turned on?
2. Try pressing **Conveyor Fwd** in the Manual section
3. If the speed slider says 0%, drag it up to 60%+
4. If still nothing, ask Herson — there may be a loose wire

### 🔴 "I'm seeing red error messages everywhere"

Don't panic. Press **Reboot** at the top-right. Wait 30 seconds. If the
errors come back after reboot, take a photo of the screen and send it
to Herson.

---

## ❓ Frequently Asked Questions

### Does this need internet to work?

**Mostly no.** The sorting itself (camera, conveyor, sensors, dashboard)
works **fully offline**. The Pi doesn't need internet to detect tomatoes
and sort them.

**Only one feature needs internet:** Method C (public tunnel / shareable
URL). Without internet, you can still use the dashboard locally, and
phones nearby can still connect via Method A (same WiFi) or Method B
(Pi's hotspot).

### Can multiple phones connect at the same time?

Yes! Up to ~10 phones simultaneously is comfortable. They all see
live-updating data.

### Can someone on a phone press buttons too?

Yes — phones have **full control**, same as the Pi screen. Anyone can
press START, STOP, change speed, etc. (If you want phones to be
view-only, ask Herson to add that restriction.)

### Will the bin counts reset if I unplug the Pi?

No — counts are saved to the database. They survive reboots. Use the
**Reset** button on the dashboard if you want to start fresh.

### What if a tomato is so unusual the camera doesn't know what it is?

The system has a fallback: if the IR sensor catches a tomato but the
camera didn't classify it confidently, it defaults to **Unripe** (Bin
2). This is rare in practice.

### How long can I run this continuously?

For demos: as long as you want, no time limit.
For continuous production: the Pi runs hot under sustained use — make
sure the cooling fan on the Pi is working. Take a break every 30-60
minutes to let things cool down.

### How do I save the data for my thesis?

All sorting events are saved to `data/sorter.db` (a database file).
Ask Herson to export it to CSV — there's a script for it:
```
.venv/bin/python scripts/export_csv.py
```

---

## 🧰 Quick reference: What every button does

| Button | What it does |
|---|---|
| **START CYCLE** (green) | Start automatic sorting. Conveyor moves. |
| **STOP** (red) | Stop sorting. Conveyor stops. |
| **RESET** (gray) | Clear all bin counts and history. Asks for confirmation. |
| **📱 Phone Access** | Show QR codes to connect your phone |
| **Exit Kiosk** | Close fullscreen — see the Pi desktop |
| **Reboot** | Restart the Pi |
| **Shutdown** | Power off the Pi cleanly |
| **View Live Camera →** | Big fullscreen camera with bounding boxes |
| **Conveyor Fwd / Rev / Stop** | Move conveyor manually |
| **Servo 4 Open / Close** | Move the feeder servo manually |
| **Sort Ripe / Unripe / Rotten** | Move the sorter flap manually (test) |
| **Fan 1/2 On / Off** | Turn bin fans on or off |
| **Speed slider** | Drag to set conveyor speed (0-100%) |

---

## 📚 For more advanced info

If you (or Herson) need to:
- **See the wiring diagram** → open [docs/WIRING.md](docs/WIRING.md) or print [docs/Tomato_Sorter_v2_Wiring.pdf](docs/Tomato_Sorter_v2_Wiring.pdf)
- **Re-calibrate servos** → see [CHEATSHEET.md](CHEATSHEET.md) section 7
- **Understand the architecture** → see [ARCHITECTURE.md](ARCHITECTURE.md)
- **Modify the code** → see [CLAUDE.md](CLAUDE.md)

---

## 🧑‍🔧 Advanced commands (for tech people only)

Skip this section if you're just an operator! These are for when
something needs fixing or configuring.

### Service management
```bash
# Check if backend is running
systemctl is-active tomato-sorter

# Restart the backend
sudo systemctl restart tomato-sorter

# View live logs
journalctl -u tomato-sorter -f
```

### Network / sharing
```bash
# Turn ON Pi hotspot (Pi becomes a WiFi access point)
sudo bash /home/bacadasa/tomato-sorter/deploy/hotspot-on.sh

# Turn OFF Pi hotspot (reconnect to normal WiFi)
sudo bash /home/bacadasa/tomato-sorter/deploy/hotspot-off.sh

# Install + auto-start the public tunnel (requires Pi internet)
bash /home/bacadasa/tomato-sorter/deploy/install-tunnel.sh

# Check tunnel
sudo systemctl status tomato-tunnel
sudo systemctl restart tomato-tunnel       # get a new URL
```

### Re-flash Arduino firmware (if servo or IR misbehaves)
```bash
bash /home/bacadasa/tomato-sorter/deploy/flash-production.sh
```

### Test individual hardware
```bash
.venv/bin/python scripts/test_camera.py    # camera + detector standalone
.venv/bin/python scripts/test_dht22.py     # temperature/humidity sensors
.venv/bin/python scripts/ir_test.py        # IR sensor live monitor
```

### Re-build the wiring PDF after editing the markdown
```bash
.venv/bin/python scripts/build_wiring_pdf.py
```

### Edit cycle timing
Open `config/settings.yaml`, change values under `cycle:`, save, then:
```bash
sudo systemctl restart tomato-sorter
```

---

**Last updated:** 2026-06-27
**Built by:** Laurence "Killua" De Guzman
**For:** Technological University of the Philippines (TUP Manila) thesis defense
**Platform:** Raspberry Pi 5 (8GB) running Debian 13 Trixie

If you got this manual but no contact info — ask Killua. He built it.
