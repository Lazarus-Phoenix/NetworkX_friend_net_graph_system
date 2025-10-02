import networkx as nx
import random
import json
import uuid
import requests  # Для отправки сообщений в VK
import os
from celery import shared_task
from django.conf import settings
from .models import GraphTask
from networkx.algorithms import community


# --- БЛОК ИМИТАЦИИ VK API ---
# В реальном проекте этот блок нужно заменить на настоящие вызовы к VK API.

def mock_vk_api_get_friends(user_id):
    """Имитирует получение списка друзей."""
    return list(range(1, random.randint(50, 150)))  # Возвращаем ID "друзей"


def mock_vk_api_are_friends(user1_id, user2_id):
    """Имитирует проверку дружбы между двумя пользователями."""
    return random.random() < 0.1  # 10% шанс, что они друзья


def send_vk_message_with_file(user_vk_id, message_text, file_path):
    """
    Имитирует отправку сообщения с файлом пользователю VK.
    В реальном проекте здесь будет логика загрузки файла на сервер VK
    и отправки сообщения через API.
    """
    # 1. Загрузить файл на сервер VK (метод `docs.getMessagesUploadServer`, `docs.save`)
    # 2. Отправить сообщение с вложением (метод `messages.send`)
    print(f"--- ИМИТАЦИЯ ОТПРАВКИ В VK ---")
    print(f"Кому: {user_vk_id}")
    print(f"Текст: {message_text}")
    print(f"Файл: {file_path}")
    print(f"-----------------------------")
    # В реальном коде здесь будет вызов requests.post(...) к VK API
    return True

# --- КОНЕЦ БЛОКА ИМИТАЦИИ ---


@shared_task(bind=True)
def create_friend_graph_task(self, user_id, user_vk_id):
    """
    Задача Celery для создания и визуализации графа друзей.
    """
    task_id = self.request.id
    task_record, _ = GraphTask.objects.get_or_create(id=task_id)
    task_record.status = 'STARTED'
    task_record.save()

    try:
        # 1. Создаем граф
        G = nx.Graph()
        G.add_node(user_id)  # Добавляем центрального пользователя

        # 2. Получаем друзей 1-го круга (используем заглушку)
        friends_lvl1 = mock_vk_api_get_friends(user_id)
        for friend in friends_lvl1:
            G.add_edge(user_id, friend)

        # 3. Находим связи между друзьями 1-го круга
        for i in range(len(friends_lvl1)):
            for j in range(i + 1, len(friends_lvl1)):
                # Проверяем, дружат ли они (используем заглушку)
                if mock_vk_api_are_friends(friends_lvl1[i], friends_lvl1[j]):
                    G.add_edge(friends_lvl1[i], friends_lvl1[j])

        # 4. Генерируем структуру для Obsidian Canvas
        canvas_data = {"nodes": [], "edges": []}
        pos = nx.spring_layout(G, k=0.8, iterations=50) # Позиции для Canvas

        for i, node_id in enumerate(G.nodes()):
            node_text = f"User {node_id}"
            if node_id == user_id:
                node_text = f"Вы (ID: {node_id})"
            
            canvas_data["nodes"].append({
                "id": str(node_id),
                "x": pos[node_id][0] * 1000, # Масштабируем для Canvas
                "y": pos[node_id][1] * 1000,
                "width": 200,
                "height": 40,
                "type": "text",
                "text": node_text
            })

        for i, edge in enumerate(G.edges()):
            canvas_data["edges"].append({
                "id": str(uuid.uuid4()),
                "fromNode": str(edge[0]),
                "toNode": str(edge[1]),
            })

        # 5. Сохраняем .canvas файл
        filename = f"graph_{task_id}.canvas"
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        filepath = os.path.join(settings.MEDIA_ROOT, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(canvas_data, f, ensure_ascii=False, indent=4)

        # 6. Отправляем сообщение пользователю
        message = f"Ваш граф друзей готов! Откройте прикрепленный файл в Obsidian, чтобы увидеть результат."
        send_vk_message_with_file(user_vk_id, message, filepath)

        # 7. Обновляем запись в БД
        task_record.status = 'SUCCESS'
        # Можно сохранить путь к файлу, если он нужен для чего-то еще
        task_record.result_image_path = os.path.join(settings.MEDIA_URL, filename) 
        task_record.save()

        return {'status': 'Success', 'message': f'Result sent to VK user {user_vk_id}'}

    except Exception as e:
        task_record.status = 'FAILURE'
        task_record.save()
        print(f"Ошибка в задаче {task_id}: {e}")  # Логирование ошибки
        return {'status': 'Failure', 'error': str(e)}
