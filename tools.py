# tools.py
import os
import json
from datetime import datetime
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv("XE_USERNAME")
PASSWORD = os.getenv("XE_PASSWORD")

BASE_URL    = "https://www.xperteleven.com"
LOGIN_URL   = f"{BASE_URL}/default.aspx"
TEAM_URL    = "https://www.xperteleven.com/players.aspx?dh=2&TeamID=1952957&Boost=1"
TEAM_NAME   = "Odensala Döders"

TEAMS = {
    "1": {
        "name": "Odensala Döders",
        "team_id": "1952957",
        "url": "https://www.xperteleven.com/players.aspx?dh=2&TeamID=1952957&Boost=1",
        "lobby_id": "#ctl00_cphMain_gvFriendsTeam_ctl02_hlFriendTeam",
        "label": "odensala",
    },
    "2": {
        "name": "Long Street FC",
        "team_id": "1953833",
        "url": "https://www.xperteleven.com/players.aspx?dh=2&TeamID=1953833&Boost=1",
        "lobby_id": "#ctl00_cphMain_gvXpertTeams_ctl02_hlXpertTeam",
        "label": "longstreet",
    },
}

def login(page, team: dict):
    """Loggar in och navigerar till valt lags spelartrupp."""
    page.goto(LOGIN_URL)
    page.wait_for_load_state("networkidle")

    page.locator("#ctl00_cphMain_FrontControl_lwLogin_tbUsername").fill(USERNAME)
    page.locator("#ctl00_cphMain_FrontControl_lwLogin_tbPassword").fill(PASSWORD)
    page.locator("#ctl00_cphMain_FrontControl_lwLogin_btnLogin").click()
    page.wait_for_load_state("networkidle")
    print("✅ Inloggad!")

    # Välj lag på landningssidan
    page.locator(team["lobby_id"]).click()
    page.wait_for_load_state("networkidle")
    print(f"✅ Valde {team['name']}!")

    # Klicka på Spelartrupp i menyn
    page.locator("#ctl00_lblTeamMenuLinksSquad").click()
    page.wait_for_load_state("networkidle")
    print("✅ Navigerade till spelartruppen!")

def parse_condition(stat_td):
    img = stat_td.locator("img")
    if img.count() > 0:
        return img.get_attribute("title") or "Okänd"
    return "Okänd"


def parse_form(form_td):
    text = form_td.inner_text().strip()
    return text if text else "N/A"


def get_players(page) -> list[dict]:
    """Hämtar kondition & form för alla spelare i truppen."""
    players = []
    name_cells = page.locator("td.PlayerNameColl").all()

    for i, cell in enumerate(name_cells, start=0):  # Börjar på 0
        try:
            # Namn
            name_link = cell.locator("a")
            name = name_link.inner_text().strip() if name_link.count() > 0 else "Okänd"

            # PlayerID
            pid_div = cell.locator("div.PlayerId")
            player_id = pid_div.inner_text().strip() if pid_div.count() > 0 else "N/A"

            # Ålder — td direkt efter PlayerNameColl (nästa syskon-td)
            age_td = page.locator(f"td[id='player_td_skill_{i}']").locator("xpath=preceding-sibling::td[1]")
            age = age_td.inner_text().strip() if age_td.count() > 0 else "N/A"

            # Skill
            skill_panel = page.locator(f"#player_td_skill_{i} div.skillBarPanel")
            skill = skill_panel.get_attribute("title") if skill_panel.count() > 0 else "N/A"

            # UV
            uv_td = page.locator(f"#player_td_uv_{i}")
            uv = uv_td.inner_text().strip() if uv_td.count() > 0 else "N/A"

            # Form — två värden, övre (aktuell) och undre (medel)
            form_td = page.locator(f"#player_td_form_{i}")
            form_current_span = form_td.locator("tr:first-child span")
            form_average_span = form_td.locator("tr:last-child span")
            form_current = form_current_span.get_attribute("title") if form_current_span.count() > 0 else "N/A"
            form_average = form_average_span.get_attribute("title") if form_average_span.count() > 0 else "N/A"

            # Kondition
            stat_td = page.locator(f"#player_td_stat_{i}")
            condition = parse_condition(stat_td) if stat_td.count() > 0 else "N/A"

            players.append({
                "name":      name,
                "player_id": player_id.strip(),
                "age":       age,
                "skill":     skill,
                "uv":        uv,
                "form_current": form_current,
                "form_average": form_average,
                "condition": condition,
                "team":      TEAM_NAME,
                "timestamp": datetime.now().isoformat(),
                
            })

        except Exception as e:
            print(f"⚠️  Fel på spelare {i}: {e}")
            continue

    return players

def save_snapshot(players: list[dict], label: str = "snapshot"):
    """Sparar spelardata som JSON med tidsstämpel."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{label}_{ts}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(players, f, ensure_ascii=False, indent=2)
    print(f"💾 Snapshot sparad: {filename}")
    return filename

def format_condition(text: str, width: int = 35) -> list[str]:
    """Bryter lång konditionstext till flera rader."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 <= width:
            current = f"{current} {word}".strip()
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines if lines else [""]


def run():
    # Välj lag
    print("\nVälj lag:")
    for key, team in TEAMS.items():
        print(f"  {key}. {team['name']}")
    lag_val = input("Välj lag (1/2): ").strip()
    if lag_val not in TEAMS:
        print("⚠️ Ogiltigt val, använder Odensala Döders som standard")
        lag_val = "1"
    team = TEAMS[lag_val]

    # Välj före/efter
    label_map = {"f": "fore", "e": "efter"}
    label = input("Är detta en snapshot FÖRE eller EFTER match? (f/e): ").strip().lower()
    if label not in label_map:
        print("⚠️ Ogiltigt val, använder 'snapshot' som standard")
        label = "snapshot"
    else:
        label = f"{team['label']}_{label_map[label]}_match"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        login(page, team)
        players = get_players(page)

        # Tabellhuvud
        print(f"\n{'Namn':<30} | {'Ålder':<6} | {'Skill':<6} | {'UV':<5} | {'Form':<5} | {'MedelForm':<9} | Kondition")
        print("-" * 100)

        for player in players:
            cond_lines = format_condition(player['condition'])
            print(f"{player['name']:<30} | {player['age']:<6} | {player['skill']:<6} | {player['uv']:<5} | {player['form_current']:<5} | {player['form_average']:<9} | {cond_lines[0]}")
            for line in cond_lines[1:]:
                print(f"{'':30} | {'':6} | {'':6} | {'':5} | {'':5} | {'':9} | {line}")

        print(f"\nTotalt {len(players)} spelare — {team['name']}")
        save_snapshot(players, label=label)
        browser.close()

if __name__ == "__main__":
    run()