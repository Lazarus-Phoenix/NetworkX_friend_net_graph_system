import networkx as nx
import matplotlib

matplotlib.use('Agg')  # Используем бэкенд, который не требует GUI
import matplotlib.pyplot as plt
import random
import string
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


# --- КОНЕЦ БЛОКА ИМИТАЦИИ ---


@shared_task(bind=True)
def create_friend_graph_task(self, user_id):
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

        # 4. Находим сообщества (кластеры)
        # Алгоритм может быть долгим, для больших графов лучше использовать более быстрые
        # Например, `nx.community.louvain_communities(G)`
        try:
            communities_generator = community.girvan_newman(G)
            top_level_communities = next(communities_generator)
            node_to_community = {node: i for i, comm in enumerate(top_level_communities) for node in comm}
            colors = [node_to_community.get(node, 0) for node in G.nodes()]
            cmap = plt.cm.jet
        except (nx.NetworkXError, StopIteration):
            # Если сообщества не найдены, используем один цвет
            colors = 'blue'
            cmap = None

        # 5. Визуализируем граф
        plt.figure(figsize=(24, 24))
        pos = nx.spring_layout(G, k=0.6, iterations=50)
        sizes = [5000 if node == user_id else 500 for node in G.nodes()]

        nx.draw_networkx_nodes(G, pos, node_size=sizes, node_color=colors, cmap=cmap, alpha=0.9)
        nx.draw_networkx_edges(G, pos, alpha=0.2)

        plt.title(f"Граф друзей для пользователя {user_id}", size=20)
        plt.axis('off')

        # 6. Сохраняем изображение
        filename = f"graph_{task_id}.png"
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        filepath = os.path.join(settings.MEDIA_ROOT, filename)
        plt.savefig(filepath)
        plt.close()

        # 7. Обновляем запись в БД
        task_record.status = 'SUCCESS'
        task_record.result_image_path = os.path.join(settings.MEDIA_URL, filename)
        task_record.save()

        return {'status': 'Success', 'image_path': task_record.result_image_path}

    except Exception as e:
        task_record.status = 'FAILURE'
        task_record.save()
        print(f"Ошибка в задаче {task_id}: {e}")  # Логирование ошибки
        return {'status': 'Failure', 'error': str(e)}

