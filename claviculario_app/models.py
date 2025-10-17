# claviculario/models.py

from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import User

class Local(models.Model):
    genero = 'm'
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome do Local")
    ativa = models.BooleanField(default=True, verbose_name="Local ativo?")
    class Meta:
        verbose_name = "Local"
        verbose_name_plural = "Locais"
        ordering = ['nome'] # Dica extra!
    def __str__(self):
        return self.nome
    

class Pessoa(models.Model):
    genero = 'f'
    nome = models.CharField(max_length=200, verbose_name="Nome Completo")
    empresa = models.CharField(max_length=100, blank=True, null=True)
    cpf_saran = models.CharField(max_length=20, unique=True, verbose_name="CPF ou SARAN")
    pin = models.CharField(max_length=128, verbose_name="Pin de Confirmação")
    ativa = models.BooleanField(default=True, verbose_name="Pessoa ativa?")
    class Meta:
        verbose_name = "Pessoa"
        verbose_name_plural = "Pessoas"
        ordering = ['nome']
    def set_pin(self, raw_pin):
        self.pin = make_password(raw_pin)
    def check_pin(self, raw_pin):
        return check_password(raw_pin, self.pin)
    def __str__(self):
        return f"{self.nome} ({self.cpf_saran})"
    

class Chave(models.Model):
    genero = 'f'
    descricao = models.CharField(max_length=150, verbose_name="Descrição da Chave", unique=True)
    local = models.ForeignKey(Local, on_delete=models.PROTECT, related_name='chaves')
    disponivel = models.BooleanField(default=True)
    ativa = models.BooleanField(default=True, verbose_name="Chave ativa?")
    class Meta:
        verbose_name = "Chave"
        verbose_name_plural = "Chaves"
        ordering = ['descricao']
    def __str__(self):
        status = "Disponível" if self.disponivel else "Emprestada"
        return f"[{self.descricao}] - {self.local.nome} ({status})"

class Emprestimo(models.Model):
    genero = 'm'
    chave = models.ForeignKey(Chave, on_delete=models.PROTECT, related_name='emprestimos')
    pessoa = models.ForeignKey(Pessoa, on_delete=models.PROTECT, related_name='emprestimos')
    data_retirada = models.DateTimeField(verbose_name="Data e Hora da Retirada")
    previsao_devolucao = models.DateTimeField(verbose_name="Previsão de Devolução",
                                              null=True,
                                              blank=True)
    data_devolucao = models.DateTimeField(null=True, blank=True, verbose_name="Data e Hora da Devolução")
    observacao = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Empréstimo"
        verbose_name_plural = "Empréstimos"
        ordering = ['-data_retirada'] # Ordena pelos mais recentes primeiro
    def __str__(self):
        return f"{self.chave.descricao} para {self.pessoa.nome}"
    
class Unidade(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome da Unidade")
    # O 'owner' é o usuário criador e administrador principal da unidade
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="unidades_criadas")
    # Campo para o logo customizado
    logo = models.ImageField(upload_to='logos/', null=True, blank=True, verbose_name="Logo da Unidade")
    # Campo para o esquema de cores
    cor_tema = models.CharField(max_length=7, default="#0d6efd", verbose_name="Cor Principal do Tema") # Padrão azul
    # Relacionamento Many-to-Many para permitir que múltiplos usuários acessem a mesma unidade
    membros = models.ManyToManyField(User, related_name="unidades_membro", blank=True)

    class Meta:
        verbose_name = "Unidade"
        verbose_name_plural = "Unidades"

    def __str__(self):
        return self.nome