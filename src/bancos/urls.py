from django.urls import path

from bancos import views

app_name = 'bancos'

urlpatterns = [
    path('', views.ListaView.as_view(), name='lista'),
    path('novo/', views.CriarView.as_view(), name='criar'),
    path('<int:pk>/editar/', views.EditarView.as_view(), name='editar'),
    path('<int:pk>/inativar/', views.InativarView.as_view(), name='inativar'),
    path('<int:pk>/reativar/', views.ReativarView.as_view(), name='reativar'),
]
