import sys
from pathlib import Path

# Prefer the mounted source tree over the copy installed into site-packages.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
