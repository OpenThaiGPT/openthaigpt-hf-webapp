import os
from pathlib import Path


PAGE_DIR = Path(os.environ["PAGE_DIR"])

ROUTE_PREFIX = "/hft"
PAGE_LOGIN = ROUTE_PREFIX + "/public/login.html"
PAGE_EDITOR_ROUTE = ROUTE_PREFIX + "/page/editor"

PAGE_EDITOR_PATH = PAGE_DIR / "editor.html"
