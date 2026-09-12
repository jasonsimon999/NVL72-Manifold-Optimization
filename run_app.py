"""Start the dashboard with this Python interpreter: python run_app.py."""
from pathlib import Path
import subprocess
import sys
from importlib.util import find_spec

def main():
    root = Path(__file__).resolve().parent
    if find_spec('streamlit') is None:
        print('Install dependencies first: python -m pip install -r requirements.txt', file=sys.stderr)
        return 1
    try:
        return subprocess.call([sys.executable, '-m', 'streamlit', 'run',
                                str(root / 'dashboard.py'), *sys.argv[1:]], cwd=root)
    except KeyboardInterrupt:
        return 0

if __name__ == '__main__':
    raise SystemExit(main())
