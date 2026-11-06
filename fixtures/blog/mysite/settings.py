import os

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev")
DEBUG = True
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = ["django.contrib.admin", "django.contrib.auth", "blog"]
ROOT_URLCONF = "mysite.urls"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "blog"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
    }
}
