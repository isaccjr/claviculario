# claviculario_app/views.py
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Emprestimo, Chave, Pessoa, Local
from .forms import EmprestimoForm, RelatorioForm, PessoaForm, ChaveForm, LocalForm
from datetime import timedelta
from django.contrib.auth.decorators import login_required, permission_required

# Para as exportações
import csv
from django.http import HttpResponse
from openpyxl import Workbook

from .mixins import BaseCreateView,BaseDesativarView,BaseListView,BaseUpdateView
from .mixins import BasePessoaView,BaseChaveView,BaseLocalView

@login_required
def view_retirada(request):
    if request.method == 'POST':
        form = EmprestimoForm(request.POST)
        if form.is_valid():
            chave_selecionada = form.cleaned_data['chave']
            if not chave_selecionada.disponivel:
                messages.error(request, 'Esta chave já foi emprestada. Por favor, selecione outra.')
                return redirect('view_retirada')
            form.save()
            chave_selecionada.disponivel = False
            chave_selecionada.save()
            messages.success(request, f'Chave "{chave_selecionada.descricao}" emprestada com sucesso!')
            return redirect('view_retirada')
    else:
        form = EmprestimoForm()

    emprestimos_ativos = Emprestimo.objects.filter(data_devolucao__isnull=True).order_by('-data_retirada')
    form_pessoa = PessoaForm()
    locais = Local.objects.all().order_by('nome')
    contexto = {
        'form': form,
        'form_pessoa' : form_pessoa,
        'emprestimos_ativos': emprestimos_ativos,
        'locais' : locais,
        'pagina_ativa': 'retirada' # Para o menu lateral
    }
    return render(request, 'claviculario_app/retirada.html', contexto)

# NOVA VIEW PARA A PÁGINA DE DEVOLUÇÃO
@login_required
def view_devolucao(request):
    emprestimos_ativos = Emprestimo.objects.filter(data_devolucao__isnull=True).order_by('chave__descricao')
    
    # Filtra as chaves e pessoas que têm empréstimos ativos
    chaves_emprestadas = Chave.objects.filter(id__in=emprestimos_ativos.values_list('chave_id', flat=True)).distinct()
    pessoas_com_chave = Pessoa.objects.filter(id__in=emprestimos_ativos.values_list('pessoa_id', flat=True)).distinct()

    # Lógica para filtros GET
    chave_id_filtrada = request.GET.get('chave')
    pessoa_id_filtrada = request.GET.get('pessoa')

    if chave_id_filtrada:
        emprestimos_ativos = emprestimos_ativos.filter(chave_id=chave_id_filtrada)
    
    if pessoa_id_filtrada:
        emprestimos_ativos = emprestimos_ativos.filter(pessoa_id=pessoa_id_filtrada)

    contexto = {
        'emprestimos': emprestimos_ativos,
        'chaves_emprestadas': chaves_emprestadas,
        'pessoas_com_chave': pessoas_com_chave,
        'pagina_ativa': 'devolucao' # Para o menu lateral
    }
    return render(request, 'claviculario_app/devolucao.html', contexto)

def paginador(request,lista:list,quant_por_pag:int = 15) :
    # Cria um Paginator com a nossa lista , mostrando n itens por página
    paginator = Paginator(lista, quant_por_pag)
    
    # Pega o número da página da URL (ex: ?page=2)
    page_number = request.GET.get('page')
    
    # Pega o objeto da página correta
    pagina = paginator.get_page(page_number)

    return pagina

# NOVA VIEW PARA A PÁGINA DE RELATÓRIO
@login_required
def view_relatorio(request):
    form = RelatorioForm(request.GET)
    emprestimos_list = _get_emprestimos_filtrados(request)
    contexto = {
        'form': form,
        'emprestimos_page': paginador(request,emprestimos_list),
        'pagina_ativa': 'relatorio' # Para o menu lateral
    }
    return render(request, 'claviculario_app/relatorio.html', contexto)

# Esta função permanece quase a mesma, apenas o redirect muda
@login_required
def registrar_devolucao(request, emprestimo_id):
    if request.method == 'POST':
        emprestimo = get_object_or_404(Emprestimo, id=emprestimo_id)
        if emprestimo.data_devolucao is not None:
            messages.warning(request, 'Esta chave já foi devolvida anteriormente.')
        else:
            emprestimo.data_devolucao = timezone.now()
            emprestimo.save()
            chave = emprestimo.chave
            chave.disponivel = True
            chave.save()
            messages.info(request, f'Devolução da chave "{chave.descricao}" registrada com sucesso.')
    
    # Redireciona de volta para a página de devolução
    return redirect('view_devolucao')

# NOVA VIEW PARA CADASTRAR PESSOA
@login_required
def cadastrar_pessoa(request):
    # Dicionário para a resposta JSON
    data = {'success': False}
    if request.method == 'POST':
        form = PessoaForm(request.POST)
        if form.is_valid():
            pessoa = form.save()
            data['success'] = True
            # Retorna os dados da nova pessoa para adicionar dinamicamente ao select
            data['pessoa'] = {'id': pessoa.id, 'nome': str(pessoa)}
        else:
            # Coleta os erros do formulário para exibir no modal
            data['errors'] = form.errors.as_json()
    
    # Retorna uma resposta JSON em vez de renderizar um template
    return JsonResponse(data)

#  VIEW PARA SERVIR COMO API DE FILTRO
@login_required
def filtrar_pessoas(request):
    # Pega os parâmetros da URL (ex: /api/pessoas/?nome=joao&empresa=fab)
    nome_query = request.GET.get('nome', '')
    empresa_query = request.GET.get('empresa', '')

    pessoas = Pessoa.objects.all()

    if nome_query:
        # Filtra por nome (case-insensitive)
        pessoas = pessoas.filter(nome__icontains=nome_query)
    
    if empresa_query:
        # Filtra por empresa (case-insensitive)
        pessoas = pessoas.filter(empresa__icontains=empresa_query)

    # Ordena por nome
    pessoas = pessoas.order_by('nome')

    # Transforma a lista de objetos Pessoa em um formato simples (JSON)
    data = [{'id': p.id, 'text': str(p)} for p in pessoas]

    return JsonResponse({'results': data})


#VIEW PARA VALIDAR O PIN E CONCLUIR A RETIRADA
@login_required
def verificar_pin_e_registrar(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método inválido.'})

    try:
        chave_id = request.POST.get('chave_id')
        pessoa_id = request.POST.get('pessoa_id')
        pin_digitado = request.POST.get('pin')
        observacao = request.POST.get('observacao')
        data_retirada = request.POST.get('data_retirada')
        
        # 1. ADICIONADO: Capturar a data de previsão do formulário
        # O 'or None' garante que se o campo vier vazio, salvamos como nulo no banco
        previsao_devolucao = request.POST.get('previsao_devolucao') or None

        pessoa = Pessoa.objects.get(pk=pessoa_id)
        chave = Chave.objects.get(pk=chave_id)

        if not pessoa.check_pin(pin_digitado):
            return JsonResponse({'success': False, 'message': 'PIN incorreto!'})

        if not chave.disponivel:
            return JsonResponse({'success': False, 'message': 'Esta chave foi retirada por outra pessoa. Atualize a página.'})
            
        Emprestimo.objects.create(
            chave=chave,
            pessoa=pessoa,
            data_retirada=data_retirada,
            observacao=observacao,
            # 2. ADICIONADO: Passar o valor para ser salvo no banco de dados
            previsao_devolucao=previsao_devolucao
        )

        chave.disponivel = False
        chave.save()

        return JsonResponse({'success': True, 'message': f'Chave "{chave.descricao}" emprestada com sucesso!'})

    except Pessoa.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Pessoa não encontrada.'})
    except Chave.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Chave não encontrada.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Ocorreu um erro: {e}'})


#VIEW DO DASHBOARD (FAZ CALCULOS DE CHAVES)
@login_required
def dashboard(request):
    # Cálculos dos cards
    total_chaves = Chave.objects.count()
    chaves_emprestadas = Emprestimo.objects.filter(data_devolucao__isnull=True)
    chaves_emprestadas_count = chaves_emprestadas.count()
    chaves_disponiveis = total_chaves - chaves_emprestadas_count
    
    # O cálculo de chaves atrasadas agora é possível
    chaves_atrasadas_count = chaves_emprestadas.filter(
        previsao_devolucao__isnull=False, 
        previsao_devolucao__lt=timezone.now()
    ).count()

    # Listas para a Dashboard
    ultimas_atividades = Emprestimo.objects.order_by('-data_retirada')[:5] # Pega as 5 últimas retiradas
    emprestimos_atrasados = chaves_emprestadas.filter(
        previsao_devolucao__isnull=False,
        previsao_devolucao__lt=timezone.now()
    ).order_by('previsao_devolucao') # Pega todas as chaves atrasadas, ordenadas pela mais antiga

    contexto = {
        'total_chaves': total_chaves,
        'chaves_emprestadas_count': chaves_emprestadas_count,
        'chaves_disponiveis': chaves_disponiveis,
        'chaves_atrasadas_count': chaves_atrasadas_count,
        'ultimas_atividades': ultimas_atividades,
        'emprestimos_atrasados': emprestimos_atrasados,
        'pagina_ativa': 'dashboard' # Para o menu lateral
    }
    return render(request, 'claviculario_app/dashboard.html', contexto)


#------------------------------------------------------------------
# VIEWS DE PESSOAS
#------------------------------------------------------------------
#VIEW PARA SERVIR COMO API DE FILTRO DE CHAVES


# --- CLASS-BASED VIEWS PARA O CRUD DE PESSOAS ---

class PessoaListView(BasePessoaView, BaseListView):
    queryset = BasePessoaView.model.objects.filter(ativa=True).order_by('nome')

class PessoaCreateView(BasePessoaView, BaseCreateView):
    title = 'Adicionar Nova Pessoa'

class PessoaUpdateView(BasePessoaView, BaseUpdateView):
    title = 'Editar Pessoa: {objeto.nome}'

class PessoaDesativarView(BaseDesativarView):
    model = Pessoa
    pagina_ativa = 'pessoas'
    success_message = "A Pessoa '{objeto.nome}' foi desativada com sucesso."
    def form_valid(self, form):
        pessoa = self.get_object()
        if pessoa.emprestimos.filter(data_devolucao__isnull=True).exists():
            messages.error(self.request, f"A pessoa '{pessoa.nome}' não pode ser desativada pois possui chaves pendentes.")
            return redirect('pessoa_list')
        return super().form_valid(form)

@login_required
def filtrar_chaves_por_local(request):
    local_id = request.GET.get('local_id')
    chaves = Chave.objects.filter(disponivel=True, ativa=True) # Começa com todas as chaves disponíveis

    if local_id:
        chaves = chaves.filter(local_id=local_id)
    else:
        # Se nenhum local for selecionado, retorna uma lista vazia
        chaves = Chave.objects.none()

    chaves = chaves.order_by('descricao')
    
    # Transforma a lista de objetos Chave em um formato simples (JSON)
    data = [{'id': c.id, 'text': str(c)} for c in chaves]

    return JsonResponse({'results': data})

@permission_required('claviculario_app.view_pessoa', raise_exception=True)
def pessoa_historico(request, pk):
    pessoa = get_object_or_404(Pessoa, pk=pk)
    # Busca todos os empréstimos dessa pessoa, ordenando pelos mais recentes
    emprestimos_list = pessoa.emprestimos.select_related('chave', 'chave__local').order_by('-data_retirada')    
    contexto = {
        'pessoa': pessoa,
        'emprestimos_page': paginador(request,emprestimos_list),
        'pagina_ativa': 'pessoas'
    }
    return render(request, 'claviculario_app/pessoa_historico.html', contexto)


#------------------------------------------------------------------
# VIEWS DE CHAVES
#------------------------------------------------------------------
class ChaveListView(BaseChaveView, BaseListView):
    queryset = BaseChaveView.model.objects.filter(ativa=True).select_related('local').order_by('local__nome', 'descricao')

class ChaveCreateView(BaseChaveView, BaseCreateView):
    title = 'Adicionar Nova Chave'

class ChaveUpdateView(BaseChaveView, BaseUpdateView):
    title = 'Editar Chave: {objeto.descricao}'

class ChaveDesativarView(BaseDesativarView):
    model = Chave # <-- Definimos o model explicitamente
    pagina_ativa = 'chaves'
    success_message = "A Chave '{objeto.descricao}' foi desativada com sucesso."
    def form_valid(self, form):
        chave = self.get_object()
        if not chave.disponivel:
            messages.error(self.request, f"A chave '{chave.descricao}' não pode ser desativada pois está emprestada.")
            return redirect('chave_list')
        return super().form_valid(form)

@permission_required('claviculario_app.view_chave', raise_exception=True)
def chave_historico(request, pk):
    chave = get_object_or_404(Chave, pk=pk)
    emprestimos_list = chave.emprestimos.select_related('pessoa').order_by('-data_retirada')
    # Aplicamos a paginação
    paginator = Paginator(emprestimos_list, 15)
    page_number = request.GET.get('page')
    emprestimos_page = paginator.get_page(page_number)
    
    contexto = {
        'chave': chave,
        'emprestimos_page': paginador(request,emprestimos_list),
        'pagina_ativa': 'chaves'
    }
    return render(request, 'claviculario_app/chave_historico.html', contexto)

#------------------------------------------------------------------
# VIEWS DE LOCAIS
#------------------------------------------------------------------

class LocalListView(BaseLocalView, BaseListView):
    queryset = BaseLocalView.model.objects.filter(ativa=True).order_by('nome')

class LocalCreateView(BaseLocalView, BaseCreateView):
    title = 'Adicionar Novo Local'

class LocalUpdateView(BaseLocalView, BaseUpdateView):
    title = 'Editar Local: {objeto.nome}'

class LocalDesativarView(BaseDesativarView):
    model = Local # <-- Definimos o model explicitamente
    pagina_ativa = 'locais'
    success_message = "O Local '{objeto.nome}' foi desativado com sucesso."
    def form_valid(self, form):
        local = self.get_object()
        if local.chaves.filter(ativa=True).exists():
            messages.error(self.request, f"O local '{local.nome}' não pode ser desativado pois ainda existem chaves ativas associadas a ele.")
            return redirect('local_list')
        return super().form_valid(form)
# LÓGICA DE FILTRO REUTILIZÁVEL (FUNÇÃO AUXILIAR)
# claviculario_app/views.py

def _get_emprestimos_filtrados(request):
    print("\n--- INICIANDO DEBUG DO FILTRO DE RELATÓRIO ---")
    print(f"[PASSO 1] Dados recebidos na URL (request.GET): {request.GET}")

    form = RelatorioForm(request.GET)
    emprestimos_list = Emprestimo.objects.select_related('chave', 'pessoa').order_by('-data_retirada')

    print(f"[PASSO 2] O formulário é válido? {form.is_valid()}")

    if form.is_valid():
        print(f"[PASSO 3] Dados 'limpos' do formulário (cleaned_data): {form.cleaned_data}")
        
        data_inicio = form.cleaned_data.get('data_inicio')
        data_fim = form.cleaned_data.get('data_fim')
        status = form.cleaned_data.get('status')
        pessoa = form.cleaned_data.get('pessoa')
        chave = form.cleaned_data.get('chave')

        if data_inicio:
            emprestimos_list = emprestimos_list.filter(data_retirada__date__gte=data_inicio)
        if data_fim:
            emprestimos_list = emprestimos_list.filter(data_retirada__date__lte=data_fim)
        if status == 'pendentes':
            emprestimos_list = emprestimos_list.filter(data_devolucao__isnull=True)
            
        if pessoa:
            print(f"-> Aplicando filtro para a pessoa: {pessoa}")
            emprestimos_list = emprestimos_list.filter(pessoa=pessoa)
        if chave:
            print(f"-> Aplicando filtro para a chave: {chave}")
            emprestimos_list = emprestimos_list.filter(chave=chave)
    else:
        # Se o formulário não for válido, vamos ver os erros
        print(f"[ERRO] Erros de validação do formulário: {form.errors}")
    
    print("--- FIM DO DEBUG ---\n")
    return emprestimos_list

# NOVA VIEW PARA EXPORTAR CSV
@login_required
def exportar_relatorio_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="relatorio_claviculario.csv"'
    
    emprestimos = _get_emprestimos_filtrados(request)
    
    writer = csv.writer(response)
    # Cabeçalho do CSV
    writer.writerow(['Chave', 'Responsável', 'CPF/SARAN', 'Data Retirada', 'Data Devolução', 'Observação'])
    
    # Linhas
    for emprestimo in emprestimos:
        writer.writerow([
            emprestimo.chave.descricao,
            emprestimo.pessoa.nome,
            emprestimo.pessoa.cpf_saran,
            emprestimo.data_retirada.strftime('%d/%m/%Y %H:%M'),
            emprestimo.data_devolucao.strftime('%d/%m/%Y %H:%M') if emprestimo.data_devolucao else 'Pendente',
            emprestimo.observacao
        ])
        
    return response

# VIEW PARA EXPORTAR EXCEL
@login_required
def exportar_relatorio_excel(request):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="relatorio_claviculario.xlsx"'
    
    emprestimos = _get_emprestimos_filtrados(request)
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Relatório"
    
    headers = ['Chave', 'Responsável', 'CPF/SARAN', 'Data Retirada', 'Data Devolução', 'Observação']
    ws.append(headers)
    

    for emprestimo in emprestimos:
        # Convert aware datetimes to local time
        data_retirada_local = timezone.localtime(emprestimo.data_retirada)
        
        # Make the datetime "naive" (remove timezone info) for Excel
        data_retirada_naive = data_retirada_local.replace(tzinfo=None)
        
        data_devolucao_final = 'Pendente'
        if emprestimo.data_devolucao:
            data_devolucao_local = timezone.localtime(emprestimo.data_devolucao)
            data_devolucao_final = data_devolucao_local.replace(tzinfo=None)
            
        ws.append([
            emprestimo.chave.descricao,
            emprestimo.pessoa.nome,
            emprestimo.pessoa.cpf_saran,
            data_retirada_naive, # Use the naive datetime
            data_devolucao_final, # Use the naive datetime or 'Pendente'
            emprestimo.observacao
        ])
        
    wb.save(response)
    return response

