import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# tentamos importar scipy, se não estiver disponível, avisamos e não rodamos a regressão
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except Exception:
    SCIPY_AVAILABLE = False


def preparar_temporal_para_projecao(df: pd.DataFrame, tipo: str = 'Ingressantes') -> pd.DataFrame:
    """
    Retorna DataFrame com colunas 'nu_ano_censo' e 'percentual_black' para o tipo selecionado.
    """
    tipos_map = {
        'Ingressantes': ('qt_ing', 'qt_ing_preta'),
        'Concluintes': ('qt_conc', 'qt_conc_preta'),
        'Matriculados': ('qt_mat', 'qt_mat_preta')
    }
    total_col, black_col = tipos_map.get(tipo, ('qt_ing', 'qt_ing_preta'))

    df_local = df.copy()
    if total_col in df_local.columns:
        df_local[total_col] = pd.to_numeric(df_local[total_col], errors='coerce').fillna(0)
    else:
        df_local[total_col] = 0

    if black_col in df_local.columns:
        df_local[black_col] = pd.to_numeric(df_local[black_col], errors='coerce').fillna(0)
    else:
        df_local[black_col] = 0
        st.warning(f"Coluna '{black_col}' não encontrada. A projeção será baseada em zeros.")

    total = df_local.groupby('nu_ano_censo')[total_col].sum().reset_index().rename(columns={total_col: 'total'})
    black = df_local.groupby('nu_ano_censo')[black_col].sum().reset_index().rename(columns={black_col: 'black'})
    combined = pd.merge(total, black, on='nu_ano_censo', how='left').fillna(0)
    combined['percent'] = 0.0
    nonzero = combined['total'] != 0
    if nonzero.any():
        combined.loc[nonzero, 'percent'] = (combined.loc[nonzero, 'black'] / combined.loc[nonzero, 'total'] * 100).round(2)
    return combined[['nu_ano_censo', 'percent']]


def projecao_page():
    st.title('Projeção e Tendências')

    if 'data' not in st.session_state or st.session_state['data'].empty:
        st.warning('Dados não carregados. Por favor, retorne à página inicial.')
        return

    df = st.session_state['data']
    tipo = st.session_state.get('tipo_dado_selecionado', 'Ingressantes')

    st.markdown(f'## Projeção para: {tipo}')

    temporal = preparar_temporal_para_projecao(df, tipo=tipo)
    if temporal.empty:
        st.info('Sem dados temporais disponíveis para projeção.')
        return

    anos = temporal['nu_ano_censo'].astype(int).tolist()
    perc = temporal['percent'].astype(float).tolist()

    if not SCIPY_AVAILABLE:
        st.error('O pacote scipy não está disponível. Instale via `pip install scipy` para habilitar regressão linear e projeções.')
        st.dataframe(temporal)
        return

    # regressão linear
    try:
        slope, intercept, r_value, p_value, std_err = stats.linregress(anos, perc)
    except Exception as e:
        st.error(f'Erro ao calcular regressão: {e}')
        return

    # projeções
    max_ano = max(anos)
    anos_futuros = list(range(min(anos), max_ano + 4))
    projecao = [slope * ano + intercept for ano in anos_futuros]
    anos_projecao = [ano for ano in anos_futuros if ano > max_ano]
    valores_projecao = [slope * ano + intercept for ano in anos_projecao]

    # meta populacional (padrão) - usar valor da session_state se definido, senão 10.2 (Censo 2022)
    meta_pop = st.session_state.get('meta_pop', 10.2)
    year_paridade = None
    # se houver tendência positiva, estimar ano de paridade e estender projeção até lá
    if slope > 0:
        try:
            anos_para_paridade = (meta_pop - intercept) / slope
            # somente considerar se for após o último ano observado
            if anos_para_paridade is not None:
                ano_paridade_float = anos_para_paridade
                # ano_paridade_float é o valor de 'ano' (não delta); se for > max_ano então haverá paridade no futuro
                # recomputar somente se ano_paridade_float > max_ano
                if ano_paridade_float > max_ano:
                    # arredondar para cima ao ano inteiro
                    ano_paridade_int = int(ano_paridade_float) if float(ano_paridade_float).is_integer() else int(ano_paridade_float) + 1
                    # limitar extensão para evitar horizontes absurdos (cap 100 anos a partir do último ano)
                    cap_ano = max_ano + 100
                    if ano_paridade_int > cap_ano:
                        ano_paridade_int = cap_ano
                    year_paridade = ano_paridade_int
                    # estender a grade de anos futuros até o ano de paridade
                    if year_paridade not in anos_futuros:
                        anos_futuros = list(range(min(anos), year_paridade + 1))
                        projecao = [slope * ano + intercept for ano in anos_futuros]
                        anos_projecao = [ano for ano in anos_futuros if ano > max_ano]
                        valores_projecao = [slope * ano + intercept for ano in anos_projecao]
        except Exception:
            year_paridade = None

    # gráfico de tendência
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=anos, y=perc, mode='markers+lines', name='Histórico', line=dict(color='#e74c3c', width=3), marker=dict(size=8)))
    fig.add_trace(go.Scatter(x=anos_futuros, y=projecao, mode='lines', name=f'Tendência Linear (R²={r_value**2:.3f})', line=dict(color='#3498db', width=2, dash='dash')))
    if anos_projecao:
        fig.add_trace(go.Scatter(x=anos_projecao, y=valores_projecao, mode='markers+lines', name='Projeção Futura', line=dict(color='#f39c12', width=2), marker=dict(size=8, symbol='diamond')))

    # desenhar linha horizontal da meta
    fig.add_trace(go.Scatter(x=anos_futuros, y=[meta_pop] * len(anos_futuros), mode='lines', name=f'Meta populacional ({meta_pop}%)', line=dict(color='#2ecc71', width=2, dash='dot')))

    # marcar o ponto de paridade, se foi estimado
    if year_paridade is not None:
        valor_paridade = slope * year_paridade + intercept
        fig.add_trace(go.Scatter(x=[year_paridade], y=[valor_paridade], mode='markers+text', name='Estimativa de Paridade', marker=dict(color='#2ecc71', size=10, symbol='star'), text=[f'{year_paridade}'], textposition='top center'))

    fig.update_layout(title=f'Tendência e Projeção de Representatividade ({tipo})', xaxis_title='Ano', yaxis_title='Representatividade (%)', height=500)

    # layout: gráfico em uma coluna (esquerda), estatísticas e comparação com a meta na outra (direita)
    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.plotly_chart(fig, use_container_width=True, key='projecao_trend')

    with right_col:
        st.markdown('### Estatísticas da Tendência')
        st.write(f'Coeficiente angular (slope): {slope:.4f} %/ano')
        st.write(f'R²: {r_value**2:.4f}')
        st.write(f'P-valor: {p_value:.6f}')
        st.write(f'Erro padrão: {std_err:.4f}')

        if p_value < 0.05:
            if slope > 0:
                st.success(f'Tendência estatisticamente significativa (p < 0.05). Crescimento estimado de +{slope:.3f}% ao ano.')
            else:
                st.warning(f'Tendência estatisticamente significativa (p < 0.05). Redução estimada de {slope:.3f}% ao ano.')
        else:
            st.info('Tendência não estatisticamente significativa (p ≥ 0.05).')

        # comparação com meta
        atual = perc[-1]
        gap = meta_pop - atual
        st.markdown('### Comparação com meta populacional')
        st.write(f'Meta populacional (Pretos): {meta_pop}% (Censo 2022)')
        st.write(f'Representatividade atual: {atual:.2f}%')
        st.write(f'Gap: {gap:.2f} pontos percentuais')

        if slope > 0 and gap > 0:
            anos_para_paridade = gap / slope
            ano_paridade = max(anos) + anos_para_paridade
            st.write(f'Tempo estimado para paridade: {anos_para_paridade:.1f} anos (aproximadamente no ano {ano_paridade:.0f})')

    # mostrar tabela (largura total)
    st.markdown('### Dados Utilizados')
    # Renomear colunas para exibição amigável
    temporal_display = temporal.copy()
    temporal_display = temporal_display.rename(columns={'nu_ano_censo': 'Ano', 'percent': 'Representatividade (%)'})
    # Garantir formatação
    if 'Representatividade (%)' in temporal_display.columns:
        try:
            temporal_display['Representatividade (%)'] = temporal_display['Representatividade (%)'].astype(float).round(2)
        except Exception:
            pass

    st.dataframe(temporal_display)
