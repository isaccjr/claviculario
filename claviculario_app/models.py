# claviculario/models.py

from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

class Local(models.Model):
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome do Local")
    ativa = models.BooleanField(default=True, verbose_name="Local ativo?")
    def __str__(self):
        return self.nome

class Pessoa(models.Model):
    nome = models.CharField(max_length=200, verbose_name="Nome Completo")
    empresa = models.CharField(max_length=100, blank=True, null=True)
    cpf_saran = models.CharField(max_length=20, unique=True, verbose_name="CPF ou SARAN")
    pin = models.CharField(max_length=128, verbose_name="Pin de Confirmação")
    ativa = models.BooleanField(default=True, verbose_name="Pessoa ativa?")
    def set_pin(self, raw_pin):
        self.pin = make_password(raw_pin)
    def check_pin(self, raw_pin):
        return check_password(raw_pin, self.pin)
    def __str__(self):
        return f"{self.nome} ({self.cpf_saran})"

class Chave(models.Model):
    descricao = models.CharField(max_length=150, verbose_name="Descrição da Chave", unique=True)
    local = models.ForeignKey(Local, on_delete=models.PROTECT, related_name='chaves')
    disponivel = models.BooleanField(default=True)
    ativa = models.BooleanField(default=True, verbose_name="Chave ativa?")
    def __str__(self):
        status = "Disponível" if self.disponivel else "Emprestada"
        return f"[{self.descricao}] - {self.local.nome} ({status})"

class Emprestimo(models.Model):
    chave = models.ForeignKey(Chave, on_delete=models.PROTECT, related_name='emprestimos')
    pessoa = models.ForeignKey(Pessoa, on_delete=models.PROTECT, related_name='emprestimos')
    data_retirada = models.DateTimeField(verbose_name="Data e Hora da Retirada")
    previsao_devolucao = models.DateTimeField(verbose_name="Previsão de Devolução",
                                              null=True,
                                              blank=True)
    data_devolucao = models.DateTimeField(null=True, blank=True, verbose_name="Data e Hora da Devolução")
    observacao = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.chave.descricao} para {self.pessoa.nome}"