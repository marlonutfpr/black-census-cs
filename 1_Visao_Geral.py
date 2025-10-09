import streamlit as st
import pandas as pd
import plotly.express as px
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

def visao_geral_page():
    st.title("Visão Geral e Evolução Temporal")

    if 'data' not in st.session_state or st.session_state['data'].empty:
        st.warning("Dados não carregados. Por favor, retorne à página inicial.")
        return

    df = st.session_state['data']

    ano_selecionado = st.session_state.get('ano_selecionado', df['nu_ano_censo'].max())
    tipo_dado_selecionado = st.session_state.get('tipo_dado_selecionado', 'Ingressantes')

    st.header(f"Dados para {tipo_dado_selecionado} - Ano: {ano_selecionado}")

    # Mapeamento do tipo de dado para as colunas do DataFrame
    coluna_total = {
        'Ingressantes': 'qt_ing',
        'Concluintes': 'qt_conc',
        'Matriculados': 'qt_mat'
    }[tipo_dado_selecionado]

    coluna_negros_pardos = {
        'Ingressantes': 'qt_ing_preta',
        'Concluintes': 'qt_conc_preta',
        'Matriculados': 'qt_mat_preta'
    }[tipo_dado_selecionado]

    # Resumo anual
    resumo_anual = df.groupby('nu_ano_censo').agg(
        total_geral=(coluna_total, 'sum'),
        total_negros_pardos=(coluna_negros_pardos, 'sum')
    ).reset_index()

    resumo_anual['percentual_negros_pardos'] = (
        resumo_anual['total_negros_pardos'] / resumo_anual['total_geral'] * 100
    ).round(2)

    # Garantir que 'nu_ano_censo' é numérico para ordenação/plot
    if 'nu_ano_censo' in resumo_anual.columns:
        try:
            resumo_anual['nu_ano_censo'] = pd.to_numeric(resumo_anual['nu_ano_censo'], errors='coerce')
        except Exception:
            pass

    st.subheader("Evolução da Representatividade de Pretos ao Longo dos Anos")
    try:
        if resumo_anual.empty:
            st.info('Resumo anual vazio: não há dados agregados por ano para esse tipo de dado.')
        else:
            fig_evolucao = px.line(
                resumo_anual.sort_values('nu_ano_censo'),
                x='nu_ano_censo',
                y='percentual_negros_pardos',
                title=f'Representatividade de Pretos ({tipo_dado_selecionado})',
                labels={
                    'nu_ano_censo': 'Ano',
                    'percentual_negros_pardos': 'Representatividade (%)'
                },
                markers=True
            )
            st.plotly_chart(fig_evolucao, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao renderizar figura de evolução: {e}")

    st.subheader(f"Dados Detalhados para o Ano {ano_selecionado}")
    df_ano = df[df['nu_ano_censo'] == ano_selecionado].copy()

    if not df_ano.empty:
        total_geral_ano = df_ano[coluna_total].sum()
        total_negros_pardos_ano = df_ano[coluna_negros_pardos].sum()
        percentual_ano = (total_negros_pardos_ano / total_geral_ano * 100).round(2) if total_geral_ano > 0 else 0

        st.metric(
            label=f"Representatividade de Pretos ({tipo_dado_selecionado}) em {ano_selecionado}",
            value=f"{percentual_ano:.2f}%",
            delta=None # Poderia ser a diferença em relação ao ano anterior, se implementado
        )

        st.write(f"Total de {tipo_dado_selecionado} em {ano_selecionado}: {int(total_geral_ano):,}")
        st.write(f"Total de Pretos ({tipo_dado_selecionado}) em {ano_selecionado}: {int(total_negros_pardos_ano):,}")

        st.subheader("Comparativo de Representatividade por Raça/Cor")
        # Tentar agregar por colunas de cor específicas (ex.: qt_ing_preta, qt_ing_parda, ...)
        cor_suffixes = ['preta', 'parda', 'amarela', 'indigena', 'branca', 'cornd']
        # Construir nomes de colunas esperados para o tipo selecionado
        cols_por_cor = [f"{coluna_total}_{s}" for s in cor_suffixes]

        available_cols = [c for c in cols_por_cor if c in df_ano.columns]

        if available_cols:
            # Somar por cor usando as colunas encontradas
            soma_por_cor = {}
            for c in available_cols:
                # extrair sufixo (cor) para rótulo legível
                cor_label = c.replace(f"{coluna_total}_", '')
                soma_por_cor[cor_label] = int(df_ano[c].sum())

            df_raca_ano = pd.DataFrame({
                'tp_cor_raca': list(soma_por_cor.keys()),
                'total': list(soma_por_cor.values())
            })
            total_sum = df_raca_ano['total'].sum() if not df_raca_ano.empty else 0
            if total_sum > 0:
                df_raca_ano['percentual'] = (df_raca_ano['total'] / total_sum * 100).round(2)
            else:
                df_raca_ano['percentual'] = 0.0

            fig_raca = px.pie(
                df_raca_ano,
                values='total',
                names='tp_cor_raca',
                title=f'Distribuição de {tipo_dado_selecionado} por Raça/Cor em {ano_selecionado}',
                hole=0.3
            )
            st.plotly_chart(fig_raca, use_container_width=True)
            # Gráfico de área (percentual) por cor ao longo do tempo — usa colunas por cor encontradas
            try:
                # Agregar por ano usando as mesmas colunas por cor
                df_year = df[['nu_ano_censo'] + available_cols].groupby('nu_ano_censo').sum().reset_index()
                # garantir ordenação e conversão
                try:
                    df_year['nu_ano_censo'] = pd.to_numeric(df_year['nu_ano_censo'], errors='coerce')
                except Exception:
                    pass
                df_year = df_year.sort_values('nu_ano_censo').reset_index(drop=True)

                # transformar em formato long e calcular percentuais por ano
                df_m = df_year.melt(id_vars='nu_ano_censo', value_vars=available_cols, var_name='cor', value_name='quantidade')
                df_m['total_ano'] = df_m.groupby('nu_ano_censo')['quantidade'].transform('sum')
                # proteger divisão por zero
                df_m['percentual'] = df_m.apply(lambda r: (r['quantidade'] / r['total_ano'] * 100) if r['total_ano'] > 0 else 0, axis=1)
                df_m['cor'] = df_m['cor'].str.replace(f"{coluna_total}_", '', regex=False).str.capitalize()

                fig_area_pct = px.area(
                    df_m.sort_values('nu_ano_censo'),
                    x='nu_ano_censo',
                    y='percentual',
                    color='cor',
                    title=f'Participação percentual por Cor/Raça ao longo do tempo ({tipo_dado_selecionado})',
                    labels={'nu_ano_censo': 'Ano', 'percentual': 'Participação (%)', 'cor': 'Cor/Raça'}
                )
                fig_area_pct.update_layout(legend_title_text='Cor/Raça', yaxis=dict(range=[0,100]))
                st.plotly_chart(fig_area_pct, use_container_width=True)
            except Exception as e:
                st.warning(f'Não foi possível gerar gráfico de área percentual por cor: {e}')
        else:
            # Fallback: usar coluna categórica 'tp_cor_raca' se disponível
            if 'tp_cor_raca' in df_ano.columns:
                df_raca_ano = df_ano.groupby('tp_cor_raca').agg(total=(coluna_total, 'sum')).reset_index()
                total_sum = df_raca_ano['total'].sum() if not df_raca_ano.empty else 0
                if total_sum > 0:
                    df_raca_ano['percentual'] = (df_raca_ano['total'] / total_sum * 100).round(2)
                else:
                    df_raca_ano['percentual'] = 0.0

                fig_raca = px.pie(
                    df_raca_ano,
                    values='total',
                    names='tp_cor_raca',
                    title=f'Distribuição de {tipo_dado_selecionado} por Raça/Cor em {ano_selecionado}',
                    hole=0.3
                )
                st.plotly_chart(fig_raca, use_container_width=True)
                # Gráfico de área (percentual) por cor usando 'tp_cor_raca' ao longo do tempo
                try:
                    # pivot anual: linhas=nu_ano_censo, colunas=tp_cor_raca
                    df_pivot = df.groupby(['nu_ano_censo', 'tp_cor_raca']).agg({coluna_total: 'sum'}).reset_index()
                    df_pivot = df_pivot.pivot(index='nu_ano_censo', columns='tp_cor_raca', values=coluna_total).fillna(0).reset_index()
                    # converter anos
                    try:
                        df_pivot['nu_ano_censo'] = pd.to_numeric(df_pivot['nu_ano_censo'], errors='coerce')
                    except Exception:
                        pass
                    df_pivot = df_pivot.sort_values('nu_ano_censo')
                    # melt e calcular percentuais por ano
                    cols_tp = [c for c in df_pivot.columns if c != 'nu_ano_censo']
                    df_m2 = df_pivot.melt(id_vars='nu_ano_censo', value_vars=cols_tp, var_name='cor', value_name='quantidade')
                    df_m2['total_ano'] = df_m2.groupby('nu_ano_censo')['quantidade'].transform('sum')
                    df_m2['percentual'] = df_m2.apply(lambda r: (r['quantidade'] / r['total_ano'] * 100) if r['total_ano'] > 0 else 0, axis=1)

                    fig_area_pct2 = px.area(
                        df_m2.sort_values('nu_ano_censo'),
                        x='nu_ano_censo',
                        y='percentual',
                        color='cor',
                        title=f'Participação percentual por Cor/Raça ao longo do tempo ({tipo_dado_selecionado})',
                        labels={'nu_ano_censo': 'Ano', 'percentual': 'Participação (%)', 'cor': 'Cor/Raça'}
                    )
                    fig_area_pct2.update_layout(legend_title_text='Cor/Raça', yaxis=dict(range=[0,100]))
                    st.plotly_chart(fig_area_pct2, use_container_width=True)
                except Exception as e:
                    st.warning(f'Não foi possível gerar gráfico de área percentual usando tp_cor_raca: {e}')
            else:
                st.info("Não há colunas por cor (qt_*_preta, _parda, ...) nem a coluna 'tp_cor_raca' disponível nos dados para este ano. Não é possível exibir o comparativo por raça/cor.")

    else:
        st.info(f"Não há dados disponíveis para o ano {ano_selecionado} e tipo de dado {tipo_dado_selecionado}.")

    # Análises temporais detalhadas (Pretos vs Outros)
    st.markdown(f"### Evolução Temporal Detalhada - {tipo_dado_selecionado} Pretos vs Outros")
    evolucao = preparar_dados_temporais(df, tipo=tipo_dado_selecionado)

    if evolucao.empty:
        st.info("Não há dados temporais suficientes para comparação Pretos vs Outros.")
    else:
        evolucao = evolucao.sort_values('nu_ano_censo')
        cols = st.columns(3)

        # Gráfico 1: Evolução percentual
        fig_percentual = go.Figure()
        fig_percentual.add_trace(go.Scatter(x=evolucao['nu_ano_censo'], y=evolucao['percent_black'], mode='lines+markers', name='Pretos (%)', line=dict(color='#e74c3c', width=3), marker=dict(size=6)))
        fig_percentual.add_trace(go.Scatter(x=evolucao['nu_ano_censo'], y=evolucao['percent_other'], mode='lines+markers', name='Outros (%)', line=dict(color='#3498db', width=3), marker=dict(size=6)))
        fig_percentual.update_layout(title_text='Evolução da Representatividade (%)', xaxis_title='Ano', yaxis_title='Representatividade (%)')
        with cols[0]:
            st.plotly_chart(fig_percentual, use_container_width=True)

        # Gráfico 2: Comparação absoluta
        fig_comparison = go.Figure()
        fig_comparison.add_trace(go.Scatter(x=evolucao['nu_ano_censo'], y=evolucao['black_sel'], mode='lines+markers', name='Pretos (Abs)', line=dict(color='#e74c3c', width=2)))
        fig_comparison.add_trace(go.Scatter(x=evolucao['nu_ano_censo'], y=evolucao['other_sel'], mode='lines+markers', name='Outros (Abs)', line=dict(color='#3498db', width=2)))
        fig_comparison.update_layout(title_text=f'Comparação: Pretos vs Outros ({tipo_dado_selecionado})', xaxis_title='Ano', yaxis_title='Contagem')
        with cols[1]:
            st.plotly_chart(fig_comparison, use_container_width=True)

        # Gráfico 3: Taxa de crescimento anual
        if len(evolucao) > 1:
            taxa_crescimento_np = evolucao['black_sel'].pct_change() * 100
            taxa_crescimento_outros = evolucao['other_sel'].pct_change() * 100

            fig_growth_rate = go.Figure()
            fig_growth_rate.add_trace(go.Bar(x=evolucao['nu_ano_censo'][1:], y=taxa_crescimento_np[1:], name='Pretos (%)', marker_color='#e74c3c', opacity=0.8))
            fig_growth_rate.add_trace(go.Bar(x=evolucao['nu_ano_censo'][1:], y=taxa_crescimento_outros[1:], name='Outros (%)', marker_color='#3498db', opacity=0.8))
            fig_growth_rate.update_layout(title_text=f'Taxa de Crescimento Anual (%) - {tipo_dado_selecionado}', xaxis_title='Ano', yaxis_title='Taxa de Crescimento (%)', barmode='group')
            with cols[2]:
                st.plotly_chart(fig_growth_rate, use_container_width=True)

        st.markdown('### Dados da Evolução Temporal')
        evolucao_display = evolucao[['nu_ano_censo', 'total_sel', 'black_sel', 'other_sel', 'percent_black', 'percent_other']].copy()
        evolucao_display.columns = ['Ano', 'Total', 'Pretos', 'Outros', 'Representatividade (%) - Pretos', 'Representatividade (%) - Outros']
        evolucao_display = evolucao_display.round(1)
        st.dataframe(evolucao_display, use_container_width=True)


# Nota: a função `visao_geral_page` é chamada a partir de `app.py`.

