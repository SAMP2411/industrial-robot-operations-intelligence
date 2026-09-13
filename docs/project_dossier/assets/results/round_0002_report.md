# Patrol Round 2 Report

- Mission Profile: targeted_follow_up
- Scenario ID: advanced_multimodal_seed_6262
- Run ID: advanced_multimodal_seed_6262_20260405T231351053826+0000
- Status: SUCCESS
- Duration: 35.9 s
- Action Result: SUCCEEDED
- Nav2 Error Code: 0
- Site Alert Level: warning
- Inspections: 2
- Anomalies: 2
- Review Required: 0
- Degraded Assets: 2
- Thermal / Acoustic / Gas Alerts: 0 / 2 / 0
- Average Health Score: 73.4
- Lowest Health Score: 73.1
- Average Confidence: 0.86
- Detection Accuracy: 100.0%
- Detection Precision / Recall / F1: 100.0% / 100.0% / 100.0%
- Mission Decision: RESUME_WATCHLIST
- Decision Reason: Follow-up assets remained stable across repeated passes. Resuming routine patrol while keeping them on the watchlist.
- Follow-Up Assets: CMP-220, CNV-510

## Zones

- packing_lane | inspections=1 | anomalies=1 | critical=0 | avg_health=73.7
- utilities_bay | inspections=1 | anomalies=1 | critical=0 | avg_health=73.1

## Assets

- [CMP-220] Compressor Cell | zone=utilities_bay | severity=warning | label=belt_slip | confidence=0.99 | review=none | health=73.1 | sources=visual+acoustic | image=/home/samarth/.ros/factory_inspection/benchmark/0000_upper_right_turn_belt_slip_10315968000000_annotated.png | raw=/home/samarth/.ros/factory_inspection/benchmark/0000_upper_right_turn_belt_slip_10315968000000_raw.png
- [CNV-510] Packing Conveyor Drive | zone=packing_lane | severity=warning | label=roller_imbalance | confidence=0.72 | review=none | health=73.7 | sources=acoustic | image=/home/samarth/.ros/factory_inspection/benchmark/0001_spawn_lane_roller_imbalance_10342395000000_annotated.png | raw=/home/samarth/.ros/factory_inspection/benchmark/0001_spawn_lane_roller_imbalance_10342395000000_raw.png
