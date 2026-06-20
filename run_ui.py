import os
import subprocess
import sys

if __name__ == "__main__":
    os.environ["PYTHONPATH"] = os.getcwd()

    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app/ui/main.py",
        ]
    )