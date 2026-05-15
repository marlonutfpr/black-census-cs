import streamlit as st
import pandas as pd
import plotly.express as px
from i18n import t


def comparativo_formato_page():
    st.title(t("format_title"))

    if 'data' not in st.session_state or st.session_state['data'].empty:
        st.warning(t("data_not_loaded"))
        return

    df = st.session_state['data']
    ano_selecionado = st.session_state.get('ano_selecionado', df['nu_ano_censo'].max())
    tipo_dado_selecionado = st.session_state.get('tipo_dado_selecionado', 'Ingressantes')

    # Colunas de interesse mapeadas pelos tipos já usados no projeto
    coluna_total_map = {
        'Ingressantes': 'qt_ing',
        'Concluintes': 'qt_conc',
        'Matriculados': 'qt_mat'
    }
    coluna_pretos_map = {
        'Ingressantes': 'qt_ing_preta',
        'Concluintes': 'qt_conc_preta',
        'Matriculados': 'qt_mat_preta'
    }

    # Aplicar a classificação de instituição fornecida no exemplo
    if 'tp_categoria_administrativa' in df.columns:
        def categorizar_instituicao(codigo):
            if codigo in [1, 2, 3]:
                return 'Pública'
            elif codigo in [4, 5, 6, 7, 8, 9]:
                return 'Privada'
            else:
                return 'Outro'

        df['tipo_instituicao_agrupado'] = df['tp_categoria_administrativa'].apply(categorizar_instituicao)

    # Detectar coluna de modalidade/formato de ensino (heurística)
    possible_modal_cols = [
        'tp_modalidade', 'in_presencial', 'modalidade', 'tp_modalidade_ensino',
        'forma_ensino', 'no_modalidade', 'in_modalidade', 'tp_forma_ensino'
    ]
    modal_col = None
    for c in possible_modal_cols:
        if c in df.columns:
            modal_col = c
            break

    if modal_col is None:
        st.info(t("format_no_modal_col") + ": " + ", ".join(possible_modal_cols))
        return

    # Criar coluna padronizada 'formato_ensino' com valores 'Presencial' / 'A Distância' / 'Outro'
    unique_vals = df[modal_col].dropna().unique()

    # Heurísticas de mapeamento
    def map_formato(val):
        if pd.isna(val):
            return 'Outro'
        s = str(val).strip().lower()
        # Strings que indicam EAD / distância
        if any(k in s for k in ['dist', 'ead', 'a distância', 'a distancia', 'à distância']):
            return 'A Distância'
        # Strings que indicam presencial
        if any(k in s for k in ['pres', 'presencial']):
            return 'Presencial'
        # Valores numéricos comuns (tentativa): 1 -> Presencial, 2 -> A Distância
        try:
            n = int(float(s))
            if n == 1:
                return 'Presencial'
            if n == 2:
                return 'A Distância'
        except Exception:
            pass
        return 'Outro'

    df['formato_ensino'] = df[modal_col].apply(map_formato)

    st.write(f"Coluna usada para formato: {modal_col}")

    # Filtrar ano
    df_ano = df[df['nu_ano_censo'] == ano_selecionado].copy()
    if df_ano.empty:
        st.info(t("no_data_year", year=ano_selecionado, dtype=tipo_dado_selecionado))
        return

    coluna_total = coluna_total_map.get(tipo_dado_selecionado, 'qt_ing')
    coluna_pretos = coluna_pretos_map.get(tipo_dado_selecionado, 'qt_ing_preta')

    # Agrupar por formato
    resumo = df_ano.groupby('formato_ensino').agg(
        total_geral=(coluna_total, 'sum'),
        total_pretos=(coluna_pretos, 'sum')
    ).reset_index()
    resumo['percentual_pretos'] = (resumo['total_pretos'] / resumo['total_geral'] * 100).round(2)

    st.subheader(t("format_bar_sub", dtype=tipo_dado_selecionado, year=ano_selecionado))
    fig = px.bar(
        resumo,
        x='formato_ensino',
        y='percentual_pretos',
        color='percentual_pretos',
        color_continuous_scale='Turbo',
        labels={'formato_ensino': t("format_label"), 'percentual_pretos': t("representativeness")},
        title=t("format_bar_title", dtype=tipo_dado_selecionado, year=ano_selecionado)
    )
    st.plotly_chart(fig, use_container_width=True, key=f'formato_bar_{ano_selecionado}_{tipo_dado_selecionado}')

    st.subheader(t("format_table_sub"))
    resumo_display = resumo.sort_values('percentual_pretos', ascending=False).copy()
    resumo_display = resumo_display.rename(columns={
        'formato_ensino': t("format_label"),
        'total_geral': t("total"),
        'total_pretos': t("black_students"),
        'percentual_pretos': t("representativeness")
    })
    cols_order = [t("format_label"), t("total"), t("black_students"), t("representativeness")]
    cols_present = [c for c in cols_order if c in resumo_display.columns]
    st.dataframe(resumo_display[cols_present])

    # Evolução temporal por formato
    evo = df.groupby(['nu_ano_censo', 'formato_ensino']).agg(
        total_geral=(coluna_total, 'sum'),
        total_pretos=(coluna_pretos, 'sum')
    ).reset_index()
    evo['percentual_pretos'] = (evo['total_pretos'] / evo['total_geral'] * 100).round(2)

    st.subheader(t("format_evol_sub"))
    fig_evo = px.line(
        evo,
        x='nu_ano_censo',
        y='percentual_pretos',
        color='formato_ensino',
        labels={'nu_ano_censo': t("year"), 'percentual_pretos': t("representativeness"), 'formato_ensino': t("format_label")},
        title=t("format_evol_title", dtype=tipo_dado_selecionado),
        markers=True
    )
    st.plotly_chart(fig_evo, use_container_width=True, key=f'formato_evol_{tipo_dado_selecionado}')




# Nota: a função `comparativo_formato_page` é chamada a partir de `app.py`
