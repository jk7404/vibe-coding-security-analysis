import json
import pandas as pd

files = {
    ("uploader", "vibe"):    "results_uploader_vibe.json",
    ("uploader", "cot"):     "results_uploader_cot.json",
    ("uploader", "pns"):     "results_uploader_pns.json",
    ("uploader", "tdd"):     "results_uploader_tdd.json",
    ("password_manager", "vibe"): "results_pm_vibe.json",
    ("password_manager", "cot"):  "results_pm_cot.json",
    ("password_manager", "pns"):  "results_pm_pns.json",
    ("password_manager", "tdd"):  "results_pm_tdd.json",
}

rows = []
for (task, method), path in files.items():
    with open(path) as f:
        data = json.load(f)
    
    issues = data.get("results", [])
    total = len(issues)
    high   = sum(1 for i in issues if i["issue_severity"] == "HIGH")
    medium = sum(1 for i in issues if i["issue_severity"] == "MEDIUM")
    low    = sum(1 for i in issues if i["issue_severity"] == "LOW")
    
    rows.append({
        "task": task,
        "method": method,
        "total_issues": total,
        "high": high,
        "medium": medium,
        "low": low,
    })

df = pd.DataFrame(rows)
print(df.to_string(index=False))
df.to_csv("summary.csv", index=False)
print("\nsummary.csv 저장됨!")