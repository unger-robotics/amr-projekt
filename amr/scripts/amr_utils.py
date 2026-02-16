#!/usr/bin/env python3
"""
Zentrale Konstanten und Hilfsfunktionen fuer AMR-Validierungsskripte.

Spiegel der Hardware-Parameter aus hardware/config.h (Single Source of Truth).
Aenderungen an Roboter-Parametern muessen hier UND in config.h erfolgen.
"""

import math
import json
import os

# ===========================================================================
# Hardware-Parameter (Spiegel von hardware/config.h)
# ===========================================================================

# Kinematik
WHEEL_DIAMETER = 0.06567            # [m] kalibriert (Bodentest)
WHEEL_RADIUS = WHEEL_DIAMETER / 2.0  # [m]
WHEEL_BASE = 0.178                  # [m] Spurbreite
WHEEL_CIRCUMFERENCE = WHEEL_DIAMETER * math.pi  # [m]

# Encoder (2x Quadratur-Zaehlung)
TICKS_PER_REV_LEFT = 748.6
TICKS_PER_REV_RIGHT = 747.2
TICKS_PER_REV = (TICKS_PER_REV_LEFT + TICKS_PER_REV_RIGHT) / 2.0  # 747.9
METERS_PER_TICK = WHEEL_CIRCUMFERENCE / TICKS_PER_REV

# Encoder-Akzeptanzgrenzen (10-Umdrehungen-Test)
TICKS_PER_REV_MIN = 740.0
TICKS_PER_REV_MAX = 760.0

# PWM / Motor
PWM_DEADZONE = 35

# Safety & Timing
FAILSAFE_TIMEOUT_MS = 500
MAX_VELOCITY = 0.4                  # [m/s] Zielgeschwindigkeit

# PID-Regler (main.cpp hardcoded)
PID_KP = 0.4
PID_KI = 0.1
PID_KD = 0.0

# IMU-Parameter
IMU_PUBLISH_HZ = 20
IMU_GYRO_DRIFT_MAX = 1.0        # [deg/min] Akzeptanzgrenze
IMU_ACCEL_BIAS_MAX = 0.6        # [m/s²] Akzeptanzgrenze az-Bias
IMU_COMPLEMENTARY_ALPHA = 0.02  # Complementary-Filter-Gewicht

# ===========================================================================
# ANSI-Farben fuer Terminal-Ausgabe
# ===========================================================================

COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_RED = "\033[31m"
COLOR_CYAN = "\033[36m"
COLOR_BOLD = "\033[1m"
COLOR_RESET = "\033[0m"


# ===========================================================================
# Geometrie-Funktionen
# ===========================================================================

def quaternion_to_yaw(q):
    """Quaternion -> Yaw-Winkel (rad).

    Akzeptiert ROS-Quaternion-Msg (mit .x/.y/.z/.w Attributen)
    oder Liste/Tupel [x, y, z, w].
    """
    if hasattr(q, 'w'):
        x, y, z, w = q.x, q.y, q.z, q.w
    else:
        x, y, z, w = q[0], q[1], q[2], q[3]
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(siny_cosp, cosy_cosp)


def yaw_to_quaternion(yaw):
    """Yaw-Winkel (rad) -> Quaternion als Tupel (x, y, z, w)."""
    qz = math.sin(yaw / 2.0)
    qw = math.cos(yaw / 2.0)
    return (0.0, 0.0, qz, qw)


def normalize_angle(angle):
    """Normalisiert Winkel auf [-pi, pi]."""
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


# Deutsche Aliase
quaternion_zu_yaw = quaternion_to_yaw
normalisiere_winkel = normalize_angle


# ===========================================================================
# JSON-Hilfsfunktionen
# ===========================================================================

def save_json(data, dateiname, verzeichnis=None):
    """Speichert ein Dictionary als JSON-Datei.

    Parameter:
        data:         Dictionary mit Ergebnissen
        dateiname:    Dateiname (z.B. 'encoder_results.json')
        verzeichnis:  Zielverzeichnis (Standard: Skript-Verzeichnis)
    """
    if verzeichnis is None:
        verzeichnis = os.path.dirname(os.path.abspath(__file__))
    pfad = os.path.join(verzeichnis, dateiname)
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=numpy_safe_json)
    return pfad


def numpy_safe_json(obj):
    """JSON-Serialisierer fuer numpy-Typen."""
    try:
        import numpy as np
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
    except ImportError:
        pass
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
