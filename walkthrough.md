# Forensic Pipeline Walkthrough

## Overview
A Django-based forensic pipeline that allows users to upload media files, run various detection models, and receive an LLM-generated report.

## Components
- **Django App**: `web/forensic_pipeline`
- **Apps**: `accounts` (User management), `analysis` (Forensic logic)
- **Task Queue**: Celery + Redis
- **Models**: Integration with existing models in `models_data` via `analysis/utils.py`.

## functionality
1. **User Registration/Login**: Users can sign up and log in.
2. **Dashboard**: Users can upload files and select models.
3. **Processing**: Requests are queued in Redis and processed by Celery workers.
4. **Analysis**: 
    - Selected models are executed using `subprocess`.
    - Outputs (scores) and visual artifacts (masks, heatmaps) are captured.
5. **VLM Integration (New)**:
    - The `web/analysis/report_generators.py` script reads the output.
    - If models like `TruFor` generate masks, they are processed by the **local `Qwen3-VL` VLM** on the server.
    - The VLM visually analyzes the mask (e.g., "white square indicates deepfake") and adds its findings to the report.
6. **Reporting**:
    - `Qwen3-VL-4B-Instruct` aggregates numerical scores and visual analysis into a final verdict.
    - Users view the comprehensive report on the dashboard.
6. **Admin**: Admins can manage users and view all analysis results/logs.

## Usage

### 1. Setup Environment
Ensure you are in the `web` directory and the virtual environment is active.
```bash
cd web
source ../venv_django/bin/activate
pip install -r requirements.txt # (If not already installed)
```

### 2. Configure Environment Variables
Create a `.env` file in `web/` or set variables:
```bash
export DEEPSEEK_API_KEY="your_api_key_here"
# Optional: export FORENSICS_MODELS_PATH="/path/to/models"
```

### 3. Start Services
Use the provided script to start Redis, Celery, and Django:
```bash
chmod +x start.sh
./start.sh
```
Or manually:
```bash
redis-server --daemonize yes
celery -A forensic_pipeline worker -l info
python3 manage.py runserver
```

### 4. Access Application
- **Web Interface**: [http://localhost:8000](http://localhost:8000)
- **Admin Panel**: [http://localhost:8000/admin](http://localhost:8000/admin) (Login: `admin` / `admin`)

## Verification Steps
1. Register a new user at `/accounts/register/`.
2. Login.
3. Upload a test image/video.
4. Select `univfd` (or other models).
5. Submit.
6. Refresh dashboard until status is `COMPLETED` or `FAILED`.
7. Click "View" to see results.
