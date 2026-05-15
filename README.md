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

O dashboard lê de um PostgreSQL no **Supabase** (materialized view
`mv_censo_rollup`, agregação server-side). O pipeline é:
microdados → CSV consolidado → SQLite (`db/etl.py`) → Supabase
(`db/load_supabase.py`). Detalhes em [db/ETL.md](db/ETL.md).

Configuração local:

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edite secrets.toml com a connection string do Supabase (Session pooler)
python db/load_supabase.py   # recria schema + carrega dados + materialized view
```

Executando o dashboard localmente

```bash
streamlit run app.py
```

A connection string pode vir de `.streamlit/secrets.toml`
(`[supabase] db_url`) ou da variável de ambiente `SUPABASE_DB_URL`.

Deploy no Render

O repositório inclui [`render.yaml`](render.yaml) (Blueprint). Passos:

1. Garanta que os dados já estão no Supabase (`python db/load_supabase.py`
   uma vez — o dashboard só lê de lá, não precisa de arquivos no Render).
2. No [dashboard do Render](https://dashboard.render.com): **New → Blueprint**,
   conecte este repositório e selecione a branch.
3. O Render lê o `render.yaml` e cria um Web Service (Python, plano free,
   build `pip install -r requirements.txt`, start
   `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`).
4. Na aba **Environment** do serviço, defina o secret **`SUPABASE_DB_URL`**
   com a connection string do Supabase (Session pooler, porta 5432). Ele
   está marcado como `sync: false` no blueprint — não vai versionado.
5. Deploy. A app sobe na URL `*.onrender.com`.

Observações:
- Plano free do Render hiberna após inatividade (primeiro acesso seguinte
  fica lento) e a 1ª carga de cada sessão leva ~6s (cacheada depois).
- Se houver erro de conexão WebSocket atrás do proxy do Render, adicione ao
  start command `--server.enableCORS false --server.enableXsrfProtection false`.

Observações e convenções

- Seletores de `Ano` e `Tipo de Dado` (Ingressantes / Concluintes / Matriculados) estão na barra lateral.
- As páginas são importadas dinamicamente; se mover ou renomear arquivos de página, atualize o mapeamento `paginas` em `app.py` ou `code/app.py`.
- Colunas esperadas no CSV: `nu_ano_censo`, `qt_ing`, `qt_ing_preta`, `qt_conc`, `qt_conc_preta`, `qt_mat`, `qt_mat_preta`, `tp_cor_raca`, entre outras (vários scripts fazem heurísticas para detectar campos similares).

Contribuição

- Abra uma issue descrevendo o bug ou feature. Para mudanças de código maiores, envie um pull request com descrição e testes/prints.

Contato
