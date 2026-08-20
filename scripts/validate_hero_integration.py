"""Static validation for the Baak Books Hero integration.

Checks the HTML contract and parses every inline JavaScript block with Node.
This does not modify the application or contact Firestore.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path('/home/ubuntu/baakbook-local/frontend')


def extract_scripts(path: Path) -> list[str]:
    soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
    return [node.string or node.get_text() for node in soup.find_all('script') if not node.get('src')]


def assert_contains(path: Path, selectors: list[str]) -> None:
    text = path.read_text(encoding='utf-8')
    missing = [selector for selector in selectors if selector not in text]
    if missing:
        raise AssertionError(f'{path.name} missing: {missing}')


def main() -> None:
    index = ROOT / 'index.html'
    admin = ROOT / 'admin.html'
    assert_contains(index, [
        'id="storefrontHero"', 'id="heroSlider"', 'id="heroSlides"',
        'id="heroPrev"', 'id="heroNext"', 'id="heroDots"',
        'function normalizeHeroConfig', 'function renderHero',
        'function startHeroAutoplay', "addEventListener('pointerdown'",
    ])
    assert_contains(admin, [
        'data-tab="hero"', 'id="panel-hero"', 'id="heroAdminVisible"',
        'id="heroAdminAutoplay"', 'id="heroAdminInterval"',
        'id="heroAdminDots"', 'id="heroAdminArrows"',
        'id="heroAdminHeight"', 'id="heroSlidesList"',
        'id="addHeroSlideBtn"', 'id="saveHeroBtn"',
        'function renderHeroEditor', 'function collectHeroEditor',
    ])

    checked = []
    with tempfile.TemporaryDirectory(prefix='baakbook-js-check-') as directory:
        directory_path = Path(directory)
        for html in (index, admin):
            for number, script in enumerate(extract_scripts(html), start=1):
                if not script.strip():
                    continue
                script_path = directory_path / f'{html.stem}-{number}.js'
                script_path.write_text(script, encoding='utf-8')
                result = subprocess.run(
                    ['node', '--check', str(script_path)],
                    capture_output=True,
                    text=True,
                )
                if result.returncode:
                    raise AssertionError(
                        f'JavaScript syntax error in {html.name} block {number}:\n{result.stderr}'
                    )
                checked.append(f'{html.name} block {number}')

    result = {
        'status': 'passed',
        'checked_scripts': checked,
        'index_contract': 'passed',
        'admin_contract': 'passed',
        'firestore_touched': False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
