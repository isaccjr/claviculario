# claviculario_app/mixins.py

from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView

from .models import Pessoa, Chave, Local
from .forms import PessoaForm, ChaveForm, LocalForm

# ========================================================================
# MIXINS DE CONFIGURAÇÃO 
# ========================================================================
class BasePessoaView:
    model = Pessoa
    form_class = PessoaForm
    pagina_ativa = 'pessoas'

class BaseChaveView:
    model = Chave
    form_class = ChaveForm
    pagina_ativa = 'chaves'

class BaseLocalView:
    model = Local
    form_class = LocalForm
    pagina_ativa = 'locais'


# ========================================================================
# CLASSES BASE DE COMPORTAMENTO
# ========================================================================
class PaginaAtivaMixin:
    """ Adiciona a variável 'pagina_ativa' ao contexto. """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self, 'pagina_ativa'):
            context['pagina_ativa'] = self.pagina_ativa
        return context
    def get_info_genero(self):
        """ Retorna o artigo e a terminação com base no 'genero' do modelo. """
        # getattr busca o atributo 'genero' diretamente no modelo
        genero = getattr(self.model, 'genero', 'm') # <-- Procurando no self.model
        if genero == 'f':
            return {'artigo': 'A', 'final': 'a'}
        return {'artigo': 'O', 'final': 'o'}

class BaseListView(PaginaAtivaMixin, LoginRequiredMixin, PermissionRequiredMixin, ListView):
    paginate_by = 15
    def get_context_object_name(self, object_list):
        # Gera o nome da variável para o template
        nome_plural = self.model._meta.verbose_name_plural.lower().replace(" ", "_")
        return f'{nome_plural}_page'
    def get_permission_required(self):
        return (f'{self.model._meta.app_label}.view_{self.model._meta.model_name}',)
    def get_template_names(self):
        return [f'claviculario_app/{self.model._meta.model_name}_list.html']

class BaseCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, PaginaAtivaMixin, CreateView):
    title = ""
    success_message_template = "{artigo} {verbose_name} foi cadastrad{final} com sucesso!"
    def get_permission_required(self):
        return (f'{self.model._meta.app_label}.add_{self.model._meta.model_name}',)
    def get_success_url(self):
        return reverse_lazy(f'{self.model._meta.model_name}_list')
    def get_template_names(self):
        return [f'claviculario_app/{self.model._meta.model_name}_form.html']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context
    def form_valid(self, form):
        response = super().form_valid(form)
        info_genero = self.get_info_genero()
        
        success_message = self.success_message_template.format(
            **info_genero,
            verbose_name=self.model._meta.verbose_name
        )
        messages.success(self.request, success_message)
        return response

class BaseUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, PaginaAtivaMixin, UpdateView):
    title = ""
    success_message_template = "{artigo} {verbose_name} foi atualizad{final} com sucesso!"
    def get_permission_required(self):
        return (f'{self.model._meta.app_label}.change_{self.model._meta.model_name}',)
    def get_success_url(self):
        return reverse_lazy(f'{self.model._meta.model_name}_list')
    def get_template_names(self):
        return [f'claviculario_app/{self.model._meta.model_name}_form.html']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title.format(objeto=self.object)
        return context
    def form_valid(self, form):
        response = super().form_valid(form)
        info_genero = self.get_info_genero()
        
        success_message = self.success_message_template.format(
            **info_genero,
            verbose_name=self.model._meta.verbose_name
        )
        messages.success(self.request, success_message)
        return response

class BaseDesativarView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    fields = ['ativa']
    def get_permission_required(self):
        return (f'{self.model._meta.app_label}.delete_{self.model._meta.model_name}',)
    def get_success_url(self):
        return reverse_lazy(f'{self.model._meta.model_name}_list')
    def get_template_names(self):
        return [f'claviculario_app/{self.model._meta.model_name}_confirm_desativar.html']
    def form_valid(self, form):
        self.object.ativa = False
        self.object.save()
        messages.success(self.request, self.success_message.format(objeto=self.object))
        return redirect(self.get_success_url())
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self, 'pagina_ativa'):
            context['pagina_ativa'] = self.pagina_ativa
        return context
    def form_valid(self, form):
        self.object.ativa = False
        self.object.save()
        
        info_genero = self.get_info_genero()
        verbose_name = self.model._meta.verbose_name
        
        success_message = f"{info_genero['artigo']} {verbose_name} '{self.object}' foi desativad{info_genero['final']} com sucesso."
        messages.success(self.request, success_message)
        return redirect(self.get_success_url())
    