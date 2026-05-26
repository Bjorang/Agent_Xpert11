# compare.py
import json
import sys
from pathlib import Path
from datetime import datetime


def load_snapshot(filepath: str) -> list[dict]:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def compare_snapshots(before: list[dict], after: list[dict]) -> list[dict]:
    before_map = {p["player_id"]: p for p in before}
    after_map  = {p["player_id"]: p for p in after}
    
    diffs = []
    all_ids = set(before_map) | set(after_map)
    
    for pid in all_ids:
        b = before_map.get(pid)
        a = after_map.get(pid)
        
        if not b:
            diffs.append({"name": a["name"], "change": "NY SPELARE", "form_current_before": "-", "form_current_after": a["form_current"], "form_current_diff": "-", "form_average_before": "-", "form_average_after": a["form_average"], "condition_before": "-", "condition_after": a["condition"]})
            continue
        if not a:
            diffs.append({"name": b["name"], "change": "BORTA", "form_current_before": b["form_current"], "form_current_after": "-", "form_current_diff": "-", "form_average_before": b["form_average"], "form_average_after": "-", "condition_before": b["condition"], "condition_after": "-"})
            continue

        form_current_before = int(b["form_current"]) if b["form_current"] != "N/A" else 0
        form_current_after  = int(a["form_current"]) if a["form_current"] != "N/A" else 0
        form_current_diff   = form_current_after - form_current_before

        form_average_before = int(b["form_average"]) if b["form_average"] != "N/A" else 0
        form_average_after  = int(a["form_average"]) if a["form_average"] != "N/A" else 0
        form_average_diff   = form_average_after - form_average_before

        diffs.append({
            "name":                 b["name"],
            "age":                  b["age"],
            "skill":                b["skill"],
            "uv":                   a["uv"],
            "form_current_before":  form_current_before,
            "form_current_after":   form_current_after,
            "form_current_diff":    form_current_diff,
            "form_average_before":  form_average_before,
            "form_average_after":   form_average_after,
            "form_average_diff":    form_average_diff,
            "condition_before":     b["condition"],
            "condition_after":      a["condition"],
        })

    diffs.sort(key=lambda x: x.get("form_current_diff", 0) if isinstance(x.get("form_current_diff"), int) else 0, reverse=True)
    return diffs


def save_diff_json(diffs: list[dict], label: str = "diff"):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{label}_{ts}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(diffs, f, ensure_ascii=False, indent=2)
    print(f"💾 JSON sparad: {filename}")
    return filename


def generate_html_report(diffs: list[dict], label: str = "rapport"):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{label}_{ts}.html"

    rows = ""
    for p in diffs:
        def diff_cell(diff):
            if isinstance(diff, int):
                color = "green" if diff > 0 else ("red" if diff < 0 else "gray")
                return f"<span style='color:{color};font-weight:bold;'>{'+'if diff > 0 else ''}{diff}</span>"
            return diff

        cond_changed = p["condition_before"] != p["condition_after"]
        cond_style = "background-color:#fff3cd;" if cond_changed else ""

        rows += f"""
        <tr style="{cond_style}">
            <td>{p['name']}</td>
            <td>{p.get('age', '-')}</td>
            <td>{p.get('skill', '-')}</td>
            <td>{p.get('uv', '-')}</td>
            <td>{p['form_current_before']}</td>
            <td>{p['form_current_after']}</td>
            <td>{diff_cell(p['form_current_diff'])}</td>
            <td>{p['form_average_before']}</td>
            <td>{p['form_average_after']}</td>
            <td>{diff_cell(p['form_average_diff'])}</td>
            <td>{p['condition_before']}</td>
            <td>{p['condition_after']}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <title>Formrapport</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; }}
        h1 {{ color: #003B66; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th {{ background-color: #003B66; color: white; padding: 8px 12px; text-align: left; }}
        td {{ padding: 7px 12px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background-color: #f5f5f5; }}
    </style>
</head>
<body>
    <h1>Formrapport — {datetime.now().strftime('%Y-%m-%d %H:%M')}</h1>
    <table>
        <tr>
            <th>Namn</th><th>Ålder</th><th>Skill</th><th>UV</th>
            <th>Form före</th><th>Form efter</th><th>Form diff</th>
            <th>Medel före</th><th>Medel efter</th><th>Medel diff</th>
            <th>Kondition före</th><th>Kondition efter</th>
        </tr>
        {rows}
    </table>
    <p style="color:gray;font-size:12px;">Gul rad = konditionsförändring</p>
</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"🌐 HTML sparad: {filename}")
    return filename


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Användning: python compare.py <before.json> <after.json>")
        sys.exit(1)

    before = load_snapshot(sys.argv[1])
    after  = load_snapshot(sys.argv[2])
    diffs  = compare_snapshots(before, after)

    save_diff_json(diffs)
    generate_html_report(diffs)
