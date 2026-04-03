#!/usr/bin/env python3
"""
Ultraschall- und Cliff-Sensor-Validierungstool fuer den AMR-Roboter.
ROS2-Node: subscribt /range/front und /cliff, fuehrt 8 Tests durch:

  1. US-Konnektivitaet: Prueft ob Ultraschalldaten ankommen, misst Rate
  2. US statische Messung: Genauigkeit bei bekannter Distanz (interaktiv)
  3. US Bereichstest: Prueft min_range, max_range und field_of_view
  4. US Wiederholgenauigkeit: Standardabweichung ueber 100 Messungen
  5. Cliff-Konnektivitaet: Prueft ob Cliff-Daten ankommen, misst Rate
  6. Cliff-Boden: Fehlalarm-Test auf festem Boden (3s)
  7. Cliff-Erkennung: Manueller Test — Sensor verdecken (interaktiv)
  8. Temperaturkorrektur: Informativ, optionale Schallgeschwindigkeits-Korrektur

Ergebnis: Terminal-Ausgabe mit PASS/FAIL + JSON-Protokoll (sensor_results.json).
"""

import datetime
import math
import sys
import time

try:
    from amr_utils import (
        CLIFF_PUBLISH_HZ,
        COLOR_BOLD,
        COLOR_CYAN,
        COLOR_GREEN,
        COLOR_RED,
        COLOR_RESET,
        US_ACCURACY_MAX_PCT,
        US_FIELD_OF_VIEW,
        US_MAX_RANGE_M,
        US_MIN_RANGE_M,
        US_PUBLISH_HZ,
        save_json,
    )
except ImportError:
    from my_bot.amr_utils import (
        CLIFF_PUBLISH_HZ,
        COLOR_BOLD,
        COLOR_CYAN,
        COLOR_GREEN,
        COLOR_RED,
        COLOR_RESET,
        US_ACCURACY_MAX_PCT,
        US_FIELD_OF_VIEW,
        US_MAX_RANGE_M,
        US_MIN_RANGE_M,
        US_PUBLISH_HZ,
        save_json,
    )

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Range
from std_msgs.msg import Bool

# ===========================================================================
# Lokale Konstanten
# ===========================================================================

US_RATE_MIN_HZ = 7.0  # Akzeptanzgrenze (Soll: 10 Hz)
US_STATIC_SAMPLES = 100  # Samples fuer statische Messung
US_REPEATABILITY_STD_MAX_M = 0.015  # 15 mm max. Standardabweichung

CLIFF_RATE_MIN_HZ = 15.0  # Akzeptanzgrenze (Soll: 20 Hz)
CLIFF_GROUND_SAMPLES = 60  # 3s bei 20 Hz
CLIFF_DETECT_TIMEOUT_S = 10.0  # Max. Wartezeit auf manuelles Cliff-Signal

SPEED_OF_SOUND_FIRMWARE = 343.2  # [m/s] in config_sensors.h (20 C)


# ===========================================================================
# ROS2-Node
# ===========================================================================


class SensorTestNode(Node):
    """ROS2-Node fuer Ultraschall- und Cliff-Validierung."""

    def __init__(self):
        super().__init__("sensor_test_node")

        # QoS: Best-Effort fuer /cliff (Match mit Sensor-Node Publisher)
        qos_sensor = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)

        # Subscriber
        self.range_sub = self.create_subscription(Range, "/range/front", self._range_callback, 10)
        self.cliff_sub = self.create_subscription(Bool, "/cliff", self._cliff_callback, qos_sensor)

        # Ultraschall-Daten
        self.range_received = False
        self.range_timestamps: list[float] = []
        self.range_values: list[float] = []
        self.last_range_msg: Range | None = None

        # Cliff-Daten
        self.cliff_received = False
        self.cliff_timestamps: list[float] = []
        self.cliff_values: list[bool] = []

        # Steuerflags
        self.collecting_range = False
        self.collecting_cliff = False

        self.get_logger().info("Sensor-Test-Node gestartet.")

    def _range_callback(self, msg: Range):
        self.range_received = True
        self.last_range_msg = msg
        if self.collecting_range:
            self.range_timestamps.append(time.time())
            self.range_values.append(msg.range)

    def _cliff_callback(self, msg: Bool):
        self.cliff_received = True
        if self.collecting_cliff:
            self.cliff_timestamps.append(time.time())
            self.cliff_values.append(msg.data)

    def wait_for_topic(self, attr: str, timeout_s: float = 5.0) -> bool:
        """Wartet bis erste Nachricht auf einem Topic empfangen wird."""
        start = time.time()
        while not getattr(self, attr):
            rclpy.spin_once(self, timeout_sec=0.1)
            if time.time() - start > timeout_s:
                return False
        return True

    def reset_range(self):
        self.range_timestamps = []
        self.range_values = []

    def reset_cliff(self):
        self.cliff_timestamps = []
        self.cliff_values = []


# ===========================================================================
# Test 1: US-Konnektivitaet
# ===========================================================================


def test_us_connectivity(node: SensorTestNode) -> dict:
    """Prueft ob Ultraschalldaten ankommen und misst die Sample-Rate."""
    print(f"\n{COLOR_BOLD}--- Test 1: US-Konnektivitaet ---{COLOR_RESET}")
    print("  Warte auf /range/front Daten (max. 5s)...")

    if not node.wait_for_topic("range_received"):
        print(f"  Ergebnis: {COLOR_RED}FAIL{COLOR_RESET} (keine Daten innerhalb 5s)")
        return {"pass": False, "rate_hz": 0.0, "reason": "timeout"}

    print("  /range/front empfangen. Messe Sample-Rate (3s)...")

    node.reset_range()
    node.collecting_range = True

    start = time.time()
    while time.time() - start < 3.0:
        rclpy.spin_once(node, timeout_sec=0.05)

    node.collecting_range = False

    n_samples = len(node.range_timestamps)
    if n_samples < 2:
        rate_hz = 0.0
    else:
        duration = node.range_timestamps[-1] - node.range_timestamps[0]
        rate_hz = (n_samples - 1) / duration if duration > 0 else 0.0

    passed = rate_hz >= US_RATE_MIN_HZ
    status = f"{COLOR_GREEN}PASS{COLOR_RESET}" if passed else f"{COLOR_RED}FAIL{COLOR_RESET}"
    print(f"  Samples: {n_samples}, Rate: {rate_hz:.1f} Hz (Soll: >= {US_RATE_MIN_HZ} Hz)")
    print(f"  Ergebnis: {status}")

    return {"pass": passed, "rate_hz": round(rate_hz, 1), "samples": n_samples}


# ===========================================================================
# Test 2: US statische Messung
# ===========================================================================


def test_us_static(node: SensorTestNode) -> dict:
    """Misst Ultraschall-Genauigkeit bei bekannter Distanz."""
    print(f"\n{COLOR_BOLD}--- Test 2: US statische Messung ---{COLOR_RESET}")
    print("  Objekt in bekannter Distanz vor dem Sensor aufstellen.")

    try:
        soll_str = input(f"  {COLOR_CYAN}Soll-Distanz eingeben [m]: {COLOR_RESET}")
        soll_m = float(soll_str)
    except (ValueError, EOFError):
        print(f"  {COLOR_RED}Ungueltige Eingabe. Test uebersprungen.{COLOR_RESET}")
        return {"pass": False, "reason": "invalid_input"}

    if soll_m < US_MIN_RANGE_M or soll_m > US_MAX_RANGE_M:
        print(
            f"  {COLOR_RED}Distanz ausserhalb des gueltigen Bereichs "
            f"({US_MIN_RANGE_M}-{US_MAX_RANGE_M} m){COLOR_RESET}"
        )
        return {"pass": False, "reason": "out_of_range", "soll_m": soll_m}

    print(f"  Sammle {US_STATIC_SAMPLES} Messungen...")

    node.reset_range()
    node.collecting_range = True

    start = time.time()
    timeout = US_STATIC_SAMPLES / US_PUBLISH_HZ * 2.0  # 2x Sicherheitsfaktor
    while len(node.range_values) < US_STATIC_SAMPLES:
        rclpy.spin_once(node, timeout_sec=0.05)
        if time.time() - start > timeout:
            break

    node.collecting_range = False

    # Timeout-Werte filtern (> max_range = Sensor-Timeout)
    valid = [v for v in node.range_values if v <= US_MAX_RANGE_M]
    n_valid = len(valid)

    if n_valid < 10:
        print(f"  Ergebnis: {COLOR_RED}FAIL{COLOR_RESET} (zu wenige gueltige Samples: {n_valid})")
        return {
            "pass": False,
            "reason": "insufficient_valid_samples",
            "samples": len(node.range_values),
            "valid_samples": n_valid,
        }

    mean_m = sum(valid) / n_valid
    std_m = math.sqrt(sum((v - mean_m) ** 2 for v in valid) / n_valid)
    fehler_m = abs(mean_m - soll_m)
    fehler_pct = (fehler_m / soll_m) * 100.0 if soll_m > 0 else 0.0

    passed = fehler_pct < US_ACCURACY_MAX_PCT
    status = f"{COLOR_GREEN}PASS{COLOR_RESET}" if passed else f"{COLOR_RED}FAIL{COLOR_RESET}"

    print(f"  Gueltige Samples: {n_valid}/{len(node.range_values)}")
    print(f"  Soll: {soll_m:.3f} m, Ist: {mean_m:.3f} m (Std: {std_m:.4f} m)")
    print(f"  Abweichung: {fehler_m:.4f} m ({fehler_pct:.1f}%) (Grenze: < {US_ACCURACY_MAX_PCT}%)")
    print(f"  Ergebnis: {status}")

    return {
        "pass": passed,
        "soll_m": soll_m,
        "ist_m": round(mean_m, 4),
        "std_m": round(std_m, 4),
        "fehler_pct": round(fehler_pct, 1),
        "samples": n_valid,
    }


# ===========================================================================
# Test 3: US Bereichstest
# ===========================================================================


def test_us_range_check(node: SensorTestNode) -> dict:
    """Prueft ob min_range, max_range und field_of_view korrekt sind."""
    print(f"\n{COLOR_BOLD}--- Test 3: US Bereichstest ---{COLOR_RESET}")

    msg = node.last_range_msg
    if msg is None:
        print(f"  Ergebnis: {COLOR_RED}FAIL{COLOR_RESET} (keine Range-Nachricht vorhanden)")
        return {"pass": False, "reason": "no_data"}

    checks = {
        "min_range": (msg.min_range, US_MIN_RANGE_M),
        "max_range": (msg.max_range, US_MAX_RANGE_M),
        "fov_rad": (msg.field_of_view, US_FIELD_OF_VIEW),
    }

    all_ok = True
    for name, (ist, soll) in checks.items():
        ok = abs(ist - soll) < 0.01
        mark = f"{COLOR_GREEN}OK{COLOR_RESET}" if ok else f"{COLOR_RED}FALSCH{COLOR_RESET}"
        print(f"  {name}: {ist:.3f} (Soll: {soll:.3f}) [{mark}]")
        if not ok:
            all_ok = False

    print(f"  Aktuelle Distanz: {msg.range:.3f} m")

    status = f"{COLOR_GREEN}PASS{COLOR_RESET}" if all_ok else f"{COLOR_RED}FAIL{COLOR_RESET}"
    print(f"  Ergebnis: {status}")

    return {
        "pass": all_ok,
        "min_range": round(msg.min_range, 3),
        "max_range": round(msg.max_range, 3),
        "fov_rad": round(msg.field_of_view, 3),
        "current_range": round(msg.range, 3),
    }


# ===========================================================================
# Test 4: US Wiederholgenauigkeit
# ===========================================================================


def test_us_repeatability(node: SensorTestNode, static_data: dict) -> dict:
    """Bewertet Standardabweichung der Ultraschallmessungen."""
    print(f"\n{COLOR_BOLD}--- Test 4: US Wiederholgenauigkeit ---{COLOR_RESET}")

    # Daten aus Test 2 wiederverwenden wenn vorhanden
    if static_data.get("std_m") is not None and static_data.get("samples", 0) >= 50:
        std_m = static_data["std_m"]
        n = static_data["samples"]
        print(f"  Verwende Daten aus Test 2 ({n} Samples).")
    else:
        print(f"  Sammle {US_STATIC_SAMPLES} Messungen bei fester Distanz...")

        node.reset_range()
        node.collecting_range = True

        start = time.time()
        timeout = US_STATIC_SAMPLES / US_PUBLISH_HZ * 2.0
        while len(node.range_values) < US_STATIC_SAMPLES:
            rclpy.spin_once(node, timeout_sec=0.05)
            if time.time() - start > timeout:
                break

        node.collecting_range = False

        valid = [v for v in node.range_values if v <= US_MAX_RANGE_M]
        n = len(valid)

        if n < 10:
            print(f"  Ergebnis: {COLOR_RED}FAIL{COLOR_RESET} (zu wenige gueltige Samples: {n})")
            return {"pass": False, "reason": "insufficient_samples", "samples": n}

        mean_m = sum(valid) / n
        std_m = math.sqrt(sum((v - mean_m) ** 2 for v in valid) / n)

    passed = std_m < US_REPEATABILITY_STD_MAX_M
    status = f"{COLOR_GREEN}PASS{COLOR_RESET}" if passed else f"{COLOR_RED}FAIL{COLOR_RESET}"

    print(f"  Std: {std_m * 1000:.1f} mm (Grenze: < {US_REPEATABILITY_STD_MAX_M * 1000:.0f} mm)")
    print(f"  Ergebnis: {status}")

    return {"pass": passed, "std_m": round(std_m, 4), "samples": n}


# ===========================================================================
# Test 5: Cliff-Konnektivitaet
# ===========================================================================


def test_cliff_connectivity(node: SensorTestNode) -> dict:
    """Prueft ob Cliff-Daten ankommen und misst die Sample-Rate."""
    print(f"\n{COLOR_BOLD}--- Test 5: Cliff-Konnektivitaet ---{COLOR_RESET}")
    print("  Warte auf /cliff Daten (max. 5s)...")

    if not node.wait_for_topic("cliff_received"):
        print(f"  Ergebnis: {COLOR_RED}FAIL{COLOR_RESET} (keine Daten innerhalb 5s)")
        return {"pass": False, "rate_hz": 0.0, "reason": "timeout"}

    print("  /cliff empfangen. Messe Sample-Rate (3s)...")

    node.reset_cliff()
    node.collecting_cliff = True

    start = time.time()
    while time.time() - start < 3.0:
        rclpy.spin_once(node, timeout_sec=0.05)

    node.collecting_cliff = False

    n_samples = len(node.cliff_timestamps)
    if n_samples < 2:
        rate_hz = 0.0
    else:
        duration = node.cliff_timestamps[-1] - node.cliff_timestamps[0]
        rate_hz = (n_samples - 1) / duration if duration > 0 else 0.0

    passed = rate_hz >= CLIFF_RATE_MIN_HZ
    status = f"{COLOR_GREEN}PASS{COLOR_RESET}" if passed else f"{COLOR_RED}FAIL{COLOR_RESET}"
    print(f"  Samples: {n_samples}, Rate: {rate_hz:.1f} Hz (Soll: >= {CLIFF_RATE_MIN_HZ} Hz)")
    print(f"  Ergebnis: {status}")

    return {"pass": passed, "rate_hz": round(rate_hz, 1), "samples": n_samples}


# ===========================================================================
# Test 6: Cliff-Boden
# ===========================================================================


def test_cliff_ground(node: SensorTestNode) -> dict:
    """Prueft auf Fehlalarme bei festem Boden (3s Sammlung)."""
    print(f"\n{COLOR_BOLD}--- Test 6: Cliff-Boden (Fehlalarm-Test) ---{COLOR_RESET}")
    print("  Roboter muss auf festem Boden stehen.")
    print(f"  Sammle {CLIFF_GROUND_SAMPLES} Cliff-Samples...\n")

    node.reset_cliff()
    node.collecting_cliff = True

    start = time.time()
    timeout = CLIFF_GROUND_SAMPLES / CLIFF_PUBLISH_HZ * 2.0
    while len(node.cliff_values) < CLIFF_GROUND_SAMPLES:
        rclpy.spin_once(node, timeout_sec=0.05)
        if time.time() - start > timeout:
            break

    node.collecting_cliff = False

    n = len(node.cliff_values)
    if n < 10:
        print(f"  Ergebnis: {COLOR_RED}FAIL{COLOR_RESET} (zu wenige Samples: {n})")
        return {"pass": False, "reason": "insufficient_samples", "samples": n}

    false_alarms = sum(1 for v in node.cliff_values if v)
    ground_pct = ((n - false_alarms) / n) * 100.0

    passed = false_alarms == 0
    status = f"{COLOR_GREEN}PASS{COLOR_RESET}" if passed else f"{COLOR_RED}FAIL{COLOR_RESET}"

    print(f"  Samples: {n}")
    print(f"  Boden erkannt: {ground_pct:.1f}%, Fehlalarme: {false_alarms}")
    print(f"  Ergebnis: {status}")

    return {
        "pass": passed,
        "ground_pct": round(ground_pct, 1),
        "cliff_false_alarms": false_alarms,
        "samples": n,
    }


# ===========================================================================
# Test 7: Cliff-Erkennung (interaktiv)
# ===========================================================================


def test_cliff_detection(node: SensorTestNode) -> dict:
    """Interaktiver Test: Sensor verdecken, Cliff-Erkennung pruefen."""
    print(f"\n{COLOR_BOLD}--- Test 7: Cliff-Erkennung (interaktiv) ---{COLOR_RESET}")
    print("  Sensor ueber eine Kante halten oder IR-Sensor verdecken.")
    print("  Potentiometer auf MH-B ggf. justieren (Schwellenwert).")

    try:
        input(f"  {COLOR_CYAN}[Enter] zum Starten...{COLOR_RESET}")
    except EOFError:
        return {"pass": False, "reason": "no_tty"}

    node.reset_cliff()
    node.collecting_cliff = True

    start = time.time()
    first_cliff_time = None

    print(f"  Warte auf Cliff-Signal (max. {CLIFF_DETECT_TIMEOUT_S:.0f}s)...")

    while time.time() - start < CLIFF_DETECT_TIMEOUT_S:
        rclpy.spin_once(node, timeout_sec=0.05)
        if first_cliff_time is None and any(v for v in node.cliff_values):
            first_cliff_time = time.time()
            # Noch 1s weiter sammeln um Anzahl zu zaehlen
        if first_cliff_time is not None and time.time() - first_cliff_time > 1.0:
            break

    node.collecting_cliff = False

    cliff_count = sum(1 for v in node.cliff_values if v)

    if first_cliff_time is None:
        print(f"  Ergebnis: {COLOR_RED}FAIL{COLOR_RESET} (kein Cliff-Signal erkannt)")
        return {
            "pass": False,
            "reaction_time_ms": 0.0,
            "cliff_detected_count": 0,
            "reason": "no_detection",
        }

    reaction_ms = (first_cliff_time - start) * 1000.0

    print(f"  Cliff erkannt nach: {reaction_ms:.0f} ms")
    print(f"  Cliff-Signale: {cliff_count}/{len(node.cliff_values)}")
    print(f"  Ergebnis: {COLOR_GREEN}PASS{COLOR_RESET}")

    return {
        "pass": True,
        "reaction_time_ms": round(reaction_ms, 1),
        "cliff_detected_count": cliff_count,
        "samples": len(node.cliff_values),
    }


# ===========================================================================
# Test 8: Temperaturkorrektur (informativ)
# ===========================================================================


def test_temperature_correction() -> dict | None:
    """Berechnet Schallgeschwindigkeits-Korrektur fuer aktuelle Temperatur."""
    print(f"\n{COLOR_BOLD}--- Test 8: Temperaturkorrektur (optional) ---{COLOR_RESET}")

    try:
        temp_str = input(
            f"  {COLOR_CYAN}Raumtemperatur eingeben [C] (leer = ueberspringen): {COLOR_RESET}"
        )
    except EOFError:
        return None

    if not temp_str.strip():
        print("  Uebersprungen.")
        return None

    try:
        temp_c = float(temp_str)
    except ValueError:
        print(f"  {COLOR_RED}Ungueltige Eingabe.{COLOR_RESET}")
        return None

    v_corrected = 331.3 + 0.607 * temp_c
    delta_pct = abs(v_corrected - SPEED_OF_SOUND_FIRMWARE) / SPEED_OF_SOUND_FIRMWARE * 100.0

    print(f"  Firmware-Wert:    {SPEED_OF_SOUND_FIRMWARE:.1f} m/s (fuer ~19.6 C)")
    print(f"  Korrigierter Wert: {v_corrected:.1f} m/s (fuer {temp_c:.1f} C)")
    print(f"  Abweichung:       {delta_pct:.2f}%")

    if delta_pct > 1.0:
        print(
            f"  {COLOR_CYAN}Empfehlung: Schallgeschwindigkeit in config_sensors.h "
            f"auf {v_corrected:.1f} m/s anpassen.{COLOR_RESET}"
        )
    else:
        print(f"  {COLOR_GREEN}Abweichung vernachlaessigbar.{COLOR_RESET}")

    return {
        "temp_c": round(temp_c, 1),
        "v_corrected": round(v_corrected, 1),
        "v_firmware": SPEED_OF_SOUND_FIRMWARE,
        "delta_pct": round(delta_pct, 2),
    }


# ===========================================================================
# Hauptprogramm
# ===========================================================================


def main(args=None):
    rclpy.init(args=args)

    print()
    print("*" * 60)
    print("  AMR Sensor-Validierungstool (Ultraschall + Cliff)")
    print("  ROS2-Node: sensor_test_node")
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"  Zeitpunkt: {ts}")
    print("*" * 60)

    node = SensorTestNode()

    # --- Ultraschall-Tests ---

    result_us_conn = test_us_connectivity(node)

    if not result_us_conn["pass"]:
        print(f"\n{COLOR_RED}US nicht erreichbar. Tests 2-4 uebersprungen.{COLOR_RESET}")
        result_us_static = {"pass": False, "reason": "skipped"}
        result_us_range = {"pass": False, "reason": "skipped"}
        result_us_repeat = {"pass": False, "reason": "skipped"}
    else:
        result_us_static = test_us_static(node)
        result_us_range = test_us_range_check(node)
        result_us_repeat = test_us_repeatability(node, result_us_static)

    # --- Cliff-Tests ---

    result_cliff_conn = test_cliff_connectivity(node)

    if not result_cliff_conn["pass"]:
        print(f"\n{COLOR_RED}Cliff nicht erreichbar. Tests 6-7 uebersprungen.{COLOR_RESET}")
        result_cliff_ground = {"pass": False, "reason": "skipped"}
        result_cliff_detect = {"pass": False, "reason": "skipped"}
    else:
        result_cliff_ground = test_cliff_ground(node)
        result_cliff_detect = test_cliff_detection(node)

    # --- Temperaturkorrektur (optional, kein PASS/FAIL) ---

    result_temp = test_temperature_correction()

    # --- Gesamtergebnis (Tests 1-7) ---

    test_results = [
        result_us_conn,
        result_us_static,
        result_us_range,
        result_us_repeat,
        result_cliff_conn,
        result_cliff_ground,
        result_cliff_detect,
    ]
    all_passed = all(r.get("pass", False) for r in test_results)
    n_pass = sum(1 for r in test_results if r.get("pass", False))

    print("\n" + "=" * 60)
    if all_passed:
        print(f"  {COLOR_GREEN}{COLOR_BOLD}GESAMTERGEBNIS: BESTANDEN (7/7 Tests){COLOR_RESET}")
    else:
        print(
            f"  {COLOR_RED}{COLOR_BOLD}GESAMTERGEBNIS: NICHT BESTANDEN "
            f"({n_pass}/7 Tests){COLOR_RESET}"
        )
    print("=" * 60)

    # JSON speichern
    results = {
        "timestamp": datetime.datetime.now().isoformat(),
        "us_connectivity": result_us_conn,
        "us_static": result_us_static,
        "us_range_check": result_us_range,
        "us_repeatability": result_us_repeat,
        "cliff_connectivity": result_cliff_conn,
        "cliff_ground": result_cliff_ground,
        "cliff_detection": result_cliff_detect,
        "overall_pass": all_passed,
    }

    if result_temp is not None:
        results["temperature_correction"] = result_temp

    pfad = save_json(results, "sensor_results.json")
    print(f"\n  Ergebnisse gespeichert: {pfad}")

    node.destroy_node()
    rclpy.shutdown()
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
