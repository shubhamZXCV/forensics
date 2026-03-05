# Forensics Pipeline - Django Project Documentation

Welcome! This guide explains your Django project from the ground up, designed for developers new to Django.

---

## Table of Contents
1. [What is Django?](#what-is-django)
2. [Project Overview](#project-overview)
3. [Project Architecture](#project-architecture)
4. [Key Components](#key-components)
5. [Database Models](#database-models)
6. [How to Navigate the Code](#how-to-navigate-the-code)
7. [Setting Up & Running](#setting-up--running)
8. [Common Tasks](#common-tasks)
9. [Django Concepts Explained](#django-concepts-explained)
10. [Troubleshooting](#troubleshooting)

---

## What is Django?

Django is a **Python web framework** that helps you build web applications quickly. Think of it as a toolbox that provides:

- **Models**: Define how your data is structured (like a database schema)
- **Views**: Handle the logic (what happens when a user clicks a button)
- **Templates**: HTML pages that users see
- **URLs**: Map web addresses to views (e.g., `/dashboard/` → show dashboard)
- **Admin Interface**: Built-in admin panel to manage data
- **Forms**: Safely handle user input

**Key Principle**: Django follows the **MVT (Model-View-Template)** pattern:
```
User visits URL → URL Router → View Function → Query Database (Model) → Render Template (HTML) → Show to User
```

---

## Project Overview

### What Does This Project Do?

This is a **Forensic Pipeline Application** that:
1. Allows users to **upload images/videos**
2. Runs multiple **detection models** on the media
3. **Processes results** using Celery (background tasks)
4. **Generates an AI report** using an LLM (Large Language Model)
5. Shows results to users in a **dashboard**

### Tech Stack

- **Web Framework**: Django 5.2.11
- **Database**: SQLite (stores users, requests, results)
- **Task Queue**: Celery (for running models in background)
- **Message Broker**: Redis (manages task queue)
- **AI Integration**: OpenAI API (for report generation)
- **Python Version**: 3.11+

---

## Project Architecture

```
forensics_shubham/
│
├── web/                              # Main Django project
│   ├── forensic_pipeline/            # Project settings & config
│   │   ├── settings.py               # Main configuration
│   │   ├── urls.py                   # Main URL router
│   │   ├── celery.py                 # Celery configuration
│   │   ├── wsgi.py                   # Web server config
│   │   └── asgi.py                   # Async server config
│   │
│   ├── accounts/                     # User management app
│   │   ├── models.py                 # User model
│   │   ├── views.py                  # User views (login, register)
│   │   ├── urls.py                   # User URLs
│   │   ├── forms.py                  # User forms
│   │   └── migrations/               # Database changes
│   │
│   ├── analysis/                     # Main analysis app
│   │   ├── models.py                 # ForensicRequest, AnalysisResult
│   │   ├── views.py                  # Dashboard, detail views
│   │   ├── urls.py                   # Analysis URLs
│   │   ├── forms.py                  # File upload form
│   │   ├── tasks.py                  # Celery background tasks
│   │   ├── utils.py                  # Helper functions
│   │   ├── report_generators.py      # LLM report generation
│   │   ├── prompts.py                # LLM prompts
│   │   └── migrations/               # Database changes
│   │
│   ├── templates/                    # HTML files
│   │   ├── base.html                 # Base template (used by all pages)
│   │   ├── analysis/
│   │   │   ├── dashboard.html        # Main dashboard
│   │   │   └── detail.html           # Request details page
│   │   ├── accounts/
│   │   │   ├── register.html         # User registration
│   │   │   └── admin_dashboard.html  # Admin dashboard
│   │   └── registration/
│   │       └── login.html            # Login page
│   │
│   ├── static/                       # CSS, JavaScript, images
│   │   └── css/
│   │
│   ├── media/                        # Uploaded files (user uploads)
│   │   └── uploads/
│   │
│   ├── manage.py                     # Django command runner
│   ├── db.sqlite3                    # Local database file
│   └── start.sh                      # Script to start all services
│
├── models_data/                      # ML models for forensics
│   ├── stage1_bfree/
│   ├── stage1_cnndetection/
│   ├── stage1_rine/
│   ├── stage1_univfd/
│   ├── stage2_trufor/
│   ├── stage3_d3/
│   ├── stage3_deepfakebench/
│   ├── stage3_genconvit/
│   ├── stage4_aasist/
│   ├── stage4_rawnet/
│   └── stage5_rtm/
│
├── tools/                            # Utility scripts
│   └── cli.py
│
└── venv_django/                      # Python virtual environment
    └── (installed packages)
```

---

## Key Components

### 1. **Accounts App** (User Management)

**Files**: `web/accounts/`

- **Purpose**: Handle user registration, login, and authentication
- **Key Files**:
  - `models.py`: Defines `CustomUser` model (extends Django's built-in User)
  - `views.py`: Register and admin dashboard views
  - `urls.py`: Maps URLs like `/accounts/register/` to views
  - `forms.py`: User creation form

**What Happens**:
```
User visits /accounts/register/ 
→ View returns registration form
→ User fills form and submits
→ New user created and saved to database
→ User can now log in
```

### 2. **Analysis App** (Main Forensics Logic)

**Files**: `web/analysis/`

- **Purpose**: Handle file uploads, model execution, report generation
- **Key Files**:
  - `models.py`: `ForensicRequest` and `AnalysisResult` models
  - `views.py`: Dashboard and detail views
  - `tasks.py`: **Celery tasks** (runs in background)
  - `utils.py`: Helper functions (subprocess calls to ML models)
  - `report_generators.py`: LLM integration for report generation
  - `urls.py`: Routes URLs to views
  - `forms.py`: File upload form

**What Happens**:
```
1. User logs in → sees Dashboard (analysis/views.py: dashboard view)
2. User uploads file + selects models → form submitted
3. Django saves ForensicRequest to database
4. Celery task triggered (analysis/tasks.py: process_forensic_request)
5. Background worker runs models using subprocess
6. Results saved as AnalysisResult objects
7. LLM generates report
8. User views details (analysis/views.py: request_detail view)
```

### 3. **Templates** (Frontend/HTML)

**Files**: `web/templates/`

- **Purpose**: Display web pages to users
- **Key Templates**:
  - `base.html`: Base template (header, navigation - used by all pages)
  - `analysis/dashboard.html`: Shows upload form and previous requests
  - `analysis/detail.html`: Shows analysis results
  - `accounts/login.html`: Login page
  - `accounts/register.html`: Registration page

**How Templates Work**:
```
View passes data to template → Template loops through data → HTML rendered → Sent to browser
```

### 4. **Static Files** (CSS, JavaScript)

**Files**: `web/static/`

- CSS files for styling
- JavaScript for interactivity
- Images and other assets

---

## Database Models

Django uses **Models** to define database tables. Here's what the database looks like:

### Model: `CustomUser` (accounts/models.py)

**Table**: `accounts_customuser`

```
CustomUser (extends Django's built-in User)
├── id (auto-generated primary key)
├── username (unique)
├── email
├── password (encrypted)
├── is_admin (optional field for admins)
└── Other built-in fields (first_name, last_name, date_joined, etc.)
```

### Model: `ForensicRequest` (analysis/models.py)

**Table**: `analysis_forensicrequest`

Represents a user's request to analyze a file.

```
ForensicRequest
├── id (primary key)
├── user (ForeignKey to CustomUser)  ← Links to user who made request
├── input_file (FileField)           ← The uploaded file
├── media_type (CharField)           ← 'image' or 'video'
├── selected_models (JSONField)      ← List of model names ["univfd", "trufor"]
├── status (CharField)               ← 'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'
├── report_content (TextField)       ← Final LLM report
└── created_at (DateTimeField)       ← When created
```

**Example**:
```
ForensicRequest #42
├── user: "john_doe"
├── input_file: "/uploads/2026/03/03/image.jpg"
├── media_type: "image"
├── selected_models: ["univfd", "trufor"]
├── status: "COMPLETED"
└── report_content: "This appears to be manipulated based on..."
```

### Model: `AnalysisResult` (analysis/models.py)

**Table**: `analysis_analysisresult`

Represents individual model output for a request.

```
AnalysisResult
├── id (primary key)
├── request (ForeignKey to ForensicRequest)  ← Links to parent request
├── model_name (CharField)                   ← Which model ran (e.g., "univfd")
├── status (CharField)                       ← 'SUCCESS' or 'FAILED'
├── output_json (JSONField)                  ← Model output (scores, etc.)
├── logs (TextField)                         ← Error logs if failed
└── completed_at (DateTimeField)             ← When completed
```

**Example**:
```
AnalysisResult #1
├── request: ForensicRequest #42
├── model_name: "univfd"
├── status: "SUCCESS"
└── output_json: {"confidence": 0.85, "prediction": "manipulated"}
```

---

## How to Navigate the Code

### Understanding a User Action

Let's trace what happens when a user **uploads a file**:

#### Step 1: User visits Dashboard
- **URL**: `http://localhost:8000/`
- **File**: `web/analysis/urls.py`
  ```python
  path('', views.dashboard, name='dashboard')
  ```
  This says: "When user visits `/`, call the `dashboard` view"

#### Step 2: View Handles Request
- **File**: `web/analysis/views.py`
  ```python
  @login_required  # Only logged-in users
  def dashboard(request):
      if request.method == 'POST':  # Form submitted
          form = ForensicRequestForm(request.POST, request.FILES)
          if form.is_valid():
              forensic_req = form.save(commit=False)
              forensic_req.user = request.user
              forensic_req.save()  # Save to database
              
              # Trigger background task
              process_forensic_request.delay(forensic_req.id)
              
              return redirect('dashboard')
      else:  # Just showing the form (GET request)
          form = ForensicRequestForm()
      
      return render(request, 'analysis/dashboard.html', {'form': form})
  ```

  **What's happening**:
  - `@login_required`: Only allows logged-in users
  - If `POST` (form submitted): Save to database, trigger task
  - If `GET` (just visiting): Show empty form

#### Step 3: Form Definition
- **File**: `web/analysis/forms.py`
  - Defines what fields the form has (file upload, model selection, etc.)

#### Step 4: Template Renders HTML
- **File**: `web/templates/analysis/dashboard.html`
  - Shows the form to user using Django template syntax

#### Step 5: Celery Task Runs in Background
- **File**: `web/analysis/tasks.py`
  ```python
  @shared_task
  def process_forensic_request(request_id):
      # Run models, generate report
      req.status = 'PROCESSING'
      # ... run each model ...
      req.status = 'COMPLETED'
  ```

---

## Setting Up & Running

### 1. **Activate Virtual Environment**

```bash
cd /home/nutrition/forensics_shubham/web
source ../venv_django/bin/activate
```

You'll see `(venv_django)` in your terminal if active.

### 2. **Install Dependencies** (First Time Only)

```bash
pip install -r requirements.txt
```

### 3. **Set Environment Variables**

Create `.env` file in `web/` folder:
```bash
cd /home/nutrition/forensics_shubham/web
echo 'DEEPSEEK_API_KEY="your_key_here"' > .env
```

### 4. **Create Database Tables** (First Time Only)

Django uses **migrations** to create/modify database tables:

```bash
python manage.py migrate
```

This runs all pending migrations. You'll see output like:
```
Operations to perform:
  Apply all migrations: admin, auth, analysis, accounts, ...
Running migrations:
  Applying accounts.0001_initial... OK
  Applying analysis.0001_initial... OK
  ...
```

### 5. **Create Admin User** (First Time Only)

```bash
python manage.py createsuperuser
```

Follow prompts:
```
Username: admin
Email: admin@example.com
Password: (your password)
```

### 6. **Start Services**

**Option A: Using the provided script**
```bash
chmod +x start.sh
./start.sh
```

**Option B: Manually start each service**

Terminal 1 - Redis:
```bash
redis-server --daemonize yes
```

Terminal 2 - Celery Worker:
```bash
celery -A forensic_pipeline worker -l info
```

Terminal 3 - Django Development Server:
```bash
python manage.py runserver
```

### 7. **Access the Application**

- **User Dashboard**: http://localhost:8000/
- **Admin Panel**: http://localhost:8000/admin/ (username: admin, password: your_password)
- **Registration**: http://localhost:8000/accounts/register/

---

## Common Tasks

### Creating a New Django App

```bash
python manage.py startapp myapp
```

This creates a new folder with models, views, urls, etc.

### Running Database Migrations

After modifying `models.py`:

```bash
# Step 1: Create migration file
python manage.py makemigrations

# Step 2: Apply migration to database
python manage.py migrate
```

### Creating a Superuser

```bash
python manage.py createsuperuser
```

### Checking Database Queries

```bash
python manage.py shell
```

Then in Python:
```python
from analysis.models import ForensicRequest
requests = ForensicRequest.objects.all()
for req in requests:
    print(req.user.username, req.status)
```

### Collecting Static Files (Production)

```bash
python manage.py collectstatic
```

### Running Tests

```bash
python manage.py test
```

### Creating a Fixture (Test Data)

```bash
python manage.py dumpdata analysis > analysis_data.json
python manage.py loaddata analysis_data.json
```

---

## Django Concepts Explained

### URLs & Routing

Django maps URLs to views using `urlpatterns`:

**File**: `web/forensic_pipeline/urls.py`
```python
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),           # /admin/ → admin interface
    path('accounts/', include('accounts.urls')), # /accounts/* → accounts app
    path('', include('analysis.urls')),         # /* → analysis app
]
```

**File**: `web/analysis/urls.py`
```python
urlpatterns = [
    path('', views.dashboard, name='dashboard'),  # / → dashboard view
    path('request/<int:pk>/', views.request_detail, name='request_detail'),  # /request/42/ → detail view
]
```

### Models & Database

Models = Python classes that represent database tables.

```python
class ForensicRequest(models.Model):
    user = models.ForeignKey(...)  # Link to User model
    status = models.CharField(...)  # Text field
    created_at = models.DateTimeField(auto_now_add=True)  # Auto-set to now

    def __str__(self):
        return f"Request {self.id}"
```

When you run `migrate`, Django creates the SQL table automatically.

### Views

Views are Python functions that handle requests and return responses:

```python
def dashboard(request):
    # request = HTTP request object
    # Do something with request data
    return render(request, 'template.html', {'data': data})
```

**Types of responses**:
- `render()`: Return HTML page
- `redirect()`: Redirect to another URL
- `JsonResponse()`: Return JSON data
- `HttpResponse()`: Return plain text

### Templates

Templates are HTML files with Django template syntax:

```html
<h1>Welcome, {{ user.username }}!</h1>

{% if request.status == 'COMPLETED' %}
    <p>Your analysis is done!</p>
{% else %}
    <p>Still processing...</p>
{% endif %}

{% for result in request.results.all %}
    <p>{{ result.model_name }}: {{ result.status }}</p>
{% endfor %}
```

### Forms

Forms validate user input and create HTML form elements:

```python
from django import forms
from .models import ForensicRequest

class ForensicRequestForm(forms.ModelForm):
    class Meta:
        model = ForensicRequest
        fields = ['input_file', 'media_type', 'selected_models']
```

In template:
```html
<form method="post" enctype="multipart/form-data">
    {% csrf_token %}  <!-- Security token -->
    {{ form.as_p }}   <!-- Render all form fields -->
    <button type="submit">Upload</button>
</form>
```

### Celery (Background Tasks)

Celery runs tasks asynchronously (in background), so long operations don't block the user:

```python
from celery import shared_task

@shared_task
def process_forensic_request(request_id):
    # This runs in a separate worker process
    # User gets immediate response, task runs in background
    pass
```

**Flow**:
```
1. User submits form (takes 1 second)
2. Django creates ForensicRequest in database
3. Django queues Celery task in Redis
4. Celery worker picks up task
5. Worker runs models (might take 10 minutes)
6. User can check status anytime
```

---

## Troubleshooting

### "No such table" Error

**Problem**: `django.db.utils.OperationalError: no such table: analysis_forensicrequest`

**Solution**:
```bash
python manage.py migrate
```

### Can't log in

**Problem**: Login page says invalid credentials

**Solution**: Make sure you have a superuser created:
```bash
python manage.py createsuperuser
```

### Celery tasks not running

**Problem**: Tasks stay in PENDING status forever

**Solution**: Make sure Redis and Celery worker are running:
```bash
redis-server --daemonize yes
celery -A forensic_pipeline worker -l info
```

### File upload not working

**Problem**: Upload form says "invalid" or file doesn't save

**Solution**: Check folder permissions:
```bash
chmod -R 755 /home/nutrition/forensics_shubham/web/media/
```

### Static files not showing (CSS, images)

**Problem**: CSS/images don't load

**Solution** (Development):
- Make sure debug=True in settings.py
- Restart Django server

**Solution** (Production):
```bash
python manage.py collectstatic
```

### "csrf_token missing" Error

**Problem**: Form submission fails with CSRF error

**Solution**: Make sure form includes CSRF token:
```html
<form method="post">
    {% csrf_token %}  <!-- Add this line -->
    {{ form }}
    <button>Submit</button>
</form>
```

### Database file locked

**Problem**: `database is locked` error

**Solution**: Stop all Django/Celery processes and restart:
```bash
pkill -f "python manage.py"
pkill -f celery
```

---

## File Modification Guide

### To Add a New Model

1. **Edit** `web/analysis/models.py`:
```python
class NewModel(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
```

2. **Create migration**:
```bash
python manage.py makemigrations
```

3. **Apply migration**:
```bash
python manage.py migrate
```

4. **Register in admin** (optional):
```python
# web/analysis/admin.py
from .models import NewModel
admin.site.register(NewModel)
```

### To Add a New Page

1. **Add URL** in `web/analysis/urls.py`:
```python
path('new-page/', views.new_page, name='new_page')
```

2. **Add View** in `web/analysis/views.py`:
```python
def new_page(request):
    data = {"message": "Hello"}
    return render(request, 'analysis/new_page.html', data)
```

3. **Create Template** `web/templates/analysis/new_page.html`:
```html
{% extends "base.html" %}

{% block content %}
    <h1>{{ message }}</h1>
{% endblock %}
```

### To Add a Background Task

1. **Add task** in `web/analysis/tasks.py`:
```python
from celery import shared_task

@shared_task
def my_task(data):
    # Do something
    return {"result": "Done"}
```

2. **Call from view** in `web/analysis/views.py`:
```python
from .tasks import my_task

my_task.delay(data)  # Runs in background
```

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `manage.py` | Django command runner |
| `forensic_pipeline/settings.py` | Project configuration |
| `forensic_pipeline/urls.py` | Main URL router |
| `analysis/models.py` | Database models |
| `analysis/views.py` | Request handlers |
| `analysis/urls.py` | Analysis app URLs |
| `analysis/tasks.py` | Background tasks |
| `accounts/models.py` | User model |
| `accounts/views.py` | Auth views |
| `templates/` | HTML files |
| `static/` | CSS, JS, images |
| `media/` | User uploads |
| `db.sqlite3` | Database file |

---

## Next Steps

1. **Run the project**: Follow "Setting Up & Running" section
2. **Explore Admin Panel**: http://localhost:8000/admin/
3. **Upload a test file**: Use the dashboard
4. **Check Celery logs**: Watch background task execution
5. **Examine code**: Start with `analysis/views.py` and `analysis/tasks.py`
6. **Modify something**: Try changing a template or adding a field to a model

---

## Useful Django Resources

- **Official Django Docs**: https://docs.djangoproject.com/
- **Django for Beginners**: https://djangoforbeginners.com/
- **Models Guide**: https://docs.djangoproject.com/en/5.2/topics/db/models/
- **Views Guide**: https://docs.djangoproject.com/en/5.2/topics/http/views/
- **Templates Guide**: https://docs.djangoproject.com/en/5.2/topics/templates/

---

## Summary

Your Django project is organized as:
- **accounts** app handles user management
- **analysis** app handles file uploads and model execution
- **Celery** runs background tasks (model inference)
- **Templates** render HTML pages
- **Models** define database structure

The main workflow is: User → Upload → Celery Task → LLM Report → Dashboard

Good luck exploring your codebase! 🚀
