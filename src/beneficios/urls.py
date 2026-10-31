from django.urls import path

from beneficios import views

app_name = 'beneficios'

urlpatterns = [
    path('cliente/<int:cliente_pk>/novo/', views.CriarView.as_view(), name='criar'),
    path('<int:pk>/', views.DetalheView.as_view(), name='detalhe'),
    path('<int:pk>/margem/', views.RegistrarMargemView.as_view(), name='registrar_margem'),
    path('<int:pk>/inativar/', views.InativarView.as_view(), name='inativar'),
]
