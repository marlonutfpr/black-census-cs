import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def preparar_dados_temporais(df: pd.DataFrame, tipo: str = 'Ingressantes') -> pd.DataFrame:
    """
    Prepara dados para análise temporal para o tipo selecionado.
    Retorna um DataFrame com colunas genéricas:
    - nu_ano_censo
    - total_sel
    - black_sel
    - other_sel
    - percent_black
    - percent_other
    """
    df_local = df.copy()

    # Mapear nomes de colunas para o tipo selecionado
    tipos_map = {
        'Ingressantes': ('qt_ing', 'qt_ing_preta'),
        'Concluintes': ('qt_conc', 'qt_conc_preta'),
        'Matriculados': ('qt_mat', 'qt_mat_preta')
    }
    total_col, black_col = tipos_map.get(tipo, ('qt_ing', 'qt_ing_preta'))

    # Garantir colunas numéricas (se existirem)
    if total_col in df_local.columns:
        df_local[total_col] = pd.to_numeric(df_local[total_col], errors='coerce').fillna(0)
    else:
        df_local[total_col] = 0

    if black_col in df_local.columns:
        df_local[black_col] = pd.to_numeric(df_local[black_col], errors='coerce').fillna(0)
    else:
        # se a coluna de pretos não existir, criar com zeros e avisar
        df_local[black_col] = 0
        st.warning(f"Coluna '{black_col}' não encontrada. A análise de representatividade para '{tipo}' não terá valores de pretos.")

    # Agrupar
    temporal_total = df_local.groupby(['nu_ano_censo'])[total_col].sum().reset_index().rename(columns={total_col: 'total_sel'})
    temporal_black = df_local.groupby(['nu_ano_censo'])[black_col].sum().reset_index().rename(columns={black_col: 'black_sel'})

    temporal_combined = pd.merge(temporal_total, temporal_black, on='nu_ano_censo', how='left').fillna(0)
    temporal_combined['other_sel'] = temporal_combined['total_sel'] - temporal_combined['black_sel']

    # percentuais (protegendo divisão por zero)
    temporal_combined['percent_black'] = 0.0
    temporal_combined['percent_other'] = 0.0
    nonzero_mask = temporal_combined['total_sel'] != 0
    if nonzero_mask.any():
        temporal_combined.loc[nonzero_mask, 'percent_black'] = (temporal_combined.loc[nonzero_mask, 'black_sel'] / temporal_combined.loc[nonzero_mask, 'total_sel'] * 100).round(1)
        temporal_combined.loc[nonzero_mask, 'percent_other'] = (temporal_combined.loc[nonzero_mask, 'other_sel'] / temporal_combined.loc[nonzero_mask, 'total_sel'] * 100).round(1)

    return temporal_combined


def analise_geral_page():
    st.title("Análise Geral")

    if 'data' not in st.session_state or st.session_state['data'].empty:
        st.warning("Dados não carregados. Por favor, retorne à página inicial.")
        return

    df = st.session_state['data']

    # Usar o 'Tipo de Dado' definido na sidebar (em app.py) quando disponível
    tipo_escolhido = st.session_state.get('tipo_dado_selecionado', None)
    if tipo_escolhido is None:
        # fallback: oferecer o selectbox localmente para compatibilidade
        tipo_escolhido = st.selectbox('Tipo de dado', ('Ingressantes', 'Concluintes', 'Matriculados'), index=0, key='analise_geral_tipo')
        st.info('Usando seleção local porque o filtro lateral não está definido.')

    st.markdown(f"### Evolução Temporal - {tipo_escolhido} Pretos vs Outros")

    evolucao = preparar_dados_temporais(df, tipo=tipo_escolhido)

    if evolucao.empty:
        st.info("Não há dados temporais suficientes para plotar as séries.")
        return

    # Garantir ordenação por ano
    evolucao = evolucao.sort_values('nu_ano_censo')

    # Organizar os três gráficos lado a lado: Evolução da Representatividade, Comparação (Abs), Taxa de Crescimento
    cols = st.columns(3)

    # Gráfico 1: Evolução percentual
    fig_percentual = go.Figure()
    fig_percentual.add_trace(go.Scatter(x=evolucao['nu_ano_censo'], y=evolucao['percent_black'], mode='lines+markers', name='Pretos (%)', line=dict(color='#e74c3c', width=3), marker=dict(size=6)))
    fig_percentual.add_trace(go.Scatter(x=evolucao['nu_ano_censo'], y=evolucao['percent_other'], mode='lines+markers', name='Outros (%)', line=dict(color='#3498db', width=3), marker=dict(size=6)))
    fig_percentual.update_layout(title_text='Evolução da Representatividade (%)', xaxis_title='Ano', yaxis_title='Representatividade (%)')
    with cols[0]:
        st.plotly_chart(fig_percentual, use_container_width=True, key='analise_geral_percentual')

    # Gráfico 3: Comparação em linha (números absolutos)
    fig_comparison = go.Figure()
    fig_comparison.add_trace(go.Scatter(x=evolucao['nu_ano_censo'], y=evolucao['black_sel'], mode='lines+markers', name='Pretos (Abs)', line=dict(color='#e74c3c', width=2)))
    fig_comparison.add_trace(go.Scatter(x=evolucao['nu_ano_censo'], y=evolucao['other_sel'], mode='lines+markers', name='Outros (Abs)', line=dict(color='#3498db', width=2)))
    fig_comparison.update_layout(title_text=f'Comparação: Pretos vs Outros ({tipo_escolhido} - Números Absolutos)', xaxis_title='Ano', yaxis_title='Número de Entrantes')
    with cols[1]:
        st.plotly_chart(fig_comparison, use_container_width=True, key='analise_geral_comparison')

    # Gráfico 4: Taxa de crescimento anual
    if len(evolucao) > 1:
        taxa_crescimento_np = evolucao['black_sel'].pct_change() * 100
        taxa_crescimento_outros = evolucao['other_sel'].pct_change() * 100

        fig_growth_rate = go.Figure()
        fig_growth_rate.add_trace(go.Bar(x=evolucao['nu_ano_censo'][1:], y=taxa_crescimento_np[1:], name=f'Pretos (%)', marker_color='#e74c3c', opacity=0.8))
        fig_growth_rate.add_trace(go.Bar(x=evolucao['nu_ano_censo'][1:], y=taxa_crescimento_outros[1:], name=f'Outros (%)', marker_color='#3498db', opacity=0.8))
        fig_growth_rate.update_layout(title_text=f'Taxa de Crescimento Anual (%) - {tipo_escolhido}', xaxis_title='Ano', yaxis_title='Taxa de Crescimento (%)', barmode='group')
        with cols[2]:
            st.plotly_chart(fig_growth_rate, use_container_width=True, key='analise_geral_growth')

    # Tabela de dados
    st.markdown('### Dados da Evolução Temporal')
    evolucao_display = evolucao[['nu_ano_censo', 'total_sel', 'black_sel', 'other_sel', 'percent_black', 'percent_other']].copy()
    evolucao_display.columns = ['Ano', 'Total', 'Pretos', 'Outros', 'Representatividade (%) - Pretos', 'Representatividade (%) - Outros']
    evolucao_display = evolucao_display.round(1)
    st.dataframe(evolucao_display, use_container_width=True)
