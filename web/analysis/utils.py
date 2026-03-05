import os
import json
import subprocess
from pathlib import Path

# Config
# web/analysis/utils.py -> web/analysis -> web -> forensics_shubham
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
# Use env var if set, otherwise default to local 'models_data'
env_models = os.getenv("FORENSICS_MODELS_PATH")
MODELS_ROOT = Path(env_models) if env_models else (PROJECT_ROOT / "models_data")

MODELS = {
    # Stage 1
    "univfd": ("stage1_univfd", "runner.py"),
    "rine": ("stage1_rine", "runner.py"),
    "bfree": ("stage1_bfree", "runner.py"),
    "cnndetection": ("stage1_cnndetection", "runner.py"),
    # Stage 2
    "trufor": ("stage2_trufor", "runner.py"),
    # Stage 3
    "deepfakebench": ("stage3_deepfakebench", "runner.py"),
    "d3": ("stage3_d3", "runner.py"),
    "genconvit": ("stage3_genconvit", "runner.py"),
    # Stage 4
    "rawnet": ("stage4_rawnet", "runner.py"),
    "aasist": ("stage4_aasist", "runner.py"),
    # Stage 5
    "rtm": ("stage5_rtm", "runner.py"),
    "edgedoc": ("stage5_edgedoc", "runner.py"),
}

# Models restricted to admin users only
RESTRICTED_MODELS = {"rawnet", "aasist", "rtm", "edgedoc"}

def get_available_models(is_admin=False):
    """Get available models. Non-admin users get filtered list."""
    all_models = list(MODELS.keys())
    if is_admin:
        return all_models
    return [m for m in all_models if m not in RESTRICTED_MODELS]

def run_model_wrapper(model_name, input_path):
    """
    Runs a forensic model and returns (success, output_json, logs).
    """
    if model_name not in MODELS:
        return False, None, f"Error: Unknown model '{model_name}'"

    folder_name, script_name = MODELS[model_name]
    model_dir = MODELS_ROOT / folder_name
    script_path = model_dir / script_name
    venv_python = model_dir / ".venv" / "bin" / "python"

    if not model_dir.exists():
        return False, None, f"Error: Model directory not found: {model_dir}"
    
    if not venv_python.exists():
        return False, None, f"Error: Virtual environment not found at {venv_python}. Run setup_envs.py first."

    if not script_path.exists():
        return False, None, f"Error: Runner script not implemented: {script_path}"

    try:
        abs_input_path = os.path.abspath(input_path)
        cmd = [str(venv_python), str(script_path), "--input", abs_input_path]
        
        # Run inside the model directory
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            cwd=model_dir,
            universal_newlines=True
        )
        
        stdout, stderr = process.communicate()
        
        logs = f"Stdout:\n{stdout}\n\nStderr:\n{stderr}"
        
        parsed_result = None
        if process.returncode == 0:
            # Try parsing last non-empty line as JSON
            stdout_lines = stdout.split('\n')
            non_empty = [l for l in stdout_lines if l.strip()]
            if non_empty:
                try:
                    parsed_result = json.loads(non_empty[-1])
                except json.JSONDecodeError:
                    pass
            return True, parsed_result, logs
        else:
            return False, None, logs

    except Exception as e:
        return False, None, f"Exception: {str(e)}"
