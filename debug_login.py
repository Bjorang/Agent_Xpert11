from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://www.xperteleven.com")
    page.wait_for_load_state("networkidle")
    
    # Dumpa alla input-fält vi hittar
    inputs = page.locator("input").all()
    for inp in inputs:
        print(f"name={inp.get_attribute('name')} | type={inp.get_attribute('type')} | id={inp.get_attribute('id')}")
    
    browser.close()