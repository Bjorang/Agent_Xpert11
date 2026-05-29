import json
import sys
from pathlib import Path
from datetime import datetime

def parse_uv(value: str) -> int:
    """Konverterar UV-sträng som '+3' eller '-2' till int."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0

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
        
       # Hantera om spelaren är helt ny
        if not b:
            diffs.append({
                "name": a["name"], 
                "age": a.get("age", "-"),
                "skill": a.get("skill", "-"),
                "uv": a.get("uv", "-"),
                "change": "NY SPELARE", 
                "uv_after": a.get("uv", "-"), 
                "uv_diff": "-",
                "form_current_before": "-", "form_current_after": a["form_current"], "form_current_diff": "-", 
                "form_average_before": "-", "form_average_after": a["form_average"], "form_average_diff": "-",
                "condition_before": "-", "condition_after": a["condition"]
            })
            continue
            
        # Hantera om spelaren har lämnat
        if not a:
            diffs.append({
                "name": b["name"], 
                "age": b.get("age", "-"),
                "skill": b.get("skill", "-"),
                "uv": b.get("uv", "-"),
                "change": "BORTA", 
                "uv_after": "-", 
                "uv_diff": "-",
                "form_current_before": b["form_current"], "form_current_after": "-", "form_current_diff": "-", 
                "form_average_before": b["form_average"], "form_average_after": "-", "form_average_diff": "-",
                "condition_before": b["condition"], "condition_after": "-"
            })
            continue

        # Beräkna UV
        uv_after  = parse_uv(a.get("uv"))
        uv_diff   = uv_after - parse_uv(b.get("uv"))

        # Beräkna nuvarande form
        form_current_before = int(b["form_current"]) if b["form_current"] != "N/A" else 0
        form_current_after  = int(a["form_current"]) if a["form_current"] != "N/A" else 0
        form_current_diff   = form_current_after - form_current_before

        # Beräkna medelform
        form_average_before = int(b["form_average"]) if b["form_average"] != "N/A" else 0
        form_average_after  = int(a["form_average"]) if a["form_average"] != "N/A" else 0
        form_average_diff   = form_average_after - form_average_before

        diffs.append({
            "name":                 b["name"],
            "age":                  b["age"],
            "skill":                b["skill"],
            "uv":                   a["uv"],
            "uv_before": parse_uv(b.get("uv")),
            "uv_after":             uv_after,
            "uv_diff":              uv_diff,
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

       # Här matchar vi exakt mot rubrikerna nedan
        rows += f"""
        <tr style="{cond_style}">
            <td>{p['name']}</td>
            <td>{p.get('age', '-')}</td>
            <td>{p.get('skill', '-')}</td>
           <td>{p.get('uv_before', '-')}</td>
            <td>{p.get('uv_after', '-')}</td>
            <td>{diff_cell(p.get('uv_diff', '-'))}</td>
            <td>{p.get('form_current_before', '-')}</td>
            <td>{p.get('form_current_after', '-')}</td>
            <td>{diff_cell(p.get('form_current_diff', '-'))}</td>
            <td>{p.get('form_average_before', '-')}</td>
            <td>{p.get('form_average_after', '-')}</td>
            <td>{diff_cell(p.get('form_average_diff', '-'))}</td>
            <td>{p.get('condition_before', '-')}</td>
            <td>{p.get('condition_after', '-')}</td>
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
            <th>UV före</th><th>UV efter</th><th>UV diff</th>
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
    from pathlib import Path

    # Hitta alla snapshot-filer
    fore_files  = sorted(Path(".").glob("*_fore_match_*.json"))
    efter_files = sorted(Path(".").glob("*_efter_match_*.json"))

    if not fore_files or not efter_files:
        print("⚠️ Inga snapshot-filer hittades!")
        sys.exit(1)

    # Visa FÖRE-filer
    print("\nTillgängliga FÖRE-filer:")
    for i, f in enumerate(fore_files, start=1):
        print(f"  {i}. {f.name}")
    fore_default = len(fore_files)
    fore_val = input(f"Välj FÖRE-fil (1-{len(fore_files)}) [standard: {fore_default}]: ").strip()
    fore_index = int(fore_val) - 1 if fore_val else fore_default - 1
    fore_file = fore_files[fore_index]

    # Visa EFTER-filer
    print("\nTillgängliga EFTER-filer:")
    for i, f in enumerate(efter_files, start=1):
        print(f"  {i}. {f.name}")
    efter_default = len(efter_files)
    efter_val = input(f"Välj EFTER-fil (1-{len(efter_files)}) [standard: {efter_default}]: ").strip()
    efter_index = int(efter_val) - 1 if efter_val else efter_default - 1
    efter_file = efter_files[efter_index]

    print(f"\n📂 Jämför:")
    print(f"   FÖRE:  {fore_file.name}")
    print(f"   EFTER: {efter_file.name}")

    before = load_snapshot(str(fore_file))
    after  = load_snapshot(str(efter_file))
    diffs  = compare_snapshots(before, after)

    save_diff_json(diffs)
    generate_html_report(diffs)