from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('task/<str:task_id>/', views.result_view, name='result'),
]
