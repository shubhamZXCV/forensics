import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forensic_pipeline.settings')
django.setup()

User = get_user_model()
username = 'admin'
password = 'admin@123'
email = 'admin@example.com'

if not User.objects.filter(username=username).exists():
    print(f"Creating superuser '{username}'...")
    User.objects.create_superuser(username=username, email=email, password=password)
    print("Superuser created successfully.")
else:
    print(f"Superuser '{username}' already exists. Updating password...")
    user = User.objects.get(username=username)
    user.set_password(password)
    user.save()
    print("Superuser password updated.")
