# Black Census - Censos da Educação Superior (Computação)

Este repositório contém um dashboard Streamlit para explorar a representatividade de estudantes (com foco em pretos) em cursos de computação no Brasil.

Conteúdo principal

- app.py - ponto de entrada do Streamlit 
- Páginas: `1_Visao_Geral.py`, `2_Comparativo_por_Curso.py`, `3_Analise_Regional.py`, `4_Analise_Institucional.py`, `5_Comparativo_Geral.py`, `6_Comparativo_Formato.py`, `7_Analise_Geral.py`, `8_Projecao.py`
- `dados_censo_computacao_consolidado.csv` 

Requisitos

- Python 3.9+ recomendado
- Dependências principais:
  - streamlit
  - pandas
  - plotly
  - scipy (opcional, usado para projeções; instalar para habilitar regressões)

Instalação rápida

1. Crie um virtualenv e ative:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Instale dependências (exemplo mínimo):

```bash
pip install streamlit pandas plotly scipy
```

Fonte de dados

O dashboard lê de um banco SQLite (`db/censo.db`) gerado por uma ETL a
partir do CSV consolidado. Gere o banco uma vez:

```bash
pip install pandas
python db/etl.py
```

Detalhes do modelo relacional e do pipeline em [db/ETL.md](db/ETL.md).
Ainda é possível, opcionalmente, subir um CSV consolidado pela barra
lateral (tem prioridade sobre o banco na sessão).

Executando o dashboard

```bash
streamlit run app.py
```

Observações e convenções

- Seletores de `Ano` e `Tipo de Dado` (Ingressantes / Concluintes / Matriculados) estão na barra lateral.
- As páginas são importadas dinamicamente; se mover ou renomear arquivos de página, atualize o mapeamento `paginas` em `app.py` ou `code/app.py`.
- Colunas esperadas no CSV: `nu_ano_censo`, `qt_ing`, `qt_ing_preta`, `qt_conc`, `qt_conc_preta`, `qt_mat`, `qt_mat_preta`, `tp_cor_raca`, entre outras (vários scripts fazem heurísticas para detectar campos similares).

Contribuição

- Abra uma issue descrevendo o bug ou feature. Para mudanças de código maiores, envie um pull request com descrição e testes/prints.

Contato
