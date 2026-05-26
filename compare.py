# compare.py
import json
import sys
from pathlib import Path
from datetime import datetime


def load_snapshot(filepath: str) -> list[dict]:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def compare_snapshots(before: list[dict], after: list[dict]) -> list[dict]:
    """Jämför två snapshots och returnerar differenser per spelare."""
    before_map = {p["player_id"]: p for p in before}
    after_map  = {p["player_id"]: p for p in after}
    
    diffs = []
    all_ids = set(before_map) | set(after_map)
    
    for pid in all_ids:
        b = before_map.get(pid)
        a = after_map.get(pid)
        
        if not b:
            diffs.append({"name": a["name"], "change": "NY SPELARE", "form_before": "-", "form_after": a["form"], "form_diff": "-", "condition_before": "-", "condition_after": a["condition"]})
            continue
        if not a:
            diffs.append({"name": b["name"], "change": "BORTA", "form_before": b["form"], "form_after": "-", "form_diff": "-", "condition_before": b["condition"], "condition_after": "-"})
            continue

        form_before = int(b["form"]) if b["form"] != "N/A" else 0
        form_after  = int(a["form"]) if a["form"] != "N/A" else 0
        form_diff   = form_after - form_before

        diffs.append({
            "name":              b["name"],
            "age":               b["age"],
            "skill":             b["skill"],
            "form_before":       form_before,
            "form_after":        form_after,
            "form_diff":         form_diff,
            "condition_before":  b["condition"],
            "condition_after":   a["condition"],
            "uv":                a["uv"],
        })

    diffs.sort(key=lambda x: x.get("form_diff", 0) if isinstance(x.get("form_diff"), int) else 0, reverse=True)
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
        diff = p.get("form_diff", "-")
        if isinstance(diff, int):
            color = "green" if diff > 0 else ("red" if diff < 0 else "gray")
            diff_str = f"+{diff}" if diff > 0 else str(diff)
        else:
            color = "gray"
            diff_str = diff

        cond_changed = p["condition_before"] != p["condition_after"]
        cond_style = "background-color:#fff3cd;" if cond_changed else ""

        rows += f"""
        <tr style="{cond_style}">
            <td>{p['name']}</td>
            <td>{p.get('age', '-')}</td>
            <td>{p.get('skill', '-')}</td>
            <td>{p['form_before']}</td>
            <td>{p['form_after']}</td>
            <td style="color:{color};font-weight:bold;">{diff_str}</td>
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
            <th>Namn</th><th>Ålder</th><th>Skill</th>
            <th>Form före</th><th>Form efter</th><th>Diff</th>
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
