# claviculario_app/forms.py

from django import forms
from .models import Emprestimo, Chave, Pessoa, Local
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm, UserChangeForm


#FORMULÁRIO PARA CRIAR E EDITAR EMPRESTIMOS 
class EmprestimoForm(forms.ModelForm):
    data_retirada = forms.DateTimeField(
        initial=timezone.now,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label="Data e Hora da Retirada"
    )
    class Meta:
        model = Emprestimo
        fields = ['chave', 'pessoa', 'data_retirada', 'previsao_devolucao','observacao']
        widgets = {
            'chave': forms.Select(attrs={'class': 'form-select'}),
            'pessoa': forms.Select(attrs={'class': 'form-select'}),
            'previsao_devolucao': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['chave'].queryset = Chave.objects.filter(disponivel=True, ativa=True).order_by('descricao')
        self.fields['pessoa'].queryset = Pessoa.objects.all().order_by('nome')

#FORMULÁRIO PARA CRIAR E EDITAR CHAVES
class ChaveForm(forms.ModelForm):
    class Meta:
        model = Chave
        fields = ['descricao', 'local']
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'local': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'descricao': 'Descrição da Chave',
            'local': 'Local da Chave',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ADICIONA O FILTRO: O dropdown de 'local' agora só mostra locais ativos.
        self.fields['local'].queryset = Local.objects.filter(ativa=True).order_by('nome')
    
    # Validação para garantir que a descrição da chave seja única
    def clean_descricao(self):
        descricao = self.cleaned_data.get('descricao')
        if self.instance and self.instance.pk:
            # Editando: verifica se outra chave já tem essa descrição
            if Chave.objects.filter(descricao=descricao).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Já existe uma chave com esta descrição.")
        else:
            # Criando: verifica se qualquer chave já tem essa descrição
            if Chave.objects.filter(descricao=descricao).exists():
                raise forms.ValidationError("Já existe uma chave com esta descrição.")
        return descricao


#FORMULÁRIO PARA O RELATÓRIO
class RelatorioForm(forms.Form):
    data_inicio = forms.DateField(
        label="De",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    data_fim = forms.DateField(
        label="Até",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    # CAMPO: Filtro por Pessoa
    pessoa = forms.ModelChoiceField(
        queryset=Pessoa.objects.all().order_by('nome'),
        required=False,
        label="Pessoa",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # CAMPO: Filtro por Chave
    chave = forms.ModelChoiceField(
        queryset=Chave.objects.all().order_by('descricao'),
        required=False,
        label="Chave",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    STATUS_CHOICES = (
        ("todos", "Todos"),
        ("pendentes", "Pendentes (Sem Devolução)"),
    )
    status = forms.ChoiceField(
        label="Status",
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

#FORMULÁRIO PARA CADASTRO DE PESSOAS
class PessoaForm(forms.ModelForm):
    pin = forms.CharField(
        label="PIN (4 a 6 dígitos)",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=4,
        max_length=6
    )
    confirmar_pin = forms.CharField(
        label="Confirmar PIN",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    class Meta:
        model = Pessoa
        fields = ['nome', 'empresa', 'cpf_saran']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'empresa': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: FAB, Empresa Terceirizada'}),
            'cpf_saran': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apenas números'}),
        }
        labels = {
            'nome': 'Nome Completo',
            'cpf_saran': 'CPF ou SARAN',
        }

    def clean_cpf_saran(self):
        # Pega o CPF/SARAN do formulário que o usuário enviou
        cpf_saran = self.cleaned_data.get('cpf_saran')
        
        # self.instance é o objeto Pessoa que está sendo editado.
        # Ao criar uma nova pessoa, self.instance não terá um 'pk' (id).
        # Ao editar, ele terá.
        if self.instance and self.instance.pk:
            # Estamos editando. Vamos procurar por pessoas com o mesmo CPF/SARAN,
            # mas EXCLUINDO a própria pessoa que estamos editando da busca.
            if Pessoa.objects.filter(cpf_saran=cpf_saran).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Este CPF ou SARAN já está cadastrado para outra pessoa.")
        else:
            # Estamos criando uma nova pessoa. A lógica antiga funciona.
            if Pessoa.objects.filter(cpf_saran=cpf_saran).exists():
                raise forms.ValidationError("Este CPF ou SARAN já está cadastrado.")
                
        return cpf_saran
    
    # Validação para garantir que os PINs digitados são iguais
    def clean(self):
        cleaned_data = super().clean()
        pin = cleaned_data.get("pin")
        confirmar_pin = cleaned_data.get("confirmar_pin")

        if pin and confirmar_pin and pin != confirmar_pin:
            self.add_error('confirmar_pin', "Os PINs não coincidem.")
    
    # Sobrescrevemos o método save para usar nosso 'set_pin'
    def save(self, commit=True):
        # Pega a instância da pessoa, mas não salva ainda (commit=False)
        pessoa = super().save(commit=False)
        # Usa nosso método seguro para definir o PIN
        pessoa.set_pin(self.cleaned_data["pin"])
        if commit:
            pessoa.save()
        return pessoa

#FORMULÁRIO PARA CRIAR E EDITAR LOCAIS
class LocalForm(forms.ModelForm):
    class Meta:
        model = Local
        fields = ['nome']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'nome': 'Nome do Local',
        }

    # Validação para garantir que o nome do local seja único
    def clean_nome(self):
        nome = self.cleaned_data.get('nome')
        if self.instance and self.instance.pk:
            if Local.objects.filter(nome=nome).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Já existe um local com este nome.")
        else:
            if Local.objects.filter(nome=nome).exists():
                raise forms.ValidationError("Já existe um local com este nome.")
        return nome
    
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ("email",)


# claviculario_app/forms.py

class CustomUserCreationForm(UserCreationForm):
    """ Formulário para criar um novo usuário. """
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

class CustomUserChangeForm(forms.ModelForm):
    """ Formulário para editar um usuário e suas permissões (grupos). """
    # O campo 'groups' permite a seleção múltipla dos grupos disponíveis.
    grupos = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Funções (Grupos)"
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'is_active', 'grupos')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se o formulário for para um usuário existente, preenchemos o campo 'grupos'
        # com os grupos aos quais ele já pertence.
        if self.instance.pk:
            self.fields['grupos'].initial = self.instance.groups.all()

    def save(self, commit=True):
        # A lógica de salvar é customizada: primeiro salvamos o usuário,
        # depois atualizamos a relação com os grupos.
        user = super().save(commit=False)
        if commit:
            user.save()
            # O .set() limpa os grupos antigos e adiciona os novos selecionados.
            user.groups.set(self.cleaned_data['grupos'])
            self.save_m2m() # Necessário para salvar relações ManyToMany
        return user