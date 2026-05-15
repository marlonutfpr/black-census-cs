
import os

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


def _get_db_url() -> str:
    """Connection string do Supabase: st.secrets > env SUPABASE_DB_URL."""
    try:
        return st.secrets["supabase"]["db_url"]
    except Exception:
        return os.environ.get("SUPABASE_DB_URL", "")


def _build_sa_url(raw: str) -> URL:
    """Monta a URL do SQLAlchemy a partir de componentes (tolerante a
    caracteres especiais na senha, ex.: '/'). URL.create faz o escaping."""
    _, _, rest = raw.partition("://")
    rest, _, query = rest.partition("?")
    creds, _, hostpart = rest.rpartition("@")
    user, _, password = creds.partition(":")
    hostport, _, dbname = hostpart.partition("/")
    host, _, port = hostport.rpartition(":")
    params = dict(p.split("=", 1) for p in query.split("&") if "=" in p)
    return URL.create(
        "postgresql+psycopg2",
        username=user,
        password=password,
        host=host,
        port=int(port) if port else 5432,
        database=dbname or "postgres",
        query={"sslmode": params.get("sslmode", "require")},
    )

st.set_page_config(
    page_title="Análise Censo Educação Superior",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Análise Temporal do Censo da Educação Superior")
st.sidebar.title("Navegação")

# Opção para carregar arquivo CSV pelo usuário (tem prioridade sobre o arquivo local)
st.sidebar.subheader("Dados")
uploaded_file = st.sidebar.file_uploader("Carregar arquivo CSV do censo (opcional)", type=['csv'], help="Escolha um arquivo CSV consolidado para carregar os dados localmente.")

st.markdown(
    """
    Este dashboard interativo permite explorar a evolução da representatividade de estudantes 
    em cursos de computação no Brasil, com foco em dados de ingressantes, concluintes e matriculados.
    Utilize o menu lateral para navegar entre as diferentes análises.
    """
)

@st.cache_resource
def _engine():
    raw = _get_db_url()
    if not raw:
        return None
    return create_engine(_build_sa_url(raw), pool_pre_ping=True)


# --- Agregação server-side ---------------------------------------------------
# As páginas só agrupam/filtram por estas 5 dimensões e somam estas medidas.
# Como SUM é associativo, fazer o roll-up no Postgres e reagrupar por
# subconjuntos no pandas dá exatamente o mesmo resultado — mas trafega ~10x
# menos dados que o `SELECT *` (228 colunas x 319k linhas).
_DIMS = [
    "nu_ano_censo",
    "no_regiao",
    "no_curso",
    "tp_categoria_administrativa",
    "tp_modalidade_ensino",
]
_MEASURES = [
    f"qt_{t}{suf}"
    for t in ("ing", "conc", "mat")
    for suf in ("", "_preta", "_parda", "_amarela", "_indigena", "_branca", "_cornd")
]
_ROLLUP_SQL = (
    "SELECT "
    + ", ".join(_DIMS)
    + ", "
    + ", ".join(f"COALESCE(SUM({m}), 0) AS {m}" for m in _MEASURES)
    + " FROM v_censo_consolidado GROUP BY "
    + ", ".join(_DIMS)
)
# A materialized view mv_censo_rollup já contém esse roll-up pré-calculado
# (criada por db/load_supabase.py). Lê ~9k linhas sem joins (~1s). Se não
# existir, cai no GROUP BY acima sobre a view.
_MV_SQL = "SELECT * FROM mv_censo_rollup"


@st.cache_data(show_spinner="Carregando dados do Supabase (agregação server-side)...")
def load_data():
    engine = _engine()
    if engine is None:
        st.error(
            "Connection string do Supabase não configurada. Defina "
            "`[supabase] db_url` em `.streamlit/secrets.toml` ou a variável "
            "de ambiente `SUPABASE_DB_URL`."
        )
        return pd.DataFrame()
    try:
        try:
            df = pd.read_sql_query(_MV_SQL, engine)
        except Exception:
            # MV ausente (ex.: carga antiga) — agrega a view na hora.
            df = pd.read_sql_query(_ROLLUP_SQL, engine)
        for col in _MEASURES:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Não foi possível ler do Supabase: {e}")
        return pd.DataFrame()

df = None
if uploaded_file is not None:
    try:
        # tentar ler como UTF-8 primeiro
        df = pd.read_csv(uploaded_file, encoding='utf-8', low_memory=False)
    except Exception:
        try:
            # fallback comum para arquivos CSV em Windows/latin1
            df = pd.read_csv(uploaded_file, encoding='latin-1', low_memory=False)
        except Exception as e:
            st.error(f"Não foi possível ler o arquivo enviado: {e}")
            df = pd.DataFrame()
    if not df.empty:
        # garantir colunas numéricas
        qty_cols = ['qt_ing', 'qt_conc', 'qt_mat']
        for col in qty_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        st.success(f"Arquivo '{getattr(uploaded_file, 'name', 'upload')}' carregado com sucesso.")
        # armazenar informação de upload na sessão para referência
        st.session_state['uploaded_file_name'] = getattr(uploaded_file, 'name', None)
else:
    df = load_data()

if not df.empty:
    st.sidebar.header("Filtros Globais")

    # Menu de navegação de páginas
    paginas = {
        "Visão Geral": "1_Visao_Geral",
        "Comparativo por Curso": "2_Comparativo_por_Curso",
        "Análise Regional": "3_Analise_Regional",
        "Análise Institucional": "4_Analise_Institucional",
        "Comparativo por Formato": "6_Comparativo_Formato",
        "Projeção e Tendências": "8_Projecao",
        "Comparativo Geral": "5_Comparativo_Geral"
    }
    pagina_selecionada = st.sidebar.radio(
        "Selecione a Página",
        list(paginas.keys()),
        index=0
    )

    anos_disponiveis = sorted(df['nu_ano_censo'].unique())
    ano_selecionado = st.sidebar.slider(
        "Selecione o Ano",
        min_value=int(min(anos_disponiveis)),
        max_value=int(max(anos_disponiveis)),
        value=int(max(anos_disponiveis)),
        step=1
    )

    # Mostrar o seletor de tipo de dado apenas se não estivermos na página 'Comparativo Geral'
    tipo_dado_selecionado = None
    if pagina_selecionada != 'Comparativo Geral':
        tipo_dado_selecionado = st.sidebar.radio(
            "Tipo de Dado",
            ('Ingressantes', 'Concluintes', 'Matriculados'),
            index=0
        )
    else:
        # Garantir que exista um valor em session_state (usar valor existente ou padrão)
        tipo_dado_selecionado = st.session_state.get('tipo_dado_selecionado', 'Ingressantes')

    st.session_state['ano_selecionado'] = ano_selecionado
    st.session_state['tipo_dado_selecionado'] = tipo_dado_selecionado
    st.session_state['data'] = df

    # Importação dinâmica da página selecionada
    import importlib
    modulo = importlib.import_module(paginas[pagina_selecionada])
    # Chama a função principal da página
    func_name = [f for f in dir(modulo) if f.endswith('_page')][0]
    getattr(modulo, func_name)()

    st.info("Navegue pelas páginas no menu lateral para ver as análises.")
else:
    st.warning("Não foi possível carregar os dados. Verifique o arquivo CSV.")


