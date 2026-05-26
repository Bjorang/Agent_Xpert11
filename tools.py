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


def login(page):
    """Loggar in på Xperteleven."""
    page.goto(LOGIN_URL)
    page.wait_for_load_state("networkidle")

    page.locator("#ctl00_cphMain_FrontControl_lwLogin_tbUsername").fill(USERNAME)
    page.locator("#ctl00_cphMain_FrontControl_lwLogin_tbPassword").fill(PASSWORD)
    page.locator("#ctl00_cphMain_FrontControl_lwLogin_btnLogin").click()

    page.wait_for_load_state("networkidle")
    print("✅ Inloggad!")

 # Välj Odensala Döders på landningssidan
    page.locator("#ctl00_cphMain_gvFriendsTeam_ctl02_hlFriendTeam").click()
    page.wait_for_load_state("networkidle")
    print("✅ Valde Odensala Döders!")

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

            # Form — hämta title-attributet från span inuti tdSpecial
            form_td = page.locator(f"#player_td_form_{i}")
            form_span = form_td.locator("tr:first-child span")
            form = form_span.get_attribute("title") if form_span.count() > 0 else "N/A"

            # Kondition
            stat_td = page.locator(f"#player_td_stat_{i}")
            condition = parse_condition(stat_td) if stat_td.count() > 0 else "N/A"

            players.append({
                "name":      name,
                "player_id": player_id.strip(),
                "age":       age,
                "skill":     skill,
                "uv":        uv,
                "form":      form,
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
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        login(page)
        
        # Debug Kittichai och ålder
        print("DEBUG - player_td_uv_16:", page.locator("#player_td_uv_16").count())
        print("DEBUG - player_td_stat_16:", page.locator("#player_td_stat_16").count())
        print("DEBUG - player_td_uv_15:", page.locator("#player_td_uv_15").count())
        print("DEBUG - player_td_age_1:", page.locator("#player_td_age_1").count())

        players = get_players(page)

        # Tabellhuvud
        print(f"\n{'Namn':<30} | {'Ålder':<6} | {'Skill':<6} | {'UV':<5} | {'Form':<5} | Kondition")
        print("-" * 90)

        for player in players:
            cond_lines = format_condition(player['condition'])
            print(f"{player['name']:<30} | {player['age']:<6} | {player['skill']:<6} | {player['uv']:<5} | {player['form']:<5} | {cond_lines[0]}")
            for line in cond_lines[1:]:
                print(f"{'':30} | {'':6} | {'':6} | {'':5} | {'':5} | {line}")

        print(f"\nTotalt {len(players)} spelare")
        save_snapshot(players, label="odensala_doeders")
        browser.close()

if __name__ == "__main__":
    run()