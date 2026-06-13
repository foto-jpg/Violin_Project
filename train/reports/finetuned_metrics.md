# crepe-full หลัง fine-tune (best.pt)

รัน: 2026-05-24
Preprocessing: 16 kHz mono, hop 10 ms, voicing threshold 0.5

| ชุดทดสอบ | n_rec | RPA | RCA | MAE_cents | n_frames |
|-----------------|------:|------:|------:|----------:|---------:|
| MOSA_test       |    52 | 0.862 | 0.871 |      60.1 |   514358 |
| MusicNet_test   |    12 | 0.309 | 0.418 |     706.5 |    99916 |
| Bach10          |    10 | 0.982 | 0.983 |      16.5 |    28832 |
| URMP            |     - |   N/A |   N/A |       N/A |        - |
