from django.urls import path

from propostas import views

app_name = 'propostas'

urlpatterns = [
    path('', views.ListaView.as_view(), name='lista'),
    path('nova/', views.CriarView.as_view(), name='criar'),
    path('beneficios/busca/', views.BuscarBeneficiosView.as_view(), name='buscar_beneficios'),
    path('beneficios/<int:pk>/card/', views.CardBeneficioView.as_view(), name='card_beneficio'),
    path(
        'beneficios/<int:pk>/margem/',
        views.RegistrarMargemInlineView.as_view(),
        name='registrar_margem_inline',
    ),
    path('<int:pk>/', views.DetalheView.as_view(), name='detalhe'),
    path('<int:pk>/editar/', views.EditarView.as_view(), name='editar'),
    path('<int:pk>/enviar/', views.EnviarView.as_view(), name='enviar'),
    path('<int:pk>/avancar/<str:status>/', views.AvancarView.as_view(), name='avancar'),
    path('<int:pk>/formalizar/', views.FormalizarView.as_view(), name='formalizar'),
    path('<int:pk>/recusar/', views.RecusarView.as_view(), name='recusar'),
    path('<int:pk>/cancelar/', views.CancelarView.as_view(), name='cancelar'),
    path('<int:pk>/observacoes/', views.EditarObservacoesView.as_view(), name='observacoes'),
]
