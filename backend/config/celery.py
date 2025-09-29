import os
from celery import Celery

# Устанавливаем переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Используем конфигурацию из настроек Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживаем задачи в файлах tasks.py приложений
app.autodiscover_tasks()