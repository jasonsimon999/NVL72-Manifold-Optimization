# Run in VS Code

## First-time setup (macOS)

1. Install Python 3.11 or later and the Microsoft Python extension in VS Code.
2. Choose **File → Open Folder** and open `Rack Manifold Optimization` (or your cloned `NVL72-Manifold-Optimization` folder). Open the folder containing `dashboard.py`, `requirements.txt`, and `run_app.py`.
3. Choose **Terminal → New Terminal**. Run these commands one at a time:

   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```

4. Press **Cmd+Shift+P**, choose **Python: Select Interpreter**, and select `.venv/bin/python` in this project. If it is absent, choose **Enter interpreter path** and browse to that file.
5. Start the app:

   ```sh
   python run_app.py
   ```

6. Open the **Local URL** printed in the terminal, normally `http://localhost:8501`. Leave the terminal running while using the dashboard. Stop it with **Ctrl+C**.

The launcher uses the selected Python interpreter, resolves the dashboard path automatically, and starts Streamlit. You do not need an editable package install, `PYTHONPATH`, or to move the scientific source files.

## Every subsequent session

Open the project folder in VS Code, open its terminal, and run:

```sh
source .venv/bin/activate
python run_app.py
```

Alternatively, after selecting the interpreter, open **Run and Debug**, select **Run manifold dashboard**, and press **F5**. Do not run `dashboard.py` with the ordinary **Run Python File** button; Streamlit needs its own runner. That button does work for `run_app.py`.

Windows: create the environment with `py -3 -m venv .venv`, activate with `.venv\Scripts\Activate.ps1` in PowerShell, and select `.venv\Scripts\python.exe`. If activation is restricted, use `.venv\Scripts\python.exe -m pip install -r requirements.txt` and `.venv\Scripts\python.exe run_app.py` directly.

## Publish on Streamlit Community Cloud

1. Commit and push the updated files to your GitHub repository, including `dashboard.py`, `requirements.txt`, `src/nvl72/`, `config/`, and `data/`. Do not upload `.venv`.
2. In Streamlit Community Cloud, select repository **jasonsimon999/NVL72-Manifold-Optimization**, the branch containing your changes (normally **main**), and main file **dashboard.py**. `run_app.py` is a local launcher, not the Cloud entrypoint.
3. In advanced settings choose **Python 3.11**, the version used for this project's tests, and deploy. For an existing app, update/reboot it after the corrected commit reaches its selected branch.
4. Cloud reads the root `requirements.txt`. Its `.` entry installs this repository's `nvl72-manifold` package (import name `nvl72`) into Cloud's Python environment. Keep this line: dashboard-only path setup does not cover every worker/cache import. The entrypoint additionally resolves its own `src` folder for local development. PyArrow is capped below 25 to match the Cloud safeguard in the supplied logs.
5. After this dependency fix is pushed, reboot the app to replace the running process and its caches. Check the build log for installation of `nvl72-manifold==0.1.1` or newer. The notice that both `requirements.txt` and `pyproject.toml` exist is expected: requirements selects the dependencies, and the `.` entry builds the model using pyproject metadata.

See Streamlit's [dependency guidance](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies) and [deployment instructions](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

## Files and troubleshooting

| Location | Purpose |
|---|---|
| `run_app.py` | Simple local startup |
| `dashboard.py` | Local and Cloud Streamlit entrypoint |
| `src/nvl72/` | Scientific model and reporting code |
| `config/` | Design and operating inputs |
| `data/` | Coolant properties and source records |
| `results/` | Saved studies and reports |
| `tests/` | Physics, deployment-import, and dashboard checks |

- **No module named streamlit/numpy/etc.:** select the project interpreter and rerun `python -m pip install -r requirements.txt`.
- **No module named nvl72 on Cloud:** verify the latest `dashboard.py` and complete `src/nvl72/` folder are committed to the deployed branch. The corrected entrypoint must contain the source-path bootstrap before its model imports.
- **Port occupied:** run `python run_app.py --server.port 8502` and use the printed URL.
- **Code changes:** save the file and click **Rerun** in Streamlit if it does not refresh automatically. Dashboard model edits load directly from `src`; no reinstall is needed.
- **Run tests:** `python -m pytest -q` from the project root.
- **Run scientific CLI studies:** install the package with `python -m pip install . --no-build-isolation --no-deps` before using `python -m nvl72 ...`; this installation is optional for the dashboard.
