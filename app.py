
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Análise Censo Educação Superior",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Análise Temporal do Censo da Educação Superior")
st.sidebar.title("Navegação")

st.markdown(
    """
    Este dashboard interativo permite explorar a evolução da representatividade de estudantes 
    em cursos de computação no Brasil, com foco em dados de ingressantes, concluintes e matriculados.
    Utilize o menu lateral para navegar entre as diferentes análises.
    """
)

@st.cache_data
def load_data():
    try:
        df = pd.read_csv('dados_censo_computacao_consolidado.csv', encoding='utf-8', low_memory=False)
        # Garantir que as colunas de quantidade são numéricas
        qty_cols = ['qt_ing', 'qt_conc', 'qt_mat']
        for col in qty_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except FileNotFoundError:
        st.error("Arquivo 'dados_censo_computacao_consolidado.csv' não encontrado. "
                 "Por favor, certifique-se de que o arquivo está no diretório correto.")
        return pd.DataFrame()

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


