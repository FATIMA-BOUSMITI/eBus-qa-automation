import json
import os
from pathlib import Path
from urllib.parse import urlsplit
import pytest
from playwright.sync_api import expect
from pages.app import EBusApp


@pytest.fixture(scope='session')
def browser_context_args(browser_context_args):
    return {**browser_context_args, 'viewport': {'width': 1280, 'height': 1000}, 'service_workers': 'block'}


@pytest.fixture
def app(page):
    """Real Flutter build + real QA API. Remap transport, never fake API bodies."""
    base = os.getenv('EBUS_UI_URL', 'http://host.docker.internal:17357')
    api = os.getenv('EBUS_API_URL', 'http://host.docker.internal:18080')
    if urlsplit(api).hostname not in {'host.docker.internal', 'localhost', '127.0.0.1'} or urlsplit(api).port != 18080:
        pytest.fail('BLOCKED: API must be the dedicated local QA target on port 18080')
    if urlsplit(base).hostname not in {'host.docker.internal', 'localhost', '127.0.0.1'}:
        pytest.fail('BLOCKED: authenticated E2E requires the local frontend; use inspection for deployed UI')

    # Fallback guard: no unrecognized host receives a write or login request.
    page.route('**/*', lambda route: route.continue_() if route.request.method in {'GET', 'HEAD', 'OPTIONS'} else route.abort('blockedbyclient'))

    def api_route(route):
        request = route.request
        path = urlsplit(request.url).path
        if request.method not in {'GET', 'HEAD', 'OPTIONS'} and not (request.method == 'POST' and path == '/users/login'):
            route.abort('blockedbyclient')
            return
        target = api + path
        query = urlsplit(request.url).query
        if query:
            target += '?' + query
        # Cross-origin response headers are rewritten only for the local browser transport.
        response = route.fetch(url=target, max_redirects=0, timeout=15000)
        route.fulfill(response=response, headers={**response.headers, 'access-control-allow-origin': '*'})

    page.route('https://ebus-backend-ao2u.onrender.com/**', api_route)
    # Firebase writes and external checkout are outside this read/navigation E2E suite.
    def firebase_route(route):
        if route.request.method not in {'GET', 'HEAD', 'OPTIONS'}:
            route.abort('blockedbyclient')
        else:
            route.continue_()
    page.route('**/*firebaseio.com/**', firebase_route)
    page.route('**/*stripe.com/**', lambda route: route.abort('blockedbyclient'))
    page.goto(base, wait_until='domcontentloaded', timeout=60000)
    placeholder = page.locator('flt-semantics-placeholder')
    placeholder.wait_for(state='attached', timeout=60000)
    placeholder.evaluate('(element)=>element.click()')
    expect(page.get_by_text('Bienvenue sur eBus', exact=False)).to_be_visible(timeout=90000)
    evidence = Path(__file__).resolve().parents[1] / 'reports/playwright/inspection'
    evidence.mkdir(parents=True, exist_ok=True)
    if not (evidence / 'local-login.json').exists():
        snapshot = {'target': base, 'semanticsEnabled': True,
                    'inputs': page.locator('input').evaluate_all('(items)=>items.map(e=>({type:e.type,role:e.getAttribute("role"),placeholder:e.placeholder}))')}
        (evidence / 'local-login.json').write_text(json.dumps(snapshot, indent=2))
        page.screenshot(path=str(evidence / 'local-login.png'), full_page=True)
    yield EBusApp(page)


def pytest_sessionfinish(session, exitstatus):
    terminal = session.config.pluginmanager.get_plugin('terminalreporter')
    stats = terminal.stats if terminal else {}
    report = {'kind': 'real-browser-local-e2e', 'exitStatus': exitstatus,
              'counts': {k: len(stats.get(k, [])) for k in ['passed', 'failed', 'skipped', 'error']}}
    output = Path(__file__).resolve().parents[1] / 'reports/playwright'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'summary.json').write_text(json.dumps(report, indent=2))
