"""Algoritmos do Challenge EntreDegraus: DP, grafos e planejamento."""
from __future__ import annotations
from collections import deque
from functools import lru_cache
from heapq import heappush, heappop
from math import hypot
from pathlib import Path
from time import perf_counter
import json
import pandas as pd

BASE = 'BASE_SIMULADA'


def carregar_dados(pasta='dados'):
    """Lê ocorrências REAIS dos arquivos e uma rede de deslocamentos HIPOTÉTICA."""
    pasta = Path(pasta)
    eventos = pd.read_csv(pasta/'ocorrencias_motiva_2025_2026.csv', parse_dates=['momento'])
    rede = json.loads((pasta/'rede_estacoes.json').read_text(encoding='utf-8'))
    exigidas = {'escada_id','estacao','momento','duracao_indisponibilidade_min','indisponivel','falha'}
    if not exigidas.issubset(eventos.columns): raise ValueError('Faltam colunas de ocorrências')
    if eventos[list(exigidas)].isna().any().any(): raise ValueError('Ocorrências incompletas')
    if (eventos.duracao_indisponibilidade_min < 0).any(): raise ValueError('Duração negativa')
    if (eventos.groupby('escada_id').estacao.nunique()!=1).any(): raise ValueError('Escada em estações diferentes')
    if not set(eventos.estacao).issubset({n['nome'] for n in rede['nos']}): raise ValueError('Estação ausente')
    return eventos.sort_values(['escada_id','momento']),rede


def dano_leitura(r):
    """Proxy de desgaste por ocorrência; NÃO usa vibração/temperatura/sensores.

    Cada evento vale 1 ponto, acrescido de até 4 pela indisponibilidade
    (1 ponto por 60 minutos), mais 0,5 por marcação de indisponibilidade
    e 0,5 por marcação de falha. Pesos são HIPÓTESES didáticas.
    """
    return (1.0 + min(float(r['duracao_indisponibilidade_min'])/60,4)
            + 0.5*int(r['indisponivel']) + 0.5*int(r['falha']))


def degradacao_recursiva(danos):
    """Recorrência exponencial sem cache: D(i)=d(i)+0.85D(i-1)+0.15D(i-2)."""
    def resolver(i):
        if i < 0: return 0.
        return danos[i] + 0.85*resolver(i-1) + 0.15*resolver(i-2)
    return resolver(len(danos)-1)


def degradacao_memoizada(danos):
    """Mesma recorrência, com memoização em dicionário; O(n) tempo/espaço."""
    memo = {}
    def resolver(i):
        if i < 0: return 0.
        if i not in memo:
            memo[i] = danos[i] + 0.85*resolver(i-1) + 0.15*resolver(i-2)
        return memo[i]
    return resolver(len(danos)-1)


def degradacao_tabulada(danos):
    """Mesma recorrência por tabulação; O(n) tempo e O(1) espaço."""
    anterior, penultimo = 0., 0.
    for dano in danos:
        atual = dano + 0.85*anterior + 0.15*penultimo
        penultimo, anterior = anterior, atual
    return anterior


def avaliar_algoritmos(leituras, repeticoes=3, janela=16):
    """Compara as 3 recorrências na MESMA janela de até 16 ocorrências por escada.

    Recursão pura tem custo exponencial; limitar janela é indispensável.
    Ranking mede histórico recente de ocorrências, NÃO desgaste por sensores.
    """
    funcoes={'Recursiva pura':degradacao_recursiva,
            'Memoizada (dicionário)':degradacao_memoizada,
            'Iterativa (tabulação)':degradacao_tabulada}
    tempos,ranking=[],[]
    for escada,grupo in leituras.groupby('escada_id',sort=True):
        ultimas=grupo.tail(janela)
        danos=[dano_leitura(r) for r in ultimas.to_dict('records')]
        valores={}
        for nome,funcao in funcoes.items():
            medidas=[]
            for _ in range(repeticoes):
                inicio=perf_counter();valor=funcao(danos)
                medidas.append((perf_counter()-inicio)*1000)
            tempos.append({'escada_id':escada,'algoritmo':nome,'tempo_ms':sum(medidas)/len(medidas)})
            valores[nome]=valor
        assert max(valores.values())-min(valores.values())<1e-8
        ranking.append({'escada_id':escada,'estacao':grupo.estacao.iloc[0],
                        'criticidade':valores['Iterativa (tabulação)'],
                        'ocorrencias_na_janela':len(danos),'ocorrencias_totais':len(grupo)})
    ranking=pd.DataFrame(ranking).sort_values('criticidade',ascending=False).reset_index(drop=True)
    ranking.insert(0,'posicao',range(1,len(ranking)+1))
    return ranking,pd.DataFrame(tempos)


def construir_grafo(rede):
    """Grafo não direcionado com lista de adjacência e pesos em minutos."""
    grafo = {n['nome']:[] for n in rede['nos']}
    for e in rede['arestas']:
        a,b,w=e['origem'],e['destino'],float(e['minutos'])
        if a not in grafo or b not in grafo or w <= 0:
            raise ValueError('Aresta inválida')
        grafo[a].append((b,w));grafo[b].append((a,w))
    for adj in grafo.values(): adj.sort()
    return grafo


def reconstruir(pais, origem, destino):
    """Reconstrói caminho ou retorna lista vazia se inalcançável."""
    if destino not in pais: return []
    caminho=[destino]
    while caminho[-1] != origem:
        caminho.append(pais[caminho[-1]])
    return caminho[::-1]


def bfs(grafo, origem, destino):
    """Menor número de arestas, independentemente dos pesos."""
    fila=deque([origem]); pais={origem:None}
    while fila:
        atual=fila.popleft()
        if atual == destino: break
        for vizinho,_ in grafo[atual]:
            if vizinho not in pais:
                pais[vizinho]=atual;fila.append(vizinho)
    return reconstruir(pais,origem,destino)


def tempo_rota(grafo, caminho):
    """Soma pesos da rota em minutos; infinito para rota inexistente."""
    if not caminho: return float('inf')
    return sum(next(w for v,w in grafo[a] if v==b) for a,b in zip(caminho,caminho[1:]))


def dijkstra(grafo, origem, destino):
    """Menor tempo em grafo com pesos positivos; devolve tempo e rota."""
    dist={origem:0.};pais={origem:None};heap=[(0.,origem)]
    while heap:
        custo,u=heappop(heap)
        if custo > dist[u]:continue
        if u==destino:break
        for v,w in grafo[u]:
            novo=custo+w
            if novo < dist.get(v,float('inf')):
                dist[v]=novo;pais[v]=u;heappush(heap,(novo,v))
    return dist.get(destino,float('inf')), reconstruir(pais,origem,destino)


def fator_heuristico(rede):
    """Menor razão tempo/distância das arestas: limite inferior admissível."""
    pos={n['nome']:(n['x_km_ilustrativo'],n['y_km_ilustrativo']) for n in rede['nos']}
    taxas=[]
    for e in rede['arestas']:
        distancia=hypot(pos[e['origem']][0]-pos[e['destino']][0],pos[e['origem']][1]-pos[e['destino']][1])
        if distancia>0:taxas.append(e['minutos']/distancia)
    return min(taxas),pos


def a_estrela(grafo, origem, destino, rede):
    """A* com h=distância euclidiana * menor min/km do grafo.

    Pela desigualdade triangular, h nunca supera o custo real restante,
    mesmo com arestas de atalho: heurística admissível e consistente.
    Coordenadas são sintéticas e usadas somente na demonstração.
    """
    fator,pos=fator_heuristico(rede)
    def h(u):return fator*hypot(pos[u][0]-pos[destino][0],pos[u][1]-pos[destino][1])
    heap=[(h(origem),0.,origem)];dist={origem:0.};pais={origem:None}
    while heap:
        _,custo,u=heappop(heap)
        if custo>dist[u]:continue
        if u==destino:break
        for v,w in grafo[u]:
            novo=custo+w
            if novo<dist.get(v,float('inf')):
                dist[v]=novo;pais[v]=u;heappush(heap,(novo+h(v),novo,v))
    return dist.get(destino,float('inf')),reconstruir(pais,origem,destino)


def comparar_rotas(grafo, rede, base=BASE):
    """Calcula BFS, Dijkstra e A* para todas as estações."""
    saida=[]
    for n in rede['nos']:
        destino=n['nome']
        if destino==base:continue
        rota_b=bfs(grafo,base,destino)
        td,rd=dijkstra(grafo,base,destino)
        ta,ra=a_estrela(grafo,base,destino,rede)
        assert abs(td-ta)<1e-9
        saida.append({'estacao':destino,'trechos_bfs':len(rota_b)-1,
                      'minutos_bfs':tempo_rota(grafo,rota_b),'minutos_dijkstra':td,
                      'minutos_a_estrela':ta,'rota_bfs':' → '.join(rota_b),
                      'rota_dijkstra':' → '.join(rd),'rota_a_estrela':' → '.join(ra)})
    return pd.DataFrame(saida)


def planejar_turno(base, horas, ranking, grafo, rede, minutos_por_manutencao=45):
    """Planejamento guloso: maior criticidade primeiro, respeitando deslocamentos.

    Considera deslocamento entre atendimentos e retorno à base; não resolve
    otimização global de roteamento (VRP/TSP). Não fraciona atendimentos.
    """
    if horas<=0 or minutos_por_manutencao<=0:raise ValueError('Duração inválida')
    restantes=ranking.to_dict('records'); atual=base;gasto=0.;plano=[]
    limite=horas*60
    for item in restantes:  # prioridade pelo ranking, sem reordenação oportunista
        ida,rota=dijkstra(grafo,atual,item['estacao'])
        volta,_=dijkstra(grafo,item['estacao'],base)
        if gasto+ida+minutos_por_manutencao+volta>limite:
            continue
        gasto+=ida+minutos_por_manutencao
        plano.append({'ordem':len(plano)+1,'escada_id':item['escada_id'],
                      'estacao':item['estacao'],'criticidade':round(item['criticidade'],4),
                      'origem':atual,'rota':' → '.join(rota),
                      'deslocamento_min':ida,'servico_min':minutos_por_manutencao,
                      'acumulado_min':gasto})
        atual=item['estacao']
    retorno,rota_retorno=dijkstra(grafo,atual,base)
    return pd.DataFrame(plano),{'base':base,'horas_disponiveis':horas,
         'minutos_usados_com_retorno':gasto+retorno,'minutos_livres':limite-gasto-retorno,
         'rota_retorno':' → '.join(rota_retorno),
         'observacao':'Heurística gulosa; prioriza criticidade, não garante ótimo global.'}
