#!/usr/bin/env python3
"""
Build a clean PDF wiring guide for the Tomato Sorter v2.0.

Output: docs/Tomato_Sorter_v2_Wiring.pdf

Pin data mirrors docs/WIRING.md (verified against the production firmware
and config/settings.yaml). Run after editing WIRING.md to keep the PDF in sync.
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageBreak, PageTemplate, Paragraph,
    Preformatted, Spacer, Table, TableStyle,
)

OUT_DIR = Path("docs")
OUT_DIR.mkdir(exist_ok=True)
OUT_PDF = OUT_DIR / "Tomato_Sorter_v2_Wiring.pdf"

# ---------- palette ----------
NAVY   = colors.HexColor("#1a2b4a")
ACCENT = colors.HexColor("#b91c1c")
GREY   = colors.HexColor("#475569")
LIGHT  = colors.HexColor("#f1f5f9")
BORDER = colors.HexColor("#cbd5e1")
TEXT   = colors.HexColor("#1e293b")
WARN   = colors.HexColor("#fef3c7")
WARNBD = colors.HexColor("#f59e0b")

styles = getSampleStyleSheet()

title_style = ParagraphStyle("T", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=26, leading=32, alignment=TA_CENTER, textColor=NAVY, spaceAfter=8)
subtitle_style = ParagraphStyle("S", parent=styles["Normal"], fontName="Helvetica",
    fontSize=13, alignment=TA_CENTER, textColor=GREY, spaceAfter=20)
h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold",
    fontSize=15, leading=19, textColor=NAVY, spaceBefore=16, spaceAfter=8)
h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=11.5, leading=15, textColor=ACCENT, spaceBefore=10, spaceAfter=5)
body = ParagraphStyle("B", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=10, leading=14, textColor=TEXT, spaceAfter=6)
mono = ParagraphStyle("M", parent=styles["BodyText"], fontName="Courier",
    fontSize=8.2, leading=10.5, textColor=TEXT, backColor=LIGHT,
    borderColor=BORDER, borderWidth=0.5, borderPadding=7, spaceAfter=10)
warn = ParagraphStyle("W", parent=body, fontSize=10, textColor=colors.HexColor("#92400e"),
    backColor=WARN, borderColor=WARNBD, borderWidth=1, borderPadding=8, spaceAfter=10)


def tbl(data, col_widths):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("TEXTCOLOR", (0, 1), (-1, -1), TEXT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(2*cm, A4[1]-1.6*cm, A4[0]-2*cm, A4[1]-1.6*cm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GREY)
    canvas.drawString(2*cm, A4[1]-1.4*cm, "Tomato Sorter v2.0 — Wiring Guide")
    canvas.drawRightString(A4[0]-2*cm, A4[1]-1.4*cm, "Hardware Reference")
    canvas.line(2*cm, 1.5*cm, A4[0]-2*cm, 1.5*cm)
    canvas.drawCentredString(A4[0]/2, 1.1*cm, f"Page {doc.page}")
    canvas.restoreState()


def build():
    doc = BaseDocTemplate(str(OUT_PDF), pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    frame = Frame(doc.leftMargin, doc.bottomMargin,
                  doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=header_footer)])

    e = []  # elements

    # ---- cover ----
    e.append(Spacer(1, 4*cm))
    e.append(Paragraph("Tomato Sorter v2.0", title_style))
    e.append(Paragraph("Complete Wiring Diagram &amp; Bill of Materials", subtitle_style))
    e.append(Spacer(1, 0.5*cm))
    e.append(Paragraph(
        "Hardware reference for recreating the AI-powered tomato sorting "
        "system. All pin assignments verified against the production "
        "firmware and configuration files.", body))
    e.append(Spacer(1, 0.5*cm))
    e.append(Paragraph(
        "<b>Platform:</b> Raspberry Pi 5 (8GB) + Arduino Uno<br/>"
        "<b>Detection:</b> YOLO11n NCNN — ripe / unripe / rotten<br/>"
        "<b>Classes &amp; bins:</b> Bin 1 Ripe, Bin 2 Unripe, Bin 3 Rotten", body))
    e.append(PageBreak())

    # ---- 1. BOM ----
    e.append(Paragraph("1. Bill of Materials", h1))
    bom = [["#", "Component", "Spec / Model", "Qty", "Notes"]]
    for row in [
        ["1", "Raspberry Pi 5", "Model B, 8GB", "1", "YOLO + dashboard"],
        ["2", "Arduino Uno", "or CH340 clone", "1", "servos, IR, relays"],
        ["3", "USB Camera", "UVC, >=640x480", "1", "V4L2"],
        ["4", "7-inch DSI Display", "Official Pi screen", "1", "kiosk dashboard"],
        ["5", "DHT22 (AM2302)", "temp/humidity", "2", "ripe + unripe bins"],
        ["6", "Servo motor", "SG90 / MG996R", "3", "Servo 2, 3, 4"],
        ["7", "IR obstacle sensor", "FC-51 active-low", "1", "sort-point trigger"],
        ["8", "Dual relay module", "12V coil, active-LOW", "1", "drives 2 fans"],
        ["9", "DC fans", "12V", "2", "bin cooling"],
        ["10", "DC motor", "12V geared", "1", "conveyor belt"],
        ["11", "BTS7960 driver", "43A H-bridge", "1", "conveyor PWM"],
        ["12", "5V PSU (external)", ">=3A", "1", "all servos"],
        ["13", "12V PSU", ">=5A", "1", "conveyor + fans"],
        ["14", "Breadboard + jumpers", "-", "-", "power rails"],
    ]:
        bom.append(row)
    e.append(tbl(bom, [0.9*cm, 3.4*cm, 3.6*cm, 1*cm, 4*cm]))

    # ---- 2. Power ----
    e.append(Paragraph("2. Power Architecture", h1))
    e.append(Paragraph("Three separate power domains. All grounds MUST tie together.", body))
    e.append(Preformatted(
        "USB-C 5V/5A  --> Raspberry Pi 5 (+ 7\" DSI display)\n"
        "External 5V  --> Servo 2, Servo 3, Servo 4  (V+ and V-)\n"
        "                 (Arduino sends ONLY signal wires)\n"
        "12V PSU      --> BTS7960 (conveyor motor)\n"
        "             --> Relay load side --> Fans", mono))
    e.append(Paragraph(
        "<b>&#9888; The #1 mistake: missing common ground.</b> ALL grounds "
        "must be commoned:  Pi GND + Arduino GND + External 5V (-) + 12V (-) "
        "+ BTS7960 GND. Without a shared ground, servos will not respond to "
        "signal pulses even when powered.", warn))

    e.append(PageBreak())

    # ---- 3. Pi GPIO ----
    e.append(Paragraph("3. Raspberry Pi 5 — GPIO Connections", h1))
    e.append(Paragraph("Pi 5 uses the RP1 chip — use gpiozero + lgpio (NOT RPi.GPIO).", body))
    pi = [["Pi Function", "BCM GPIO", "Phys Pin", "Connects To"]]
    for row in [
        ["DHT22 #1 (Ripe) data", "GPIO 4", "Pin 7", "DHT22 #1 DATA"],
        ["DHT22 #2 (Unripe) data", "GPIO 23", "Pin 16", "DHT22 #2 DATA"],
        ["Conveyor RPWM", "GPIO 18", "Pin 12", "BTS7960 RPWM"],
        ["Conveyor LPWM", "GPIO 19", "Pin 35", "BTS7960 LPWM"],
        ["3.3V power", "-", "Pin 1 / 17", "DHT22 VCC (both)"],
        ["5V power", "-", "Pin 2 / 4", "BTS7960 VCC, R_EN, L_EN"],
        ["Ground", "-", "Pin 6/9/14/...", "Common GND rail"],
        ["Arduino link", "-", "USB", "Arduino (/dev/ttyUSB0)"],
        ["Camera", "-", "USB", "USB webcam"],
        ["Display", "-", "DSI", "7\" DSI screen"],
    ]:
        pi.append(row)
    e.append(tbl(pi, [4.6*cm, 2.4*cm, 2.6*cm, 4.2*cm]))
    e.append(Paragraph("DHT22 wiring (x2, identical except data pin):", h2))
    e.append(Preformatted(
        "DHT22          Raspberry Pi\n"
        "VCC (+)   ---> 3.3V  (pin 1 or 17)\n"
        "DATA      ---> GPIO 4 (ripe) / GPIO 23 (unripe)\n"
        "GND (-)   ---> GND\n"
        "(10k pull-up VCC<->DATA if bare sensor; most boards have it)", mono))

    # ---- 4. Arduino ----
    e.append(Paragraph("4. Arduino Uno — Connections", h1))
    ard = [["Arduino Pin", "Function", "Connects To", "Notes"]]
    for row in [
        ["D2", "IR sensor input", "IR module OUT", "active LOW = detected"],
        ["D4", "Relay 1 control", "Relay IN1", "active LOW -> Fan 1"],
        ["D7", "Relay 2 control", "Relay IN2", "active LOW -> Fan 2"],
        ["D8", "Servo 4 signal", "Servo 4 signal", "open=75 closed=0"],
        ["D9", "Servo 1 (DISABLED)", "-", "retired"],
        ["D10", "Servo 2 signal", "Servo 2 signal", "open=0 closed=89"],
        ["D11", "Servo 3 signal", "Servo 3 signal", "open=90 closed=0"],
        ["5V", "Logic 5V", "Relay VCC", "relay logic only"],
        ["GND", "Ground", "Common GND rail", "MANDATORY"],
    ]:
        ard.append(row)
    e.append(tbl(ard, [2.4*cm, 3.4*cm, 3.4*cm, 4.6*cm]))

    e.append(PageBreak())

    # ---- 5. Subsystems ----
    e.append(Paragraph("5. Subsystem Wiring Detail", h1))
    e.append(Paragraph("5.1 Servos (x3) — powered by EXTERNAL 5V PSU", h2))
    e.append(Preformatted(
        "Servo Red    ---> External 5V (+) rail\n"
        "Servo Brown  ---> External 5V (-) rail (GND)\n"
        "Servo Signal ---> Arduino D10 (S2) / D11 (S3) / D8 (S4)\n"
        "External 5V (-) rail ALSO wires to Arduino GND.\n\n"
        "Servo 2: OPEN=0   CLOSED=89   (sorter flap A)\n"
        "Servo 3: OPEN=90  CLOSED=0    (sorter flap B)\n"
        "Servo 4: OPEN=75  CLOSED=0    (feeder/agitator)\n"
        "RULE: Servo 2 & 3 must NEVER both be closed (collide).", mono))

    e.append(Paragraph("5.2 IR Sensor — Arduino D2", h2))
    e.append(Preformatted(
        "IR VCC  ---> Arduino 5V\n"
        "IR GND  ---> Arduino GND\n"
        "IR OUT  ---> Arduino D2\n"
        "LOW = object detected -> IR:TRIGGERED\n"
        "HIGH = clear          -> IR:CLEAR\n"
        "Adjust sensitivity potentiometer so DETECT LED lights at sort point.", mono))

    e.append(Paragraph("5.3 Dual Relay + Fans — 12V coil, active LOW", h2))
    e.append(Preformatted(
        "LOGIC SIDE:                  LOAD SIDE (12V fans):\n"
        "Relay VCC -> Arduino 5V      12V (+) -> COM1 and COM2\n"
        "Relay GND -> Arduino GND     NO1     -> Fan 1 (+)\n"
        "Relay IN1 -> Arduino D4      NO2     -> Fan 2 (+)\n"
        "Relay IN2 -> Arduino D7      Fan (-) -> 12V (-)\n"
        "Arduino pin LOW = relay ON = fan spins. Fans default ON at boot.", mono))

    e.append(Paragraph("5.4 Conveyor — BTS7960, 12V motor, PWM speed", h2))
    e.append(Preformatted(
        "LOGIC SIDE (Raspberry Pi):     MOTOR SIDE (12V):\n"
        "BTS VCC  -> Pi 5V              BTS B+ -> 12V PSU (+)\n"
        "BTS GND  -> Pi GND             BTS B- -> 12V PSU (-)\n"
        "BTS R_EN -> Pi 5V             BTS M+ -> motor wire 1\n"
        "BTS L_EN -> Pi 5V             BTS M- -> motor wire 2\n"
        "BTS RPWM -> Pi GPIO18 (pin12)  forward PWM\n"
        "BTS LPWM -> Pi GPIO19 (pin35)  reverse PWM\n"
        "R_IS / L_IS -> leave disconnected\n"
        "Speed = software PWM 0-100% @ 1kHz from dashboard slider. DC only.", mono))

    e.append(PageBreak())

    # ---- 6. Block diagram ----
    e.append(Paragraph("6. Full System Block Diagram", h1))
    e.append(Preformatted(
        "                        +------------------+\n"
        "                        |   12V PSU (>=5A)  |\n"
        "                        +--+------------+--+\n"
        "                           |            |\n"
        "                   +-------v----+  +----v-----+\n"
        "                   |  BTS7960   |  | Relay x2 |\n"
        "                   | (conveyor) |  | load side|\n"
        "                   +--+------+--+  +-+------+-+\n"
        "        GPIO18/19    |      | motor  |      |\n"
        "     +---------------+    +-v-+   +-v-+  +-v-+\n"
        "     |   (PWM)            |Belt|   |Fan1| |Fan2|\n"
        "     |                    +---+   +---+  +---+\n"
        " +---v--------+                     ^      ^\n"
        " | Raspberry  |                     |D4    |D7\n"
        " |   Pi 5     |  USB  +-------------+------+-----+\n"
        " | - YOLO     +------>|     Arduino Uno          |\n"
        " | - Dashboard|       | D2 <-- IR sensor         |\n"
        " | - Conv PWM |       | D8 --> Servo 4           |\n"
        " | GPIO4 <-DHT22 ripe | D10--> Servo 2 (flap A)  |\n"
        " | GPIO23<-DHT22 unrip| D11--> Servo 3 (flap B)  |\n"
        " | + 7\" DSI   |       +-----------+--------------+\n"
        " | + USB cam  |                   | signal only\n"
        " +------------+            +-------v------+\n"
        "                           | External 5V  |--> Servo 2,3,4\n"
        "                           +--------------+\n"
        "  ====== COMMON GROUND (all PSU -, Pi GND, Arduino GND) ======", mono))

    # ---- 7. Bins ----
    e.append(Paragraph("7. Bins / Sorting Logic", h1))
    bins = [["Bin", "Class", "DHT22", "Fan", "Sorter combo"]]
    for row in [
        ["Bin 1", "Ripe", "Yes (GPIO 4)", "Yes (Relay 1)", "S2 CLOSED + S3 OPEN"],
        ["Bin 2", "Unripe", "Yes (GPIO 23)", "Yes (Relay 2)", "S2 OPEN + S3 CLOSED"],
        ["Bin 3", "Rotten", "No", "No", "S2 OPEN + S3 OPEN"],
    ]:
        bins.append(row)
    e.append(tbl(bins, [1.6*cm, 2*cm, 3*cm, 3*cm, 4.6*cm]))
    e.append(Paragraph(
        "Flow: Camera classifies (YOLO) -> tomato travels on conveyor -> "
        "IR triggers at sort point -> Servo 2/3 flap routes tomato to the "
        "correct bin -> returns to rest.", body))

    # ---- 8. cheat card ----
    e.append(Paragraph("8. Quick Pin Reference", h1))
    e.append(Preformatted(
        "RASPBERRY PI 5              ARDUINO UNO\n"
        "GPIO4  (pin7)  DHT22 ripe    D2   IR sensor OUT\n"
        "GPIO23 (pin16) DHT22 unripe  D4   Relay 1 (Fan 1)\n"
        "GPIO18 (pin12) BTS RPWM      D7   Relay 2 (Fan 2)\n"
        "GPIO19 (pin35) BTS LPWM      D8   Servo 4\n"
        "3.3V   (pin1)  DHT22 VCC     D10  Servo 2\n"
        "5V     (pin2)  BTS logic     D11  Servo 3\n"
        "USB            Arduino+Cam   (D9  Servo 1 = DISABLED)\n\n"
        "POWER:  Pi=USB-C 5V | Servos=ext 5V PSU | Conveyor+Fans=12V PSU\n"
        "GROUND: all commoned together", mono))

    doc.build(e)
    print(f"Wrote {OUT_PDF}")


if __name__ == "__main__":
    build()
