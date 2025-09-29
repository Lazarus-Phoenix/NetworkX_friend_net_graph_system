from django.db import models
import uuid

class GraphTask(models.Model):
    """
    Модель для хранения информации о задаче по построению графа.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Статус задачи
    STATUS_CHOICES = (
        ('PENDING', 'В ожидании'),
        ('STARTED', 'Выполняется'),
        ('SUCCESS', 'Успешно'),
        ('FAILURE', 'Ошибка'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    # Путь к сгенерированному изображению графа
    result_image_path = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Задача {self.id} - {self.status}"
