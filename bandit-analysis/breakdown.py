import json
import pandas as pd

files = {
    ("uploader", "vibe"):         "results_uploader_vibe.json",
    ("uploader", "cot"):          "results_uploader_cot.json",
    ("uploader", "pns"):          "results_uploader_pns.json",
    ("uploader", "tdd"):          "results_uploader_tdd.json",
    ("password_manager", "vibe"): "results_pm_vibe.json",
    ("password_manager", "cot"):  "results_pm_cot.json",
    ("password_manager", "pns"):  "results_pm_pns.json",
    ("password_manager", "tdd"):  "results_pm_tdd.json",
}

rows = []
for (task, method), path in files.items():
    with open(path) as f:
        data = json.load(f)
    
    for issue in data.get("results", []):
        rows.append({
            "task":       task,
            "method":     method,
            "filename":   issue["filename"].split("/")[-1],
            "severity":   issue["issue_severity"],
            "confidence": issue["issue_confidence"],
            "test_id":    issue["test_id"],
            "test_name":  issue["test_name"],
            "issue_text": issue["issue_text"],
            "line_number": issue["line_number"],
        })

df = pd.DataFrame(rows)
print(df.to_string(index=False))
df.to_csv("detailed_results.csv", index=False)
print("\ndetailed_results.csv saved!")