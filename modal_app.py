"""Deploy only from a cloud runner. No local model downloads."""
import os
import subprocess
import sys

import modal

UPSTREAM_COMMIT = "7fe6b7665f8bf035998f401f8cb779fbe53f2751"
MODEL_REVISION = "8d6e83bcd3701a76fc27a764965665da1df7da78"
app = modal.App("haru-ja-free")
weights = modal.Volume.from_name("haru-ja-weights", create_if_missing=True)
image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "libsndfile1", "ffmpeg")
    .run_commands(
        "git clone https://github.com/higurashi-ai/Haru.git /opt/Haru",
        f"git -C /opt/Haru checkout {UPSTREAM_COMMIT}",
        "python -m pip install /opt/Haru/haru",
    )
    .env({
        "HF_HOME": "/models/hf",
        "HF_HUB_DISABLE_TELEMETRY": "1",
        "HARU_MODEL_REVISION": MODEL_REVISION,
        "PYTHONDONTWRITEBYTECODE": "1",
        "TRITON_CACHE_DIR": "/models/triton",
        "TORCHINDUCTOR_CACHE_DIR": "/models/torchinductor",
    })
    .add_local_file("protected_haru.py", "/opt/protected_haru.py")
)
password = os.environ.get("HARU_PASSWORD", "")
if modal.is_local() and len(password) < 32:
    raise RuntimeError("A fresh private HARU_PASSWORD is required for deployment.")
credentials = modal.Secret.from_dict({"HARU_PASSWORD": password}) if modal.is_local() else modal.Secret.from_dict({})

@app.function(
    image=image,
    gpu=["L4", "A10", "L40S"],
    cpu=2,
    memory=16384,
    min_containers=0,
    max_containers=1,
    scaledown_window=10,
    timeout=900,
    startup_timeout=900,
    volumes={"/models": weights},
    secrets=[credentials],
)
@modal.concurrent(max_inputs=20)
@modal.web_server(8000, startup_timeout=900)
def web():
    import base64
    import json
    import time
    import urllib.request
    import urllib.error
    process = subprocess.Popen([sys.executable, "/opt/protected_haru.py"])
    header = "Basic " + base64.b64encode(("haru:" + os.environ["HARU_PASSWORD"]).encode()).decode()
    deadline = time.monotonic() + 840
    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("Haru server exited during initialization")
            try:
                request = urllib.request.Request("http://127.0.0.1:8000/api/ready",
                    headers={"Authorization": header})
                with urllib.request.urlopen(request, timeout=5) as response:
                    ready = json.load(response).get("ready", False)
                if ready:
                    weights.commit()
                    print("Haru model ready; weights and GPU kernel cache committed.", flush=True)
                    return
            except (urllib.error.URLError, TimeoutError):
                pass
            time.sleep(1)
        raise TimeoutError("Haru model initialization did not complete")
    except BaseException:
        process.terminate()
        raise
