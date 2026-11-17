#!/usr/bin/env python3
"""Apply Flying Bear Ghost 6 (MKS Robin Nano V3.1) settings to a clean Marlin tree.

usage: python3 -I apply_ghost6.py <path to Marlin/Marlin directory> [full|g1_lite|g2_features|g3_full|safe|galaxy_lite|safe_noeeprom]
Every value that is an ASSUMPTION (not verified on the real printer) is tagged ASSUME.
"""
import re, sys, pathlib

root = pathlib.Path(sys.argv[1])
cfg = root / "Configuration.h"
adv = root / "Configuration_adv.h"
texts = {cfg: cfg.read_text(), adv: adv.read_text()}
log = []


def setdef(f, name, value=None, enable=True, add_comment=None):
    """Enable/disable '#define NAME [value]' keeping indentation. value=None keeps old value."""
    t = texts[f]
    pat = re.compile(r'^([ \t]*)(//)?([ \t]*)#define[ \t]+' + re.escape(name) + r'(?=[ \t]|$)(.*)$', re.M)
    m = pat.search(t)
    if not m:
        raise SystemExit(f"NOT FOUND: {name} in {f.name}")
    indent, _, _, rest = m.groups()
    rest = rest.rstrip()
    # split value and trailing comment
    vm = re.match(r'^[ \t]*(.*?)([ \t]*//.*)?$', rest)
    oldval, comment = vm.group(1), (vm.group(2) or "")
    val = oldval if value is None else str(value)
    if not val and comment:
        comment = "  " + comment.lstrip()
    line = f"{indent}{'' if enable else '//'}#define {name}" + (f" {val}" if val else "") + comment
    texts[f] = t[:m.start()] + line + t[m.end():]
    log.append(f"{f.name}: {line.strip()}")


C, A = cfg, adv

# ---- identity / board ------------------------------------------------------
setdef(C, "STRING_CONFIG_H_AUTHOR", '"(Ghost6 custom)"')
t = texts[C]
t = re.sub(r'#define MOTHERBOARD BOARD_RAMPS_14_EFB', '#define MOTHERBOARD BOARD_MKS_ROBIN_NANO_V3_1', t)
texts[C] = t
setdef(C, "SERIAL_PORT", "-1")                    # USB CDC
setdef(C, "CUSTOM_MACHINE_NAME", '"Ghost 6"')
# Stock M503 has no M906 -> drivers are not UART-configured (standalone). A4988 timing is the safest
# choice for ANY standalone driver (A4988/DRV8825/TMC2208 standalone); step rates here are far below its limit.
for ax in ("X", "Y", "Z", "E0"):
    setdef(C, f"{ax}_DRIVER_TYPE", "A4988")

# ---- temperature -----------------------------------------------------------
setdef(C, "HEATER_0_MAXTEMP", "280")
setdef(C, "BED_MAXTEMP", "120")
setdef(C, "PIDTEMPBED")
setdef(C, "PID_EDIT_MENU")
setdef(C, "PID_AUTOTUNE_MENU")

# ---- kinematics / geometry -------------------------------------------------
setdef(C, "COREXY")
setdef(C, "X_BED_SIZE", "255")
setdef(C, "Y_BED_SIZE", "210")
setdef(C, "Z_MAX_POS", "210")
# VERIFIED: from M503 of the stock Marlin 2.0.9.2 on this printer
setdef(C, "DEFAULT_AXIS_STEPS_PER_UNIT", "{ 160.6, 160.6, 800, 405 }")
setdef(C, "DEFAULT_MAX_FEEDRATE", "{ 200, 200, 4, 45 }")
# Accelerations: stock is conservative (print 500, travel 1500, max 1500). Raised moderately; tune up later.
setdef(C, "DEFAULT_MAX_ACCELERATION", "{ 2000, 2000, 100, 3000 }")
setdef(C, "DEFAULT_ACCELERATION", "1000")
setdef(C, "DEFAULT_TRAVEL_ACCELERATION", "1500")
# VERIFIED: stock PID (M301 / M304)
setdef(C, "DEFAULT_KP", "11.58")
setdef(C, "DEFAULT_KI", "0.61")
setdef(C, "DEFAULT_KD", "55.36")
setdef(C, "DEFAULT_BED_KP", "103.73")
setdef(C, "DEFAULT_BED_KI", "17.06")
setdef(C, "DEFAULT_BED_KD", "420.46")
setdef(C, "S_CURVE_ACCELERATION")

# ---- features --------------------------------------------------------------
setdef(C, "EEPROM_SETTINGS")
setdef(C, "PRINTCOUNTER")
setdef(C, "SDSUPPORT")
setdef(C, "LCD_BED_TRAMMING")                     # no probe on stock Ghost 6 -> manual 4-corner assist
setdef(C, "BED_TRAMMING_INSET_LFRB", "{ 28, 31, 27, 29 }")  # ASSUME: screws at (28,31)-(228,181) from owner's Klipper cfg
# ASSUME: endstops trigger LOW (owner's Klipper cfg: !PA15 / !PD2 / !PC8 with pullups). VERIFY with M119.
for ax in ("X", "Y", "Z"):
    setdef(C, f"{ax}_MIN_ENDSTOP_HIT_STATE", "LOW")
setdef(C, "NOZZLE_PARK_FEATURE")
setdef(C, "LCD_LANGUAGE", "ru")

# ---- display: MKS TS35 (480x320, SPI on EXP1/EXP2) + Galaxy UI -------------
setdef(C, "MKS_TS35_V2_0")                        # preset: ST7796, 480x320, SPI
setdef(C, "TFT_COLOR_UI")
setdef(C, "NOVIN3DP_GALAXY_UI")
setdef(C, "TOUCH_SCREEN")
setdef(C, "TFT_ROTATION", "TFT_ROTATE_180")       # screen is mounted vertically: flip UI 180 deg (reads top-to-bottom)

# ---- advanced --------------------------------------------------------------
setdef(A, "LIN_ADVANCE")
setdef(A, "ADVANCE_K", "0.0")                     # keep off until tuned (M900)
setdef(A, "BABYSTEPPING")
setdef(A, "ADAPTIVE_STEP_SMOOTHING")
setdef(A, "POWER_LOSS_RECOVERY")
setdef(A, "EMERGENCY_PARSER")
setdef(A, "ADVANCED_PAUSE_FEATURE")
setdef(A, "PARK_HEAD_ON_PAUSE")
setdef(A, "SHOW_REMAINING_TIME")
setdef(A, "LONG_FILENAME_HOST_SUPPORT")
setdef(A, "BINARY_FILE_TRANSFER")
setdef(A, "USB_FLASH_DRIVE_SUPPORT")
setdef(A, "USE_OTG_USB_HOST")                     # native USB host (Robin Nano V3 OTG)
setdef(A, "INPUT_SHAPING_X")
setdef(A, "INPUT_SHAPING_Y")
setdef(A, "SHAPING_MENU")

# ---- profiles ---------------------------------------------------------------
profile = sys.argv[2] if len(sys.argv) > 2 else "full"
EXTRAS = ("INPUT_SHAPING_X", "INPUT_SHAPING_Y", "SHAPING_MENU", "LIN_ADVANCE", "ADAPTIVE_STEP_SMOOTHING",
          "POWER_LOSS_RECOVERY", "EMERGENCY_PARSER")
USB = ("BINARY_FILE_TRANSFER", "USE_OTG_USB_HOST", "USB_FLASH_DRIVE_SUPPORT")
if profile in ("safe", "galaxy_lite", "safe_noeeprom", "g1_lite"):
    for n in EXTRAS + USB:
        setdef(A, n, enable=False)
if profile == "g2_features":
    for n in USB:
        setdef(A, n, enable=False)
if profile in ("safe", "safe_noeeprom"):
    setdef(C, "NOVIN3DP_GALAXY_UI", enable=False)          # standard Marlin Color UI
if profile == "safe_noeeprom":
    setdef(C, "PRINTCOUNTER", enable=False)
    setdef(C, "EEPROM_SETTINGS", enable=False)

# Nano4: the I2C EEPROM Marlin expects on this board hangs the boot (verified: build without EEPROM boots,
# build with I2C EEPROM reboots). Keep settings in a file on the SD card instead.
if profile not in ("safe_noeeprom",):
    t = texts[C]
    t = t.replace("#define EEPROM_SETTINGS", "#define EEPROM_SETTINGS\n#define SDCARD_EEPROM_EMULATION  // settings stored on the SD card (I2C EEPROM hangs on Nano4)", 1)
    texts[C] = t
    log.append("Configuration.h: #define SDCARD_EEPROM_EMULATION")

for f, t in texts.items():
    f.write_text(t)
print("\n".join(log))
