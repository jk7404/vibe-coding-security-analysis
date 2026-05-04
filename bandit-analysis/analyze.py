import json
import pandas as pd

files = {
    # user_profile_picture_uploader
    ("uploader", "vibe", "gpt5"):  "results_uploader2_vibe_gpt5.json",
    ("uploader", "vibe", "haiku"): "results_uploader2_vibe_haiku.json",
    ("uploader", "cot", "gpt5"):   "results_uploader2_cot_gpt5.json",
    ("uploader", "cot", "haiku"):  "results_uploader2_cot_haiku.json",
    ("uploader", "pns", "gpt5"):   "results_uploader2_pns_gpt5.json",
    ("uploader", "pns", "haiku"):  "results_uploader2_pns_haiku.json",
    ("uploader", "tdd", "gpt5"):   "results_uploader2_tdd_gpt5.json",
    ("uploader", "tdd", "haiku"):  "results_uploader2_tdd_haiku.json",
    # password_manager
    ("password_manager", "vibe", "gpt5"):  "results_pm2_vibe_gpt5.json",
    ("password_manager", "vibe", "haiku"): "results_pm2_vibe_haiku.json",
    ("password_manager", "cot", "gpt5"):   "results_pm2_cot_gpt5.json",
    ("password_manager", "cot", "haiku"):  "results_pm2_cot_haiku.json",
    ("password_manager", "pns", "gpt5"):   "results_pm2_pns_gpt5.json",
    ("password_manager", "pns", "haiku"):  "results_pm2_pns_haiku.json",
    ("password_manager", "tdd", "gpt5"):   "results_pm2_tdd_gpt5.json",
    ("password_manager", "tdd", "haiku"):  "results_pm2_tdd_haiku.json",
    # server_log_manager
    ("server_log_manager", "vibe", "gpt5"):  "results_slm2_vibe_gpt5.json",
    ("server_log_manager", "vibe", "haiku"): "results_slm2_vibe_haiku.json",
    ("server_log_manager", "cot", "gpt5"):   "results_slm2_cot_gpt5.json",
    ("server_log_manager", "cot", "haiku"):  "results_slm2_cot_haiku.json",
    ("server_log_manager", "pns", "gpt5"):   "results_slm2_pns_gpt5.json",
    ("server_log_manager", "pns", "haiku"):  "results_slm2_pns_haiku.json",
    ("server_log_manager", "tdd", "gpt5"):   "results_slm2_tdd_gpt5.json",
    ("server_log_manager", "tdd", "haiku"):  "results_slm2_tdd_haiku.json",
}

rows = []
for (task, method, model), path in files.items():
    with open(path) as f:
        data = json.load(f)

    issues = data.get("results", [])
    rows.append({
        "task":         task,
        "method":       method,
        "model":        model,
        "total_issues": len(issues),
        "high":         sum(1 for i in issues if i["issue_severity"] == "HIGH"),
        "medium":       sum(1 for i in issues if i["issue_severity"] == "MEDIUM"),
        "low":          sum(1 for i in issues if i["issue_severity"] == "LOW"),
    })

df = pd.DataFrame(rows)
print(df.to_string(index=False))
df.to_csv("summary2.csv", index=False)
print("\nsummary2.csv saved!")