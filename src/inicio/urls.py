from django.urls import path

from . import views

app_name = 'inicio'

urlpatterns = [
    path('', views.index, name='index'),
    path('busca-clientes/', views.buscar_clientes, name='buscar_clientes'),
    path('fila-propostas/', views.fila_propostas, name='fila_propostas'),
]
