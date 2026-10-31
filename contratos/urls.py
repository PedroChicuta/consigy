from django.urls import path

from contratos import views

app_name = 'contratos'

urlpatterns = [
    path('', views.ListaView.as_view(), name='lista'),
    path('<int:pk>/', views.DetalheView.as_view(), name='detalhe'),
    path('<int:pk>/avancar/<str:status>/', views.AvancarView.as_view(), name='avancar'),
    path('<int:pk>/cancelar/', views.CancelarView.as_view(), name='cancelar'),
]
