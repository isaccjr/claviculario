# claviculario_app/urls.py

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # --- Autenticação ---
    
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
     # ROTA DE REGISTRO
    
    # ROTAS PARA GESTÃO DE CONTAS
    path('contas/', views.UserListView.as_view(), name='user_list'),
    path('contas/criar/', views.UserCreateView.as_view(), name='user_create'),
    path('contas/<int:pk>/editar/', views.UserUpdateView.as_view(), name='user_update'),
    path('contas/<int:pk>/desativar/', views.UserDesativarView.as_view(), name='user_desativar'),
    # --- Rota Principal (Homepage) ---
    # Apenas UMA rota para o caminho vazio (''). Agora ela aponta para a dashboard.
    path('', views.dashboard, name='dashboard'),
    
    # --- Páginas de pessoas
    path('pessoas/', views.PessoaListView.as_view(), name='pessoa_list'),
    path('pessoas/nova/', views.PessoaCreateView.as_view(), name='pessoa_create'),
    path('pessoas/<int:pk>/editar/', views.PessoaUpdateView.as_view(), name='pessoa_update'),
    path('pessoas/<int:pk>/desativar/', views.PessoaDesativarView.as_view(), name='pessoa_desativar'),
    path('pessoas/<int:pk>/historico/', views.pessoa_historico, name='pessoa_historico'),

    #Páginas de chaves
    path('chaves/', views.ChaveListView.as_view(), name='chave_list'),
    path('chaves/nova/', views.ChaveCreateView.as_view(), name='chave_create'),
    path('chaves/<int:pk>/editar/', views.ChaveUpdateView.as_view(), name='chave_update'),
    path('chaves/<int:pk>/desativar/', views.ChaveDesativarView.as_view(), name='chave_desativar'),
    path('chaves/<int:pk>/historico/', views.chave_historico, name='chave_historico'),

    #Página de locais
    path('locais/', views.LocalListView.as_view(), name='local_list'),
    path('locais/novo/', views.LocalCreateView.as_view(), name='local_create'),
    path('locais/<int:pk>/editar/', views.LocalUpdateView.as_view(), name='local_update'),
    path('locais/<int:pk>/desativar/', views.LocalDesativarView.as_view(), name='local_desativar'),

    #Página de emprestimos e relatório de emprestimos 
    path('retirada/', views.view_retirada, name='view_retirada'),
    path('devolucao/', views.view_devolucao, name='view_devolucao'),
    path('emprestimo/<int:emprestimo_id>/devolver/', views.registrar_devolucao, name='registrar_devolucao'),
    path('relatorio/', views.view_relatorio, name='view_relatorio'),
    
    # --- Funcionalidades (APIs) ---
    path('pessoa/cadastrar/', views.cadastrar_pessoa, name='cadastrar_pessoa'),
    path('api/pessoas/', views.filtrar_pessoas, name='filtrar_pessoas'),
    path('retirada/verificar/', views.verificar_pin_e_registrar, name='verificar_pin_e_registrar'),
     path('api/chaves/', views.filtrar_chaves_por_local, name='filtrar_chaves_por_local'),

    # --- Exportações
    path('relatorio/exportar/csv/', views.exportar_relatorio_csv, name='exportar_relatorio_csv'),
    path('relatorio/exportar/excel/', views.exportar_relatorio_excel, name='exportar_relatorio_excel'),

     # --- Importação
    path('importar/', views.importar_dados_page, name='importar_dados_page'),
    path('importar/template-pessoas/', views.download_template_pessoas, name='download_template_pessoas'),
    path('importar/template-chaves/', views.download_template_chaves, name='download_template_chaves'),
    
    # ---PROCESSAR OS UPLOADS
    path('importar/processar-pessoas/', views.importar_pessoas, name='importar_pessoas'),
    path('importar/processar-chaves/', views.importar_chaves, name='importar_chaves'),

    path('analise/', views.analytics_page, name='analytics_page'),
    # --- API PARA ANALISE DOS DADOS
    path('api/analytics-data/', views.analytics_data, name='analytics_data'),


]