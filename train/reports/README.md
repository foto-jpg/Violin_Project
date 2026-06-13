# train/reports/ - ผลการเทรน & ประเมิน

ไฟล์รายงานจริง (CSV/JSON/MD) จากการ fine-tune CREPE รอบ `finetune_2026-05-23`
(เก็บเฉพาะไฟล์เล็ก - checkpoint `.pt` และ `.zip` ขนาดใหญ่ถูกกันออก)

## ไฟล์เด่น
| ไฟล์ | เนื้อหา |
|------|---------|
| `training_log_epoch.csv` | metric ราย epoch (train_loss, val_RPA/RCA/MAE) |
| `training_log.csv` | metric ราย step |
| `training_summary.json` | สรุปการเทรน (best_epoch, stop_reason, config) |
| `baseline_metrics.*` / `finetuned_metrics.*` | เทียบก่อน/หลัง fine-tune บน 3 test set |
| `error_analysis_report.md` | วิเคราะห์ข้อผิดพลาด + recordings ที่แย่สุด |
| `training_results_report.md` | รายงานสรุปผลรวม |

## สรุปผล
- เทรนตั้งไว้ 30 epoch แต่หยุดที่ epoch 5 (best = **epoch 1**, val RPA ~0.66)
- best.pt ดีกว่า baseline ทุก test set  นำไป deploy เป็น `backend/checkpoints/crepe_violin.pt`
