# claviculario/admin.py

from django.contrib import admin
from .models import Local, Pessoa, Chave, Emprestimo
from .forms import PessoaForm

@admin.register(Pessoa)
class PessoaAdmin(admin.ModelAdmin):
    form = PessoaForm
    # Apenas para melhorar a visualização na lista de pessoas
    list_display = ('nome', 'empresa', 'cpf_saran')
    search_fields = ('nome', 'empresa', 'cpf_saran')
    
    # Define quais campos não devem aparecer na lista de edição
    # O campo 'pin' do modelo (o criptografado) não deve ser editado diretamente
    exclude = ('pin',)


@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    list_display = ('chave', 'pessoa', 'data_retirada', 'data_devolucao')
    list_filter = ('pessoa', 'chave')
    search_fields = ('chave__descricao', 'pessoa__nome')


admin.site.register(Local)
admin.site.register(Chave)