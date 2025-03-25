from django.contrib.auth.models import User
from django.db.utils import IntegrityError

try:
    superuser = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpassword'
    )
    print(f"Superuser '{superuser.username}' created successfully!")
except IntegrityError:
    print("Superuser already exists.")