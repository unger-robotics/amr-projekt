#!/usr/bin/env python3
"""Hailo-8 Inference Runner (Host-seitig, kein ROS2).

Laeuft nativ auf dem Raspberry Pi 5 (Python 3.13 + hailort) und sendet
Detektionsergebnisse via UDP an den Docker-Container (hailo_udp_receiver_node).

Architektur:
  MJPEG-Stream (:8082) → Hailo-8 YOLOv8 @ 5 Hz → UDP :5005 → ROS2 Container

Voraussetzungen:
  - dashboard_bridge muss laufen (MJPEG auf Port 8082)
  - hailort Python-Paket installiert (oder --fallback Modus)
  - HEF-Modell vorhanden (oder --fallback Modus)

Verwendung:
  python3 host_hailo_runner.py --model hardware/models/yolov8s.hef
  python3 host_hailo_runner.py --fallback   # Dummy-Detektionen ohne Hailo
"""

import argparse
import json
import socket
import sys
import time

import cv2
import numpy as np

# COCO-Klassen (YOLOv8 Default, 80 Klassen) — Englisch fuer Modell-Kompatibilitaet
COCO_LABELS = [
    "person",
    "bicycle",
    "car",
    "motorcycle",
    "airplane",
    "bus",
    "train",
    "truck",
    "boat",
    "traffic light",
    "fire hydrant",
    "stop sign",
    "parking meter",
    "bench",
    "bird",
    "cat",
    "dog",
    "horse",
    "sheep",
    "cow",
    "elephant",
    "bear",
    "zebra",
    "giraffe",
    "backpack",
    "umbrella",
    "handbag",
    "tie",
    "suitcase",
    "frisbee",
    "skis",
    "snowboard",
    "sports ball",
    "kite",
    "baseball bat",
    "baseball glove",
    "skateboard",
    "surfboard",
    "tennis racket",
    "bottle",
    "wine glass",
    "cup",
    "fork",
    "knife",
    "spoon",
    "bowl",
    "banana",
    "apple",
    "sandwich",
    "orange",
    "broccoli",
    "carrot",
    "hot dog",
    "pizza",
    "donut",
    "cake",
    "chair",
    "couch",
    "potted plant",
    "bed",
    "dining table",
    "toilet",
    "tv",
    "laptop",
    "mouse",
    "remote",
    "keyboard",
    "cell phone",
    "microwave",
    "oven",
    "toaster",
    "sink",
    "refrigerator",
    "book",
    "clock",
    "vase",
    "scissors",
    "teddy bear",
    "hair drier",
    "toothbrush",
]

# Deutsche Uebersetzung der COCO-Klassen (fuer Dashboard-Anzeige)
COCO_LABELS_DE = [
    "Person",
    "Fahrrad",
    "Auto",
    "Motorrad",
    "Flugzeug",
    "Bus",
    "Zug",
    "LKW",
    "Boot",
    "Ampel",
    "Hydrant",
    "Stoppschild",
    "Parkuhr",
    "Bank",
    "Vogel",
    "Katze",
    "Hund",
    "Pferd",
    "Schaf",
    "Kuh",
    "Elefant",
    "Baer",
    "Zebra",
    "Giraffe",
    "Rucksack",
    "Regenschirm",
    "Handtasche",
    "Krawatte",
    "Koffer",
    "Frisbee",
    "Skier",
    "Snowboard",
    "Ball",
    "Drachen",
    "Baseballschlaeger",
    "Baseballhandschuh",
    "Skateboard",
    "Surfbrett",
    "Tennisschlaeger",
    "Flasche",
    "Weinglas",
    "Tasse",
    "Gabel",
    "Messer",
    "Loeffel",
    "Schuessel",
    "Banane",
    "Apfel",
    "Sandwich",
    "Orange",
    "Brokkoli",
    "Karotte",
    "Hotdog",
    "Pizza",
    "Donut",
    "Kuchen",
    "Stuhl",
    "Sofa",
    "Topfpflanze",
    "Bett",
    "Esstisch",
    "Toilette",
    "Fernseher",
    "Laptop",
    "Maus",
    "Fernbedienung",
    "Tastatur",
    "Handy",
    "Mikrowelle",
    "Ofen",
    "Toaster",
    "Spuele",
    "Kuehlschrank",
    "Buch",
    "Uhr",
    "Vase",
    "Schere",
    "Teddybaer",
    "Foehn",
    "Zahnbuerste",
]

INPUT_WIDTH = 640
INPUT_HEIGHT = 640
UDP_HOST = "127.0.0.1"
UDP_PORT = 5005
MJPEG_URL = "http://127.0.0.1:8082/stream"


def preprocess(frame: np.ndarray) -> np.ndarray:
    """Bild auf Modell-Eingabegroesse skalieren (uint8 RGB fuer Hailo)."""
    resized = cv2.resize(frame, (INPUT_WIDTH, INPUT_HEIGHT))
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    return rgb.astype(np.uint8)


def postprocess(raw_output: dict, orig_h: int, orig_w: int, threshold: float) -> list:
    """Hailo-NMS-Ausgabe in Detektionsliste umwandeln.

    Hailo-HEF mit integriertem NMS liefert einen ragged Array:
    data[0][class_id] = np.array shape (N_i, 5) pro Klasse,
    wobei 5 = [y_min, x_min, y_max, x_max, confidence], normalisiert [0,1].
    N_i variiert je Klasse (inhomogene Dimensionen).
    """
    detections = []
    for _name, data in raw_output.items():
        # Batch-Dimension: data[0] = Array mit 80 Klassen-Arrays
        batch = data[0] if hasattr(data, "__getitem__") else data
        num_classes = len(batch)

        for class_id in range(num_classes):
            class_dets = batch[class_id]
            if class_dets is None or len(class_dets) == 0:
                continue

            for det in class_dets:
                confidence = float(det[4])
                if confidence < threshold:
                    continue

                y1 = float(det[0]) * orig_h
                x1 = float(det[1]) * orig_w
                y2 = float(det[2]) * orig_h
                x2 = float(det[3]) * orig_w

                label = (
                    COCO_LABELS_DE[class_id]
                    if class_id < len(COCO_LABELS_DE)
                    else f"Klasse_{class_id}"
                )
                detections.append(
                    {
                        "class_id": class_id,
                        "label": label,
                        "confidence": round(confidence, 3),
                        "bbox": [
                            round(x1, 1),
                            round(y1, 1),
                            round(x2, 1),
                            round(y2, 1),
                        ],
                    }
                )
    return detections


def run_fallback(udp_sock: socket.socket):
    """Fallback-Modus: Dummy-Detektionen ohne Hailo-Hardware."""
    print("[FALLBACK] Sende Dummy-Detektionen (sports ball) @ 5 Hz ...")
    print(f"[FALLBACK] UDP → {UDP_HOST}:{UDP_PORT}")

    count = 0
    while True:
        payload = json.dumps(
            {
                "timestamp": time.time(),
                "inference_ms": 0.0,
                "detections": [
                    {
                        "class_id": 32,
                        "label": "sports ball",
                        "confidence": 0.85,
                        "bbox": [678.0, 494.0, 778.0, 594.0],
                    }
                ],
            }
        ).encode("utf-8")

        udp_sock.sendto(payload, (UDP_HOST, UDP_PORT))
        count += 1
        if count % 25 == 0:
            print(f"[FALLBACK] {count} Pakete gesendet")
        time.sleep(0.2)


def run_hailo(model_path: str, threshold: float, udp_sock: socket.socket):
    """Hailo-8 Inference mit MJPEG-Stream als Eingabe."""
    try:
        from hailo_platform import (
            HEF,
            ConfigureParams,
            FormatType,
            HailoStreamInterface,
            InferVStreams,
            InputVStreamParams,
            OutputVStreamParams,
            VDevice,
        )
    except ImportError:
        print("FEHLER: hailo_platform nicht verfuegbar!")
        print("Installiere hailort oder nutze --fallback")
        sys.exit(1)

    print(f"[HAILO] Lade Modell: {model_path}")
    hef = HEF(model_path)
    vdevice = VDevice()
    configure_params = ConfigureParams.create_from_hef(hef, interface=HailoStreamInterface.PCIe)
    network_group = vdevice.configure(hef, configure_params)[0]

    input_vstream_info = hef.get_input_vstream_infos()
    output_vstream_info = hef.get_output_vstream_infos()

    input_params = InputVStreamParams.make_from_network_group(
        network_group, quantized=False, format_type=FormatType.UINT8
    )
    output_params = OutputVStreamParams.make_from_network_group(
        network_group, quantized=False, format_type=FormatType.FLOAT32
    )

    print(
        f"[HAILO] Initialisiert: {len(input_vstream_info)} Input(s), "
        f"{len(output_vstream_info)} Output(s)"
    )
    print(f"[HAILO] MJPEG-Quelle: {MJPEG_URL}")
    print(f"[HAILO] UDP → {UDP_HOST}:{UDP_PORT}")
    print(f"[HAILO] Threshold: {threshold}, Rate: 5 Hz")

    MAX_STARTUP_RETRIES = 10
    retry_delay = 2.0
    cap = None
    for attempt in range(1, MAX_STARTUP_RETRIES + 1):
        cap = cv2.VideoCapture(MJPEG_URL)
        if cap.isOpened():
            print(f"[HAILO] MJPEG-Stream verbunden (Versuch {attempt})")
            break
        cap.release()
        if attempt < MAX_STARTUP_RETRIES:
            print(
                f"[HAILO] MJPEG-Stream nicht erreichbar, "
                f"Versuch {attempt}/{MAX_STARTUP_RETRIES} "
                f"(naechster in {retry_delay:.0f}s)"
            )
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 1.5, 30.0)
    else:
        print(
            f"FEHLER: MJPEG-Stream nach {MAX_STARTUP_RETRIES} Versuchen "
            f"nicht erreichbar: {MJPEG_URL}"
        )
        print("Ist dashboard_bridge gestartet?")
        sys.exit(1)

    with (
        network_group.activate(),
        InferVStreams(network_group, input_params, output_params) as pipeline,
    ):
        count = 0
        while True:
            t_start = time.monotonic()

            ret, frame = cap.read()
            if not ret:
                # Reconnect bei Stream-Abbruch
                cap.release()
                time.sleep(1.0)
                cap = cv2.VideoCapture(MJPEG_URL)
                continue

            # Kamera ist 180° gedreht montiert — Bild vor Inference drehen
            frame = cv2.rotate(frame, cv2.ROTATE_180)
            orig_h, orig_w = frame.shape[:2]
            preprocessed = preprocess(frame)
            input_data = {input_vstream_info[0].name: np.expand_dims(preprocessed, axis=0)}

            t_infer = time.monotonic()
            raw_output = pipeline.infer(input_data)
            dt_ms = (time.monotonic() - t_infer) * 1000.0

            if count == 0:
                for name, data in raw_output.items():
                    batch = data[0]
                    sizes = [len(batch[i]) for i in range(len(batch))]
                    total = sum(sizes)
                    print(
                        f'[DEBUG] Output "{name}": {len(batch)} Klassen, {total} Detektionen gesamt'
                    )

            detections = postprocess(raw_output, orig_h, orig_w, threshold)

            payload = json.dumps(
                {
                    "timestamp": time.time(),
                    "inference_ms": round(dt_ms, 1),
                    "detections": detections,
                }
            ).encode("utf-8")

            udp_sock.sendto(payload, (UDP_HOST, UDP_PORT))

            count += 1
            if detections and count % 5 == 0:
                labels = [d["label"] for d in detections]
                print(f"[HAILO] {len(detections)} Objekt(e) in {dt_ms:.1f} ms: {', '.join(labels)}")
            elif count % 25 == 0:
                print(f"[HAILO] Frame {count}: {dt_ms:.1f} ms, keine Detektionen")

            # Rate-Limiting auf 5 Hz
            elapsed = time.monotonic() - t_start
            sleep_time = 0.2 - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    cap.release()  # type: ignore[unreachable]


def main():
    parser = argparse.ArgumentParser(description="Hailo-8 Inference Runner (Host-seitig)")
    parser.add_argument(
        "--model",
        default="hardware/models/yolov8s.hef",
        help="Pfad zum HEF-Modell (Default: hardware/models/yolov8s.hef)",
    )
    parser.add_argument(
        "--threshold", type=float, default=0.35, help="Confidence-Schwellwert (Default: 0.35)"
    )
    parser.add_argument(
        "--fallback",
        action="store_true",
        help="Fallback-Modus: Dummy-Detektionen ohne Hailo-Hardware",
    )
    args = parser.parse_args()

    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print("=== Hailo-8 Host Runner ===")
    print(f"Modus: {'FALLBACK' if args.fallback else 'HAILO'}")

    try:
        if args.fallback:
            run_fallback(udp_sock)
        else:
            run_hailo(args.model, args.threshold, udp_sock)
    except KeyboardInterrupt:
        print("\nBeendet.")
    finally:
        udp_sock.close()


if __name__ == "__main__":
    main()
