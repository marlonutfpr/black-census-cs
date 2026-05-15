import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from i18n import t

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
        st.warning(t("proj_col_missing", col=black_col))

    total = df_local.groupby('nu_ano_censo')[total_col].sum().reset_index().rename(columns={total_col: 'total'})
    black = df_local.groupby('nu_ano_censo')[black_col].sum().reset_index().rename(columns={black_col: 'black'})
    combined = pd.merge(total, black, on='nu_ano_censo', how='left').fillna(0)
    combined['percent'] = 0.0
    nonzero = combined['total'] != 0
    if nonzero.any():
        combined.loc[nonzero, 'percent'] = (combined.loc[nonzero, 'black'] / combined.loc[nonzero, 'total'] * 100).round(2)
    return combined[['nu_ano_censo', 'percent']]


def projecao_page():
    st.title(t("proj_title"))

    if 'data' not in st.session_state or st.session_state['data'].empty:
        st.warning(t("data_not_loaded"))
        return

    df = st.session_state['data']
    tipo = st.session_state.get('tipo_dado_selecionado', 'Ingressantes')

    st.markdown(f'## {t("proj_for", dtype=tipo)}')

    temporal = preparar_temporal_para_projecao(df, tipo=tipo)
    if temporal.empty:
        st.info(t("proj_no_data"))
        return

    anos = temporal['nu_ano_censo'].astype(int).tolist()
    perc = temporal['percent'].astype(float).tolist()

    if not SCIPY_AVAILABLE:
        st.error(t("proj_scipy_missing"))
        st.dataframe(temporal)
        return

    # regressão linear
    try:
        slope, intercept, r_value, p_value, std_err = stats.linregress(anos, perc)
    except Exception as e:
        st.error(t("proj_regression_error", error=e))
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
    fig.add_trace(go.Scatter(x=anos, y=perc, mode='markers+lines', name=t("proj_history"), line=dict(color='#e74c3c', width=3), marker=dict(size=8)))
    fig.add_trace(go.Scatter(x=anos_futuros, y=projecao, mode='lines', name=t("proj_trend", r2=f'{r_value**2:.3f}'), line=dict(color='#3498db', width=2, dash='dash')))
    if anos_projecao:
        fig.add_trace(go.Scatter(x=anos_projecao, y=valores_projecao, mode='markers+lines', name=t("proj_future"), line=dict(color='#f39c12', width=2), marker=dict(size=8, symbol='diamond')))

    # desenhar linha horizontal da meta
    fig.add_trace(go.Scatter(x=anos_futuros, y=[meta_pop] * len(anos_futuros), mode='lines', name=t("proj_meta", meta=meta_pop), line=dict(color='#2ecc71', width=2, dash='dot')))

    # marcar o ponto de paridade, se foi estimado
    if year_paridade is not None:
        valor_paridade = slope * year_paridade + intercept
        fig.add_trace(go.Scatter(x=[year_paridade], y=[valor_paridade], mode='markers+text', name=t("proj_parity_label"), marker=dict(color='#2ecc71', size=10, symbol='star'), text=[f'{year_paridade}'], textposition='top center'))

    fig.update_layout(title=t("proj_chart_title", dtype=tipo), xaxis_title=t("year"), yaxis_title=t("representativeness"), height=500)

    # layout: gráfico em uma coluna (esquerda), estatísticas e comparação com a meta na outra (direita)
    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.plotly_chart(fig, use_container_width=True, key='projecao_trend')

    with right_col:
        st.markdown(f'### {t("proj_stats_header")}')
        st.write(f'{t("proj_slope")}: {slope:.4f} %/{t("year")}')
        st.write(f'R²: {r_value**2:.4f}')
        st.write(f'{t("proj_pvalue")}: {p_value:.6f}')
        st.write(f'{t("proj_std_err")}: {std_err:.4f}')

        if p_value < 0.05:
            if slope > 0:
                st.success(t("proj_significant_positive", slope=f'{slope:.3f}'))
            else:
                st.warning(t("proj_significant_negative", slope=f'{slope:.3f}'))
        else:
            st.info(t("proj_not_significant"))

        # comparação com meta
        atual = perc[-1]
        gap = meta_pop - atual
        st.markdown(f'### {t("proj_meta_header")}')
        st.write(t("proj_meta_value", meta=meta_pop))
        st.write(t("proj_current", val=f'{atual:.2f}'))
        st.write(t("proj_gap", gap=f'{gap:.2f}'))

        if slope > 0 and gap > 0:
            anos_para_paridade = gap / slope
            ano_paridade = max(anos) + anos_para_paridade
            st.write(t("proj_parity_estimate", years=f'{anos_para_paridade:.1f}', year=f'{ano_paridade:.0f}'))

    # mostrar tabela (largura total)
    st.markdown(f'### {t("proj_data_header")}')
    temporal_display = temporal.copy()
    temporal_display = temporal_display.rename(columns={'nu_ano_censo': t("year"), 'percent': t("representativeness")})
    if t("representativeness") in temporal_display.columns:
        try:
            temporal_display[t("representativeness")] = temporal_display[t("representativeness")].astype(float).round(2)
        except Exception:
            pass

    st.dataframe(temporal_display)
