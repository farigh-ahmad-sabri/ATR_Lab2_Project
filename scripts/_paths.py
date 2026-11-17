"""Make `src/` importable when scripts are run as `python scripts/<name>.py`."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
