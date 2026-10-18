from entredegraus_dp import *

def test_dp():
    d=[1,2,3,4,5]
    assert abs(degradacao_recursiva(d)-degradacao_memoizada(d))<1e-10
    assert abs(degradacao_memoizada(d)-degradacao_tabulada(d))<1e-10

def test_rotas():
    dados,rede=carregar_dados('dados');g=construir_grafo(rede)
    for n in rede['nos']:
        dest=n['nome']
        if dest==BASE:continue
        d,_=dijkstra(g,BASE,dest);a,_=a_estrela(g,BASE,dest,rede)
        assert abs(d-a)<1e-9

def test_turno():
    dados,rede=carregar_dados('dados');rank,_=avaliar_algoritmos(dados,repeticoes=1)
    plano,res=planejar_turno(BASE,8,rank,construir_grafo(rede),rede)
    assert res['minutos_livres']>=-1e-8
