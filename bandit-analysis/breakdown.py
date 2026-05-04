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
    
    for issue in data.get("results", []):
        rows.append({
            "task":        task,
            "method":      method,
            "model":       model,
            "filename":    issue["filename"].split("/")[-1],
            "severity":    issue["issue_severity"],
            "confidence":  issue["issue_confidence"],
            "test_id":     issue["test_id"],
            "test_name":   issue["test_name"],
            "issue_text":  issue["issue_text"],
            "line_number": issue["line_number"],
        })

df = pd.DataFrame(rows)
print(df.to_string(index=False))
df.to_csv("detailed_results2.csv", index=False)
print("\ndetailed_results2.csv saved!")