"""Cloud-style startup must use checkout code, not an installed local model."""
from pathlib import Path
import subprocess
import sys

def test_dashboard_from_outside_checkout(tmp_path):
    root=Path(__file__).resolve().parents[1]
    script=r'''
import sys
from pathlib import Path
from streamlit.testing.v1 import AppTest
root=Path(sys.argv[1])
assert 'nvl72' not in sys.modules
app=AppTest.from_file(str(root/'dashboard.py'),default_timeout=45).run()
assert not app.exception, str(app.exception)
import nvl72
assert Path(nvl72.__file__).resolve().is_relative_to(root/'src')
app.sidebar.selectbox[1].set_value('in_row').run()
assert not app.exception, str(app.exception)
next(b for b in app.button if b.label=='Show saved optimized result').click().run()
assert not app.exception, str(app.exception)
assert any(x.value=='Saved optimized candidate' for x in app.subheader)
'''
    # -I ignores PYTHONPATH and the current directory. This catches accidental
    # dependence on pytest's pythonpath configuration or a stale installed model.
    result=subprocess.run([sys.executable,'-I','-c',script,str(root)],cwd=tmp_path,
                          capture_output=True,text=True,timeout=120)
    assert result.returncode==0,result.stdout+result.stderr
