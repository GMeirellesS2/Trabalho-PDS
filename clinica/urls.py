from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'), # O caminho vazio '' significa a página inicial
]