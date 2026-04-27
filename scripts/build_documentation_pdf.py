#!/usr/bin/env python3
"""
Build a professional PDF documentation for the Tomato Sorter v2.0 thesis prototype.

Output: docs/Tomato_Sorter_v2_Documentation.pdf
"""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageBreak, PageTemplate, Paragraph,
    Spacer, Table, TableStyle, KeepTogether, NextPageTemplate,
)

OUT_DIR = Path("docs")
OUT_DIR.mkdir(exist_ok=True)
OUT_PDF = OUT_DIR / "Tomato_Sorter_v2_Documentation.pdf"

# ---------- Color palette (industrial / academic) ----------
NAVY    = colors.HexColor("#1a2b4a")
ACCENT  = colors.HexColor("#b91c1c")   # tomato red
GREY    = colors.HexColor("#475569")
LIGHT   = colors.HexColor("#f1f5f9")
BORDER  = colors.HexColor("#cbd5e1")
TEXT    = colors.HexColor("#1e293b")

# ---------- Styles ----------
styles = getSampleStyleSheet()

title_style = ParagraphStyle("Title", parent=styles["Title"],
    fontName="Helvetica-Bold", fontSize=26, leading=32, alignment=TA_CENTER,
    textColor=NAVY, spaceAfter=8)

subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"],
    fontName="Helvetica", fontSize=13, alignment=TA_CENTER,
    textColor=GREY, spaceAfter=24)

h1_style = ParagraphStyle("H1", parent=styles["Heading1"],
    fontName="Helvetica-Bold", fontSize=16, leading=20,
    textColor=NAVY, spaceBefore=20, spaceAfter=10,
    borderPadding=(0, 0, 4, 0))

h2_style = ParagraphStyle("H2", parent=styles["Heading2"],
    fontName="Helvetica-Bold", fontSize=12, leading=16,
    textColor=ACCENT, spaceBefore=12, spaceAfter=6)

body_style = ParagraphStyle("Body", parent=styles["BodyText"],
    fontName="Helvetica", fontSize=10.5, leading=15,
    alignment=TA_JUSTIFY, textColor=TEXT, spaceAfter=8)

bullet_style = ParagraphStyle("Bullet", parent=body_style,
    leftIndent=18, bulletIndent=6, spaceAfter=3)

mono_style = ParagraphStyle("Mono", parent=body_style,
    fontName="Courier", fontSize=9.5, leading=13,
    backColor=LIGHT, borderColor=BORDER, borderWidth=0.5,
    borderPadding=8, leftIndent=0, rightIndent=0, spaceAfter=10)

cover_label_style = ParagraphStyle("CoverLabel", parent=styles["Normal"],
    fontName="Helvetica-Bold", fontSize=10, alignment=TA_CENTER,
    textColor=GREY, spaceAfter=4)

cover_value_style = ParagraphStyle("CoverValue", parent=styles["Normal"],
    fontName="Helvetica", fontSize=11, alignment=TA_CENTER,
    textColor=TEXT, spaceAfter=12)

# ---------- Page templates ----------
def header_footer(canvas, doc):
    canvas.saveState()
    width, height = A4

    # Top accent bar
    canvas.setFillColor(NAVY)
    canvas.rect(0, height - 1.0 * cm, width, 1.0 * cm, stroke=0, fill=1)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, height - 1.1 * cm, width, 0.1 * cm, stroke=0, fill=1)

    # Header text
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(2 * cm, height - 0.65 * cm, "TOMATO SORTER v2.0")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(width - 2 * cm, height - 0.65 * cm,
                           "Thesis Prototype Documentation")

    # Footer
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(2 * cm, 1.5 * cm, width - 2 * cm, 1.5 * cm)
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(GREY)
    canvas.drawString(2 * cm, 1.0 * cm,
                      "Laurence De Guzman  |  TUP Manila")
    canvas.drawRightString(width - 2 * cm, 1.0 * cm,
                           f"Page {doc.page}")
    canvas.restoreState()


def cover_page(canvas, doc):
    canvas.saveState()
    width, height = A4

    # Full navy background
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, width, height, stroke=0, fill=1)

    # Accent stripe
    canvas.setFillColor(ACCENT)
    canvas.rect(0, height - 12 * cm, width, 0.3 * cm, stroke=0, fill=1)

    # Title block
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 32)
    canvas.drawCentredString(width / 2, height - 8 * cm, "Tomato Sorter v2.0")

    canvas.setFont("Helvetica", 14)
    canvas.drawCentredString(width / 2, height - 9.2 * cm,
                             "AI-Powered Tomato Sorting System")

    canvas.setFont("Helvetica-Oblique", 11)
    canvas.setFillColor(colors.HexColor("#cbd5e1"))
    canvas.drawCentredString(width / 2, height - 10.0 * cm,
                             "Raspberry Pi 5  |  Arduino Uno  |  YOLO11n  |  Flask")

    # Bottom info
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(colors.white)
    canvas.drawCentredString(width / 2, 5.0 * cm, "PROTOTYPE DOCUMENTATION")

    canvas.setFont("Helvetica", 11)
    canvas.drawCentredString(width / 2, 4.2 * cm, "Laurence De Guzman")
    canvas.drawCentredString(width / 2, 3.6 * cm,
                             "Technological University of the Philippines, Manila")
    canvas.drawCentredString(width / 2, 3.0 * cm, "April 2026")

    canvas.restoreState()


# ---------- Helpers ----------
def make_table(data, col_widths=None, header=True):
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    style = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, 0), "LEFT"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    t.setStyle(TableStyle(style))
    return t


def code_block(text):
    safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe = safe.replace("\n", "<br/>").replace(" ", "&nbsp;")
    return Paragraph(safe, mono_style)


# ---------- Content sections ----------
def build_story():
    story = []

    # ----- COVER PAGE (drawn by cover_page template) -----
    story.append(Spacer(1, 0.1))   # placeholder for cover
    story.append(NextPageTemplate("body"))
    story.append(PageBreak())

    # ----- 1. EXECUTIVE SUMMARY -----
    story.append(Paragraph("1. Executive Summary", h1_style))
    story.append(Paragraph(
        "This document describes the design and implementation of the Tomato "
        "Sorter v2.0, an automated tomato classification and sorting system "
        "developed as a thesis prototype. The system uses a YOLO11n deep "
        "learning model running on a Raspberry Pi 5 to classify tomatoes by "
        "ripeness condition (ripe, unripe, or rotten) and physically sort them "
        "into the appropriate storage bins through a conveyor and servo "
        "mechanism controlled by an Arduino Uno. A real-time web dashboard "
        "running in kiosk mode on a 7-inch touchscreen display provides live "
        "monitoring, environmental data from dual DHT22 sensors, and manual "
        "control of the system.", body_style))
    story.append(Paragraph(
        "The system is designed to operate fully offline (no internet required), "
        "auto-launch on boot, and survive component failures through systemd "
        "service auto-restart. From power-on to fully operational dashboard "
        "takes approximately 30 seconds.", body_style))

    # ----- 2. SYSTEM ARCHITECTURE -----
    story.append(Paragraph("2. System Architecture", h1_style))
    story.append(Paragraph(
        "The system is built on a 5-layer software architecture with strict "
        "separation of concerns. Each layer communicates only with the layer "
        "directly below it, or via an in-memory event bus, ensuring components "
        "remain testable and replaceable in isolation.", body_style))

    arch_data = [
        ["Layer", "Module", "Responsibility"],
        ["Layer 4", "api/",         "Web interface (Flask + WebSocket)"],
        ["Layer 3", "app/",         "Orchestration, state, event bus"],
        ["Layer 2", "services/",    "Stateless workers (detector, sensors, classifier)"],
        ["Layer 1", "hardware/",    "Pure I/O wrappers (camera, GPIO, DHT22)"],
        ["Layer 5", "persistence/", "SQLite database, CSV exporter"],
    ]
    story.append(make_table(arch_data, [2.2 * cm, 3 * cm, 10 * cm]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Hardware Control Split", h2_style))
    story.append(Paragraph(
        "Compute and real-time control responsibilities are split between two "
        "boards. The Raspberry Pi 5 handles AI inference, the dashboard, "
        "logging, and high-level orchestration. The Arduino Uno handles "
        "real-time hardware control where microsecond precision is required, "
        "such as servo PWM and IR sensor interrupt handling. The two boards "
        "communicate over USB serial at 9600 baud through the device file "
        "<font face='Courier'>/dev/ttyACM0</font>.", body_style))

    split_data = [
        ["Raspberry Pi 5 handles", "Arduino Uno handles"],
        ["Camera capture + YOLO inference", "Servo 1 (gate) — hardware PWM"],
        ["Flask web dashboard",            "Servo 2 (sorter) — hardware PWM"],
        ["SQLite event logging",           "IR sensor (interrupt-driven)"],
        ["DHT22 temperature/humidity",     "Relay 1 / Relay 2 (fan control)"],
        ["BTS7960 conveyor PWM",           "Serial command parsing"],
        ["WebSocket live updates",         ""],
    ]
    story.append(make_table(split_data, [8 * cm, 8 * cm]))

    story.append(PageBreak())

    # ----- 3. MATERIALS LIST -----
    story.append(Paragraph("3. Materials and Components", h1_style))
    story.append(Paragraph(
        "The complete bill of materials for the prototype is organized below "
        "by functional category.", body_style))

    story.append(Paragraph("3.1 Main Processing Unit", h2_style))
    story.append(make_table([
        ["Component", "Specification", "Qty"],
        ["Raspberry Pi 5", "8GB RAM, Debian 13 Trixie OS", "1"],
        ["7-inch DSI Touchscreen", "DSI cable + 5V/GND on pins 4 and 6", "1"],
        ["MicroSD Card", "32GB", "1"],
        ["Pi 5 USB-C Power Adapter", "5V / 5A official", "1"],
        ["Active Cooling Fan", "For sustained CPU inference", "1"],
    ], [5.5 * cm, 8.5 * cm, 1.5 * cm]))

    story.append(Paragraph("3.2 Microcontroller", h2_style))
    story.append(make_table([
        ["Component", "Specification", "Qty"],
        ["Arduino Uno", "ATmega328P, hardware PWM control", "1"],
        ["USB-A to USB-B Cable", "Pi-Arduino link (power + serial)", "1"],
    ], [5.5 * cm, 8.5 * cm, 1.5 * cm]))

    story.append(Paragraph("3.3 Vision and AI", h2_style))
    story.append(make_table([
        ["Component", "Specification", "Qty"],
        ["USB Camera", "640x480, /dev/video0", "1"],
        ["YOLO11n Model", "NCNN format, 3 classes, 480x480 input", "1"],
    ], [5.5 * cm, 8.5 * cm, 1.5 * cm]))

    story.append(Paragraph("3.4 Actuation", h2_style))
    story.append(make_table([
        ["Component", "Specification", "Qty"],
        ["Servo Motor (Gate)", "Releases tomatoes one at a time", "1"],
        ["Servo Motor (Sorter)", "180 deg — left=ripe, center=unripe, right=rotten", "1"],
        ["BTS7960 Motor Driver", "H-bridge for 12V DC conveyor motor", "1"],
        ["DC Conveyor Motor", "12V DC", "1"],
    ], [5.5 * cm, 8.5 * cm, 1.5 * cm]))

    story.append(Paragraph("3.5 Sensing", h2_style))
    story.append(make_table([
        ["Component", "Specification", "Qty"],
        ["DHT22 Sensor", "Temperature/humidity — Bin 1 (ripe)", "1"],
        ["DHT22 Sensor", "Temperature/humidity — Bin 2 (unripe)", "1"],
        ["IR Sensor", "Detects tomato at sort point", "1"],
    ], [5.5 * cm, 8.5 * cm, 1.5 * cm]))

    story.append(Paragraph("3.6 Power Supplies", h2_style))
    story.append(make_table([
        ["Component", "Specification", "Qty"],
        ["12V Power Supply", "Conveyor motor + fans (via relay)", "1"],
        ["5V Power Supply", "2A min — Servo 1 and Servo 2", "1"],
    ], [5.5 * cm, 8.5 * cm, 1.5 * cm]))

    story.append(Paragraph("3.7 Relay and Cooling", h2_style))
    story.append(make_table([
        ["Component", "Specification", "Qty"],
        ["Dual Relay Module", "Controls Fan 1 and Fan 2", "1"],
        ["DC Fan", "Bin 1 ventilation (ripe)", "1"],
        ["DC Fan", "Bin 2 ventilation (unripe)", "1"],
    ], [5.5 * cm, 8.5 * cm, 1.5 * cm]))

    story.append(Paragraph("3.8 Wiring and Prototyping", h2_style))
    story.append(make_table([
        ["Component", "Specification", "Qty"],
        ["Breadboard", "Full-size", "3"],
        ["Jumper Wires", "Assorted M-M, M-F, F-F", "1 set"],
    ], [5.5 * cm, 8.5 * cm, 1.5 * cm]))

    story.append(Paragraph("3.9 Storage Bins", h2_style))
    story.append(make_table([
        ["Bin", "Class", "DHT22 Sensor", "Cooling Fan"],
        ["Bin 1", "Ripe",   "Yes", "Yes (Relay 1)"],
        ["Bin 2", "Unripe", "Yes", "Yes (Relay 2)"],
        ["Bin 3", "Rotten", "No",  "No"],
    ], [2.5 * cm, 4 * cm, 4.5 * cm, 4.5 * cm]))

    story.append(PageBreak())

    # ----- 4. SORTING WORKFLOW -----
    story.append(Paragraph("4. Sorting Workflow", h1_style))
    story.append(Paragraph(
        "The complete operational cycle of the system is shown below. The "
        "key safety rule is that only one tomato is allowed on the conveyor "
        "at any time. Servo 1 only opens the gate after Servo 2 has finished "
        "sorting the previous tomato.", body_style))

    story.append(code_block(
        "1.  Servo 1 (gate) opens briefly\n"
        "2.  One tomato falls onto the conveyor\n"
        "3.  Servo 1 closes quickly\n"
        "4.  Conveyor runs (12V motor via BTS7960)\n"
        "5.  USB camera captures tomato\n"
        "6.  YOLO11n classifies as ripe / unripe / rotten\n"
        "7.  Detection logged to SQLite database\n"
        "8.  IR sensor at end of conveyor detects tomato arrival\n"
        "9.  Pi commands Arduino to rotate Servo 2:\n"
        "       Left   = Ripe   -> Bin 1\n"
        "       Center = Unripe -> Bin 2\n"
        "       Right  = Rotten -> Bin 3\n"
        "10. Servo 2 holds for ~600ms (tomato falls into bin)\n"
        "11. Servo 2 returns to home position\n"
        "12. Servo 1 opens again -> next tomato -> repeat"))

    story.append(Paragraph(
        "If the camera fails to detect a tomato (poor lighting, occlusion, "
        "or speed mismatch), the system applies a safe fallback: the tomato "
        "is sorted as 'unripe' to prevent good produce from being discarded.",
        body_style))

    # ----- 5. PI <-> ARDUINO PROTOCOL -----
    story.append(Paragraph("5. Pi-Arduino Communication Protocol", h1_style))
    story.append(Paragraph(
        "Serial communication operates at 9600 baud over USB. Commands are "
        "newline-terminated ASCII strings. The Pi initiates most exchanges; "
        "the Arduino additionally publishes asynchronous events when the IR "
        "sensor triggers.", body_style))

    story.append(Paragraph("Pi to Arduino (Commands)", h2_style))
    story.append(make_table([
        ["Command", "Action"],
        ["SERVO1:OPEN",      "Gate opens briefly"],
        ["SERVO1:CLOSE",     "Gate closes"],
        ["SERVO2:LEFT",      "Sort to ripe bin"],
        ["SERVO2:CENTER",    "Sort to unripe bin"],
        ["SERVO2:RIGHT",     "Sort to rotten bin"],
        ["RELAY1:ON / OFF",  "Fan 1 control"],
        ["RELAY2:ON / OFF",  "Fan 2 control"],
    ], [5 * cm, 11 * cm]))

    story.append(Paragraph("Arduino to Pi (Events)", h2_style))
    story.append(make_table([
        ["Message", "Meaning"],
        ["IR:TRIGGERED", "Tomato detected at sort point"],
        ["SERVO1:DONE",  "Gate movement complete"],
        ["SERVO2:DONE",  "Sorter movement complete"],
        ["OK",           "Generic acknowledgement"],
    ], [5 * cm, 11 * cm]))

    story.append(PageBreak())

    # ----- 6. SOFTWARE STACK -----
    story.append(Paragraph("6. Software Stack", h1_style))
    story.append(make_table([
        ["Software", "Purpose"],
        ["Python 3.13", "Main language on the Pi"],
        ["OpenCV (system, GTK/Qt5)", "Camera capture and image preprocessing"],
        ["NCNN", "YOLO inference (ARM-optimized, 2-3x faster than PyTorch)"],
        ["Flask + Flask-SocketIO", "Web server and real-time WebSocket updates"],
        ["SQLite", "Detection, sensor, and event logging"],
        ["gpiozero + lgpio", "Pi 5 GPIO control (RP1 chip compatible)"],
        ["adafruit-circuitpython-dht", "DHT22 sensor reading"],
        ["pyserial", "Pi to Arduino serial communication"],
        ["Arduino IDE / C++", "Arduino Uno firmware"],
        ["systemd", "Service auto-start and auto-restart on boot"],
        ["Chromium", "Kiosk-mode dashboard display"],
    ], [5 * cm, 11 * cm]))

    # ----- 7. POWER DISTRIBUTION -----
    story.append(Paragraph("7. Power Distribution", h1_style))
    story.append(Paragraph(
        "The system uses three independent power sources, all sharing a common "
        "ground reference. This isolation prevents brown-outs on the Pi caused "
        "by inrush current from servos and motors.", body_style))

    story.append(make_table([
        ["Source", "Powers"],
        ["Pi USB-C Adapter (5V/5A)", "Raspberry Pi 5 only"],
        ["12V Power Supply",         "Conveyor (via BTS7960) + fans (via relay load side)"],
        ["5V Power Supply (2A+)",    "Servo 1 and Servo 2"],
        ["Pi 5V GPIO pin",           "DHT22 sensors, IR sensor logic, relay coil VCC"],
        ["Pi USB to Arduino",        "Powers Arduino + provides serial link"],
    ], [5.5 * cm, 10.5 * cm]))

    # ----- 8. DASHBOARD -----
    story.append(Paragraph("8. Dashboard Interface", h1_style))
    story.append(Paragraph(
        "The dashboard runs in Chromium kiosk mode on the 7-inch DSI display "
        "at <font face='Courier'>http://localhost:5000</font>. The interface "
        "follows an industrial SCADA design pattern: clean, neutral dark "
        "theme, no decorative animations, optimized for unattended operation.",
        body_style))

    story.append(Paragraph("Dashboard Features", h2_style))
    for item in [
        "Live camera feed with detection bounding boxes overlaid in real-time",
        "Bin counters: Bin 1 (Ripe), Bin 2 (Unripe), Bin 3 (Rotten)",
        "Environmental gauges: temperature and humidity per bin",
        "System status: conveyor, fans, servo positions",
        "Manual fan toggles and servo calibration sliders",
        "Activity log: last 10 detections with timestamp and confidence",
        "WebSocket push updates approximately every 500 ms",
    ]:
        story.append(Paragraph(f"&bull;&nbsp;&nbsp;{item}", bullet_style))

    story.append(PageBreak())

    # ----- 9. RELIABILITY -----
    story.append(Paragraph("9. Reliability and Risk Mitigation", h1_style))
    story.append(make_table([
        ["Risk", "Mitigation"],
        ["DHT22 read failures (40-60% normal)", "Caching layer; UI shows real vs cached badge"],
        ["Pi CPU overheating during long runs", "Active cooler + thermal alarm in dashboard"],
        ["Service crash mid-operation",         "systemd auto-restart on failure"],
        ["Camera misses detection",             "Fallback class = unripe (safe default)"],
        ["Network failure on demo day",         "Fully local — no internet required"],
        ["SD card corruption",                  "Regular DB backups; NVMe SSD recommended"],
    ], [6.5 * cm, 9.5 * cm]))

    # ----- 10. BOOT SEQUENCE -----
    story.append(Paragraph("10. Boot Sequence", h1_style))
    story.append(Paragraph(
        "When the Raspberry Pi is powered on, the following sequence runs "
        "automatically without user intervention:", body_style))

    story.append(code_block(
        "1.  Debian Trixie boots and auto-logs in as user 'bacadasa'\n"
        "2.  systemd starts three services in order:\n"
        "       - tomato-sensors.service   (DHT22 polling loop)\n"
        "       - tomato-detector.service  (Camera + YOLO inference)\n"
        "       - tomato-dashboard.service (Flask web server)\n"
        "3.  Wayfire compositor launches the desktop\n"
        "4.  Chromium opens fullscreen at http://localhost:5000\n"
        "5.  Dashboard is fully operational\n\n"
        "Total boot-to-dashboard time: approximately 30 seconds."))

    # ----- 11. CONCLUSION -----
    story.append(Paragraph("11. Conclusion", h1_style))
    story.append(Paragraph(
        "Tomato Sorter v2.0 demonstrates a panel-grade integration of edge AI "
        "inference, real-time microcontroller hardware control, and a "
        "production-quality web dashboard on consumer-grade hardware. The "
        "5-layer software architecture ensures each subsystem can be tested, "
        "replaced, or extended independently. The split between the Raspberry "
        "Pi and the Arduino provides the best of both worlds: high-level "
        "Linux services for AI and web, and microcontroller precision for "
        "real-time actuation.", body_style))
    story.append(Paragraph(
        "All configuration is externalized to YAML, all events are logged to "
        "SQLite for reproducible analysis, and the system auto-launches in "
        "kiosk mode for unattended operation. The result is a system that "
        "is not only functional but defensible to a thesis review panel as "
        "an example of clean engineering practice on embedded hardware.",
        body_style))

    return story


def build_pdf():
    doc = BaseDocTemplate(
        str(OUT_PDF),
        pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title="Tomato Sorter v2.0 — Prototype Documentation",
        author="Laurence De Guzman",
    )
    cover_frame = Frame(0, 0, A4[0], A4[1], leftPadding=0, rightPadding=0,
                        topPadding=0, bottomPadding=0, id="cover")
    body_frame  = Frame(2 * cm, 2 * cm, A4[0] - 4 * cm, A4[1] - 4 * cm,
                        id="body")

    doc.addPageTemplates([
        PageTemplate(id="cover", frames=cover_frame, onPage=cover_page),
        PageTemplate(id="body",  frames=body_frame,  onPage=header_footer),
    ])

    story = build_story()
    doc.build(story)
    print(f"PDF generated: {OUT_PDF.resolve()}")


if __name__ == "__main__":
    build_pdf()
