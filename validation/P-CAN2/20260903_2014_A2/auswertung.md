# S-A Auswertung: 20260903_2014_A2

Datenframes gesamt: 113118, Messdauer aus Log: 600.0 s, mittlere Rate: 188.5 Frames/s

## Zaehler-Deltas (nachher - vorher)

| Zaehler | vorher | nachher | Delta |
| --- | --- | --- | --- |
| rx_packets | 2507679 | 2620803 | 113124 |
| rx_errors | 140601 | 146602 | 6001 |
| rx_over_errors | 140601 | 146602 | 6001 |
| rx_fifo_errors | 0 | 0 | 0 |
| rx_missed_errors | 0 | 0 | 0 |
| rx_dropped | 2267223 | 2267223 | 0 |
| bus_error | 0 | 0 | 0 |
| arbitration_lost | 0 | 0 | 0 |
| error_warning | 1 | 1 | 0 |
| error_passive | 1 | 1 | 0 |
| bus_off | 0 | 0 | 0 |
| restarts | 0 | 0 | 0 |

## Je ID: Empfang, Verlust, Zwischenankunftszeit

| ID | Soll [Hz] | erwartet | empfangen | Verlust [%] | dt Median [ms] | dt p99 [ms] | dt max [ms] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0x110 | 10 | 6000 | 6000 | 0.00 | 100.0 | 110.1 | 120.0 |
| 0x120 | 20 | 12000 | 12000 | 0.00 | 50.0 | 50.1 | 50.3 |
| 0x130 | 50 | 29999 | 30000 | 0.00 | 20.0 | 20.2 | 20.4 |
| 0x131 | 50 | 29999 | 30000 | 0.00 | 20.0 | 20.2 | 20.4 |
| 0x140 | 2 | 1200 | 1200 | 0.00 | 500.0 | 500.4 | 500.6 |
| 0x1F0 | 1 | 600 | 600 | 0.00 | 1000.0 | 1000.4 | 1000.7 |
| 0x200 | 20 | 12000 | 8718 | 27.35 | 59.6 | 100.1 | 100.3 |
| 0x201 | 20 | 12000 | 12000 | 0.00 | 59.3 | 59.8 | 60.1 |
| 0x210 | 10 | 6000 | 6000 | 0.00 | 100.0 | 100.1 | 100.3 |
| 0x220 | 10 | 6000 | 6000 | 0.00 | 100.0 | 100.1 | 100.3 |
| 0x2F0 | 1 | 600 | 600 | 0.00 | 1000.0 | 1000.0 | 1000.1 |

Rechnerische Buslast (ohne Stuffing): 1.75 % bei 1 Mbit/s

## Burst-Fenster (>= 3 Frames innerhalb Fenster)

| Fenster [us] | Anzahl |
| --- | --- |
| 300 | 0 |
| 500 | 2999 |
| 1000 | 13833 |
| 2000 | 13930 |

| ID als 3. oder spaeterer Frame im Burst (1000 us) | Anzahl |
| --- | --- |
| 0x131 | 7812 |
| 0x201 | 6000 |
| 0x200 | 2718 |
| 0x140 | 24 |
| 0x1F0 | 14 |

## Error-Frames im Log: 6000, davon RX-Ueberlauf (CAN_ERR_CRTL_RX_OVERFLOW): 6000

| Daten-ID unmittelbar vor dem Ueberlauf-Frame | Anzahl |
| --- | --- |
| 0x220 | 4394 |
| 0x201 | 1606 |

Lesart: Faellt der Verlust genau auf die IDs, die im Burst als 3. Frame ankommen, und steigt rx_over_errors (Ueberlauf-Error-Frames im Log), ist es Fall 1 (MCP2515). Steigt bus_error, Fall 2. Beides 0 bei Verlust > 0,1 %: Fall 3.
