"""Separate page; homepage layout and fixed optimization remain intact."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT/'src') not in sys.path:sys.path.insert(0,str(ROOT/'src'))
from nvl72.dynamic.ui import render
render(ROOT)
