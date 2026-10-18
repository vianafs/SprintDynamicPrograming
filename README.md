# EntreDegraus — Dynamic Programming (dados Motiva)

Projeto Python para o Challenge Motiva/FIAP, com notebook **executado**, algoritmos documentados e resultados.

## O que veio dos arquivos oficiais

Foram lidas as planilhas **`ecr_2025.XLSX` e `ecr_2026.XLSX`** do ZIP enviado pelo grupo. Foram extraídas **17,951 ocorrências válidas**, de **197 escadas** distribuídas por **12 códigos de estação**. Foram ignoradas ocorrências sem código `-ECR-XXX-ERnn` reconhecível ou com datas inválidas. O CSV `dados/ocorrencias_motiva_2025_2026.csv` contém o recorte necessário para reproduzir os cálculos.

**Limitação essencial:** essas planilhas são registros de **avarias e manutenção**, e não leituras estruturadas de vibração, temperatura, corrente, tensão, nível de óleo e velocidade. Não inventamos essas medições. O ranking produzido é uma **proxy de criticidade por histórico de ocorrências**, não um indicador de degradação por sensores. Para atender literalmente ao item de sensores do enunciado, é preciso acrescentar a planilha correta de telemetria.

## Metodologia

- **Dano por ocorrência:** `1 + min(duração_em_minutos/60, 4) + 0,5 × indisponível + 0,5 × falha`. Pesos e limite de quatro horas são escolhas **didáticas**, não parâmetros Motiva.
- **Recorrência:** `D(i) = dano(i) + 0,85 D(i-1) + 0,15 D(i-2)`; casos anteriores ao primeiro valem zero. Implementada por recursão pura, memoização em dicionário e tabulação iterativa.
- **Comparação justa:** todas as versões recebem as **últimas 16 ocorrências** por escada. Esse limite evita a explosão exponencial da versão recursiva pura. O ranking usa a mesma janela.
- **Grafo:** 12 códigos de estação encontrados nas planilhas, ligados a uma **base simulada**. Arestas, coordenadas e pesos em minutos são **hipóteses acadêmicas** (ver `dados/rede_estacoes.json`). Não correspondem à rede ou a tempos oficiais.
- **Rotas:** BFS minimiza o número de trechos; Dijkstra e A* minimizam minutos. A heurística de A* é a distância euclidiana ilustrativa multiplicada pela menor razão tempo/distância das arestas, um limite inferior consistente e admissível.
- **Turno:** `planejar_turno(BASE, 8, ...)` tenta atender as escadas em ordem decrescente de criticidade, considera deslocamentos entre estações e retorno à base, e reserva 45 minutos por serviço. Heurística gulosa, sem garantia de ótimo global.

## Resultados observados

- As três implementações de programação dinâmica produziram valores numericamente iguais.
- Tempos médios observados (ms por equipamento): Iterativa (tabulação): 0.0011, Memoizada (dicionário): 0.0043, Recursiva pura: 0.2426. Valores variam conforme o computador.
- Dijkstra e A* retornaram o mesmo menor tempo para todas as 12 estações do grafo.
- No turno simulado de 8 horas, foram programados **10 atendimentos**, incluindo retorno à base, com **480.0 minutos** utilizados.
- Os primeiros equipamentos do ranking são: SP04-6-ECR-PIN-ER06, SP04-6-ECR-PIN-ER21, SP04-6-ECR-PIN-ER14, SP04-6-ECR-PIN-ER26, SP04-6-ECR-PIN-ER20. Isso indica **prioridade na pontuação criada**, não risco operacional validado.

## Como executar

```bash
pip install -r requirements.txt
jupyter notebook notebook.ipynb
```

Também é possível importar as funções de `entredegraus_dp.py`. O notebook já contém saídas gravadas e abre diretamente no GitHub. Os resultados exportados ficam em `resultados/`.

## Estrutura

- `notebook.ipynb`: demonstração executada, explicações e interpretações.
- `entredegraus_dp.py`: funções documentadas.
- `dados/ocorrencias_motiva_2025_2026.csv`: extração de ocorrências **reais**.
- `dados/rede_estacoes.json`: códigos de estação reais, **arestas e tempos simulados**.
- `resultados/`: ranking, rotas e turno.
- `testes/`: testes automatizados.

## Ética e escopo

Não contém nomes de funcionários, telefones ou texto longo livre dos registros originais. Não deve ser usado para orientar equipes de manutenção reais sem validação de engenharia, telemetria e tempos oficiais.
