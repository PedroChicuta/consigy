from django.urls import path

from propostas import views

app_name = 'modalidades'

urlpatterns = [
    path('', views.ModalidadeListaView.as_view(), name='lista'),
    path('nova/', views.ModalidadeCriarView.as_view(), name='criar'),
    path('<int:pk>/editar/', views.ModalidadeEditarView.as_view(), name='editar'),
    path('<int:pk>/inativar/', views.ModalidadeInativarView.as_view(), name='inativar'),
    path('<int:pk>/reativar/', views.ModalidadeReativarView.as_view(), name='reativar'),
]
