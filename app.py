
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

import chart_theme
chart_theme.apply()

import i18n

# ── Seletor de idioma (topo da sidebar, sempre visível) ───────────────────────
lang_label = st.sidebar.selectbox(
    i18n.t("nav_language"),
    list(i18n.LANGUAGES.keys()),
    index=list(i18n.LANGUAGES.keys()).index(
        next((k for k, v in i18n.LANGUAGES.items() if v == i18n.get_language()), "🇧🇷 Português")
    ),
)
i18n.set_language(lang_label)

st.sidebar.title(i18n.t("nav_title"))
st.sidebar.markdown("---")



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

df = load_data()

if not df.empty:
    st.sidebar.header(i18n.t("nav_global_filters"))

    # Menu de navegação de páginas
    paginas = {
        i18n.t("page_home"):        "0_Home",
        i18n.t("page_overview"):    "1_Visao_Geral",
        i18n.t("page_by_course"):   "2_Comparativo_por_Curso",
        i18n.t("page_regional"):    "3_Analise_Regional",
        i18n.t("page_institutional"): "4_Analise_Institucional",
        i18n.t("page_format"):      "6_Comparativo_Formato",
        i18n.t("page_projection"):  "8_Projecao",
        i18n.t("page_general"):     "5_Comparativo_Geral",
    }
    pagina_selecionada = st.sidebar.radio(
        i18n.t("nav_select_page"),
        list(paginas.keys()),
        index=0
    )

    anos_disponiveis = sorted(df['nu_ano_censo'].unique())
    ano_selecionado = st.sidebar.slider(
        i18n.t("nav_select_year"),
        min_value=int(min(anos_disponiveis)),
        max_value=int(max(anos_disponiveis)),
        value=int(max(anos_disponiveis)),
        step=1
    )

    # Tipos de dado localizados
    dtype_labels = i18n.dtype_keys()
    home_key = i18n.t("page_home")
    general_key = i18n.t("page_general")

    # Mostrar o seletor de tipo de dado apenas se não estivermos na página Inicial ou Comparativo Geral
    tipo_dado_selecionado = None
    if pagina_selecionada not in (home_key, general_key):
        tipo_dado_selecionado_label = st.sidebar.radio(
            i18n.t("nav_data_type"),
            dtype_labels,
            index=0
        )
        # Converter para o equivalente em PT (chave interna usada pelas páginas)
        tipo_dado_selecionado = i18n.dtype_to_pt(tipo_dado_selecionado_label)
    else:
        tipo_dado_selecionado = st.session_state.get('tipo_dado_selecionado', 'Ingressantes')

    # Na Página Inicial, renderizar e parar
    if pagina_selecionada == home_key:
        import importlib
        modulo = importlib.import_module("0_Home")
        modulo.home_page()
        st.stop()

    st.session_state['ano_selecionado'] = ano_selecionado
    st.session_state['tipo_dado_selecionado'] = tipo_dado_selecionado
    st.session_state['data'] = df

    # Importação dinâmica da página selecionada
    import importlib
    modulo = importlib.import_module(paginas[pagina_selecionada])
    # Chama a função principal da página
    func_name = [f for f in dir(modulo) if f.endswith('_page')][0]
    getattr(modulo, func_name)()

    st.info(i18n.t("nav_select_page"))
else:
    # Mesmo sem dados, permite ver a Página Inicial
    import importlib as _il
    _home = _il.import_module("0_Home")
    _home.home_page()
    st.warning("Não foi possível carregar os dados. Verifique a conexão com o Supabase ou carregue um arquivo CSV.")


