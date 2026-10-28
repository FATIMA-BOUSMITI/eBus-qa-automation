"""Inspect the real public Flutter UI before choosing selectors. No login performed."""
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

output = Path(__file__).resolve().parents[1] / 'reports/playwright/inspection'
output.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(channel=os.getenv('EBUS_BROWSER_CHANNEL') or None, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1280, 'height': 900})
    if os.getenv('EBUS_INSPECT_API_URL'):
        api = os.environ['EBUS_INSPECT_API_URL']
        if urlsplit(api).hostname not in {'127.0.0.1', 'localhost', 'host.docker.internal'} or urlsplit(api).port != 18080:
            raise RuntimeError('Only dedicated local QA API remapping is allowed')
        def read_api(route):
            if route.request.method not in {'GET','HEAD','OPTIONS'}:
                route.abort('blockedbyclient')
                return
            parsed = urlsplit(route.request.url)
            response = route.fetch(url=api + parsed.path + ('?' + parsed.query if parsed.query else ''), max_redirects=0)
            route.fulfill(response=response, headers={**response.headers, 'access-control-allow-origin':'*'})
        page.route('https://ebus-backend-ao2u.onrender.com/**', read_api)
    page.goto(os.getenv('EBUS_INSPECT_UI_URL', 'https://ebus-frontend-1an4.onrender.com/'), wait_until='domcontentloaded', timeout=90000)
    placeholder = page.locator('flt-semantics-placeholder')
    placeholder.wait_for(state='attached', timeout=90000)
    placeholder.evaluate('(element) => element.click()')
    page.get_by_text('Bienvenue sur eBus', exact=False).wait_for(timeout=150000)
    page.screenshot(path=str(output / 'login.png'), full_page=True)
    snapshot = {'title': page.title(), 'bodyText': page.locator('body').inner_text(),
                'inputs': page.locator('input').evaluate_all('(items)=>items.map(e=>({type:e.type,placeholder:e.placeholder,role:e.getAttribute("role"),label:e.getAttribute("aria-label")}))'),
                'semantics': page.locator('flt-semantics').evaluate_all('(items)=>items.map(e=>({role:e.getAttribute("role"),label:e.getAttribute("aria-label"),text:e.innerText})).filter(e=>e.role||e.label||e.text)')}
    (output / 'login.json').write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(snapshot, ensure_ascii=False))
    browser.close()
