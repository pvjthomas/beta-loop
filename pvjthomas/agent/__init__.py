import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PVJ_ROOT = Path(__file__).resolve().parents[1]
for path in (REPO_ROOT, PVJ_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from . import agent
