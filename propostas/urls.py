from django.urls import path

from propostas import views

app_name = 'propostas'

urlpatterns = [
    path('', views.ListaView.as_view(), name='lista'),
    path('nova/', views.CriarView.as_view(), name='criar'),
    path('<int:pk>/', views.DetalheView.as_view(), name='detalhe'),
    path('<int:pk>/editar/', views.EditarView.as_view(), name='editar'),
    path('<int:pk>/enviar/', views.EnviarView.as_view(), name='enviar'),
    path('<int:pk>/avancar/<str:status>/', views.AvancarView.as_view(), name='avancar'),
    path('<int:pk>/formalizar/', views.FormalizarView.as_view(), name='formalizar'),
    path('<int:pk>/recusar/', views.RecusarView.as_view(), name='recusar'),
    path('<int:pk>/cancelar/', views.CancelarView.as_view(), name='cancelar'),
    path('<int:pk>/observacoes/', views.EditarObservacoesView.as_view(), name='observacoes'),
]
