# claviculario_app/admin.py

from django.contrib import admin
from .models import Unidade, Local, Pessoa, Chave, Emprestimo
from .forms import PessoaForm

@admin.register(Unidade)
class UnidadeAdmin(admin.ModelAdmin):
    """
    Configuração de como o modelo 'Unidade' aparece no painel de admin.
    """
    list_display = ('nome', 'owner', 'cor_tema')
    search_fields = ('nome', 'owner__username')
    list_filter = ('owner',)
    # O campo 'membros' é um ManyToManyField, melhor editado com um widget horizontal
    filter_horizontal = ('membros',)

@admin.register(Local)
class LocalAdmin(admin.ModelAdmin):
    """
    Configuração de como o modelo 'Local' aparece no painel de admin.
    """
    list_display = ('nome', 'ativa')
    search_fields = ('nome',)
    list_filter = ('ativa',)

@admin.register(Chave)
class ChaveAdmin(admin.ModelAdmin):
    """
    Configuração de como o modelo 'Chave' aparece no painel de admin.
    """
    list_display = ('descricao', 'local', 'disponivel', 'ativa')
    search_fields = ('descricao', 'local__nome')
    list_filter = ('ativa', 'disponivel', 'local')
    # Organiza os campos no formulário de edição
    fieldsets = (
        (None, {
            'fields': ('descricao', 'local')
        }),
        ('Status', {
            'fields': ('disponivel', 'ativa')
        }),
    )

@admin.register(Pessoa)
class PessoaAdmin(admin.ModelAdmin):
    """
    Configuração de como o modelo 'Pessoa' aparece no painel de admin.
    Usa o PessoaForm customizado para garantir a criptografia do PIN.
    """
    form = PessoaForm
    list_display = ('nome', 'empresa', 'cpf_saran', 'ativa')
    search_fields = ('nome', 'empresa', 'cpf_saran')
    list_filter = ('ativa', 'empresa')
    # O campo 'pin' (criptografado) não deve ser editado diretamente
    exclude = ('pin',)

@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    """
    Configuração de como o modelo 'Emprestimo' aparece no painel de admin.
    """
    list_display = ('chave', 'pessoa', 'data_retirada', 'previsao_devolucao', 'data_devolucao')
    list_filter = ('pessoa', 'chave')
    search_fields = ('chave__descricao', 'pessoa__nome')
    # Torna os campos de data apenas leitura, pois são gerenciados pelo sistema
    readonly_fields = ('data_retirada', 'data_devolucao')