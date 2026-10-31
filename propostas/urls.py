from django.urls import path

from propostas import views

app_name = 'propostas'

urlpatterns = [
    path('', views.ListaView.as_view(), name='lista'),
    path('nova/', views.CriarView.as_view(), name='criar'),
    path('<int:pk>/', views.DetalheView.as_view(), name='detalhe'),
    path('<int:pk>/editar/', views.EditarView.as_view(), name='editar'),
    path('<int:pk>/observacoes/', views.EditarObservacoesView.as_view(), name='observacoes'),
]
