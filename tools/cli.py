import argparse
import sys
import os
import json
import subprocess
from pathlib import Path

# Config
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Config
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Use env var if set, otherwise default to local 'models_data' or 'models'
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

def run_model(model_name, input_path, extra_args=[]):
    if model_name not in MODELS:
        print(f"Error: Unknown model '{model_name}'. Available: {list(MODELS.keys())}")
        return

    folder_name, script_name = MODELS[model_name]
    model_dir = MODELS_ROOT / folder_name
    script_path = model_dir / script_name
    venv_python = model_dir / ".venv" / "bin" / "python"

    if not model_dir.exists():
        print(f"Error: Model directory not found: {model_dir}")
        return
    
    if not venv_python.exists():
        print(f"Error: Virtual environment not found at {venv_python}. Run setup_envs.py first.")
        # Fallback to system python? No, unwise.
        return

    if not script_path.exists():
        print(f"Error: Runner script not implemented: {script_path}")
        print("Please implement the runner wrapper for this model.")
        return

    print(f"\n>>> Running {model_name} on {input_path}...")
    try:
        # Resolving input path to absolute because we change CWD
        abs_input_path = os.path.abspath(input_path)
        cmd = [str(venv_python), str(script_path), "--input", abs_input_path] + extra_args
        
        # Run inside the model directory so relative paths (like preprocessing/...) work
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            cwd=model_dir,
            bufsize=1,  # Line buffering
            universal_newlines=True
        )
        
        stdout_lines = []
        stderr_lines = []
        
        # Stream output and wait for completion
        stdout, stderr = process.communicate()
        
        if stdout:
            for line in stdout.split('\n'):
                if line.strip():
                    print(line)
                    stdout_lines.append(line.strip())
        
        if stderr:
            print(f"Stderr:\n{stderr}")
            stderr_lines.append(stderr)

        if process.returncode != 0:
            print(f"FAILED (Exit Code: {process.returncode})")
            stderr_str = "\n".join(stderr_lines)
            if stderr_str: print(f"Stderr:\n{stderr_str}") # Print again if missed
        else:
            print("SUCCESS.")
            try:
                # Try parsing last non-empty line as JSON
                non_empty = [l for l in stdout_lines if l.strip()]
                if non_empty:
                    parsed = json.loads(non_empty[-1])
                    print(f"Parsed Result: {json.dumps(parsed, indent=2)}")
            except json.JSONDecodeError:
                pass

    except Exception as e:
        print(f"Exception: {e}")

def main():
    parser = argparse.ArgumentParser(description="Forensics CLI Tester")
    parser.add_argument("model", help="Model name or 'all'", choices=list(MODELS.keys()) + ["all"])
    parser.add_argument("input", help="Path to input image/video/audio file")
    
    args, extras = parser.parse_known_args()
    
    # Pass extras to the runner
    # We need to modify run_model to accept extras
    
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    if args.model == "all":
        print("Running ALL models...")
        for m in MODELS:
            run_model(m, args.input, extras)
    else:
        run_model(args.model, args.input, extras)

if __name__ == "__main__":
    main()
