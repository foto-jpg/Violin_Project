# crepe-full (pretrained ก่อน fine-tune)

รัน: 2026-05-23
Preprocessing: 16 kHz mono, hop 10 ms, voicing threshold 0.5

| ชุดทดสอบ | n_rec | RPA | RCA | MAE_cents | n_frames |
|-----------------|------:|------:|------:|----------:|---------:|
| MOSA_test       |    52 | 0.811 | 0.823 |      92.0 |   553463 |
| MusicNet_test   |    12 | 0.119 | 0.250 |    1470.6 |   302627 |
| Bach10          |    10 | 0.967 | 0.968 |      14.8 |    29514 |
| URMP            |     - |   N/A |   N/A |       N/A |        - |
