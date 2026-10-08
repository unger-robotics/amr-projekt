# S-A Auswertung: 20260903_1956_A1

Datenframes gesamt: 113179, Messdauer aus Log: 600.0 s, mittlere Rate: 188.6 Frames/s

## Zaehler-Deltas (nachher - vorher)

| Zaehler | vorher | nachher | Delta |
| --- | --- | --- | --- |
| rx_packets | 2306544 | 2419723 | 113179 |
| rx_errors | 129299 | 135973 | 6674 |
| rx_over_errors | 129299 | 135973 | 6674 |
| rx_fifo_errors | 0 | 0 | 0 |
| rx_missed_errors | 0 | 0 | 0 |
| rx_dropped | 2267223 | 2267223 | 0 |
| bus_error | 0 | 0 | 0 |
| arbitration_lost | 0 | 0 | 0 |
| error_warning | 0 | 0 | 0 |
| error_passive | 0 | 0 | 0 |
| bus_off | 0 | 0 | 0 |
| restarts | 0 | 0 | 0 |

## Je ID: Empfang, Verlust, Zwischenankunftszeit

| ID | Soll [Hz] | erwartet | empfangen | Verlust [%] | dt Median [ms] | dt p99 [ms] | dt max [ms] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0x110 | 10 | 6000 | 6000 | 0.00 | 100.0 | 110.0 | 110.1 |
| 0x120 | 20 | 12000 | 12000 | 0.00 | 50.0 | 50.1 | 50.1 |
| 0x130 | 50 | 29999 | 30001 | 0.00 | 20.0 | 20.2 | 20.3 |
| 0x131 | 50 | 29999 | 29768 | 0.77 | 20.0 | 20.2 | 40.3 |
| 0x140 | 2 | 1200 | 1200 | 0.00 | 500.0 | 500.3 | 500.5 |
| 0x1F0 | 1 | 600 | 600 | 0.00 | 1000.0 | 1000.3 | 1000.7 |
| 0x200 | 20 | 12000 | 9419 | 21.51 | 59.5 | 100.1 | 640.3 |
| 0x201 | 20 | 12000 | 12000 | 0.00 | 59.3 | 59.8 | 60.0 |
| 0x210 | 10 | 6000 | 5971 | 0.48 | 100.0 | 100.2 | 400.2 |
| 0x220 | 10 | 6000 | 5620 | 6.33 | 100.0 | 300.0 | 1700.0 |
| 0x2F0 | 1 | 600 | 600 | 0.00 | 1000.0 | 1000.2 | 1000.3 |

Rechnerische Buslast (ohne Stuffing): 1.75 % bei 1 Mbit/s

## Burst-Fenster (>= 3 Frames innerhalb Fenster)

| Fenster [us] | Anzahl |
| --- | --- |
| 300 | 0 |
| 500 | 5099 |
| 1000 | 16101 |
| 2000 | 19146 |

| ID als 3. oder spaeterer Frame im Burst (1000 us) | Anzahl |
| --- | --- |
| 0x131 | 7915 |
| 0x201 | 6805 |
| 0x200 | 4839 |
| 0x210 | 1656 |
| 0x220 | 1203 |
| 0x2F0 | 199 |
| 0x140 | 26 |
| 0x1F0 | 10 |

## Error-Frames im Log: 6674, davon RX-Ueberlauf (CAN_ERR_CRTL_RX_OVERFLOW): 6674

| Daten-ID unmittelbar vor dem Ueberlauf-Frame | Anzahl |
| --- | --- |
| 0x220 | 3351 |
| 0x201 | 2401 |
| 0x200 | 471 |
| 0x131 | 340 |
| 0x210 | 108 |
| 0x2F0 | 2 |
| 0x130 | 1 |

Lesart: Faellt der Verlust genau auf die IDs, die im Burst als 3. Frame ankommen, und steigt rx_over_errors (Ueberlauf-Error-Frames im Log), ist es Fall 1 (MCP2515). Steigt bus_error, Fall 2. Beides 0 bei Verlust > 0,1 %: Fall 3.
