from django.shortcuts import render, redirect
from django.urls import reverse
from .tasks import create_friend_graph_task
from .models import GraphTask
from celery.result import AsyncResult


def index_view(request):
    """
    Отображает главную страницу и запускает задачу по построению графа.
    """
    if request.method == 'POST':
        # Запускаем нашу Celery задачу.
        # В реальном приложении сюда нужно передать ID пользователя VK или токен.
        task = create_friend_graph_task.delay(1)  # Передаем условный user_id = 1
        # Перенаправляем на страницу результата с ID задачи
        return redirect(reverse('result', kwargs={'task_id': task.id}))

    return render(request, 'core/index.html')


def result_view(request, task_id):
    """
    Отображает статус задачи и результат (граф).
    """
    task_result = AsyncResult(task_id)
    graph_task = GraphTask.objects.filter(id=task_id).first()

    context = {
        'task_id': task_id,
        'task_status': task_result.status,
        'graph_task': graph_task,
    }

    # Если задача выполнена, добавляем путь к изображению в контекст
    if task_result.successful() and graph_task:
        context['image_url'] = graph_task.result_image_path

    return render(request, 'core/success.html', context)
