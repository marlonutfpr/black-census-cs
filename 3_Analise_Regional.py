
import streamlit as st
import pandas as pd
import plotly.express as px
from i18n import t

def analise_regional_page():
    st.title(t("regional_title"))

    if 'data' not in st.session_state or st.session_state['data'].empty:
        st.warning(t("data_not_loaded"))
        return

    df = st.session_state['data']
    ano_selecionado = st.session_state.get('ano_selecionado', df['nu_ano_censo'].max())
    tipo_dado_selecionado = st.session_state.get('tipo_dado_selecionado', 'Ingressantes')

    st.header(t("regional_header", dtype=tipo_dado_selecionado, year=ano_selecionado))

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

    df_ano = df[df['nu_ano_censo'] == ano_selecionado].copy()

    if not df_ano.empty:
        # Agrupar por região
        regional_data = df_ano.groupby('no_regiao').agg({
            coluna_total: 'sum',
            coluna_negros_pardos: 'sum'
        }).reset_index()

        regional_data['percentual_negros_pardos'] = (
            regional_data[coluna_negros_pardos] / regional_data[coluna_total] * 100
        ).round(2)

        regional_data = regional_data.sort_values('percentual_negros_pardos', ascending=False)

        st.subheader(t("regional_bar_sub", dtype=tipo_dado_selecionado))
        fig_regional = px.bar(
            regional_data,
            x='no_regiao',
            y='percentual_negros_pardos',
            color='percentual_negros_pardos',
            color_continuous_scale='Viridis',
            title=t("regional_bar_title", dtype=tipo_dado_selecionado, year=ano_selecionado),
            labels={
                'no_regiao': t("region"),
                'percentual_negros_pardos': t("representativeness")
            }
        )
        st.plotly_chart(fig_regional, use_container_width=True)

        st.subheader(t("regional_evol_sub"))
        # Dados para evolução temporal por região
        regional_evolution = df.groupby(['nu_ano_censo', 'no_regiao']).agg({
            coluna_total: 'sum',
            coluna_negros_pardos: 'sum'
        }).reset_index()

        regional_evolution['percentual_negros_pardos'] = (
            regional_evolution[coluna_negros_pardos] / regional_evolution[coluna_total] * 100
        ).round(2)

        fig_regional_evol = px.line(
            regional_evolution,
            x='nu_ano_censo',
            y='percentual_negros_pardos',
            color='no_regiao',
            title=t("regional_evol_title", dtype=tipo_dado_selecionado),
            labels={
                'nu_ano_censo': t("year"),
                'percentual_negros_pardos': t("representativeness"),
                'no_regiao': t("region")
            },
            markers=True
        )
        st.plotly_chart(fig_regional_evol, use_container_width=True)

        # Mapa de calor: matriz 2D (Regiões x Anos) com percentual de Pretos
        st.subheader(t("regional_heatmap_sub"))
        heatmap_df = regional_evolution.pivot(index='no_regiao', columns='nu_ano_censo', values='percentual_negros_pardos').fillna(0)

        # Ordenar colunas (anos) e linhas (regiões) para apresentação consistente
        heatmap_df = heatmap_df.reindex(sorted(heatmap_df.columns), axis=1)
        heatmap_df = heatmap_df.reindex(sorted(heatmap_df.index), axis=0)

        # Usar px.imshow para criar o heatmap
        fig_heatmap = px.imshow(
            heatmap_df,
            labels=dict(x=t("year"), y=t("region"), color=t("representativeness")),
            x=heatmap_df.columns.astype(str),
            y=heatmap_df.index,
            color_continuous_scale='Turbo',
            aspect='auto',
            origin='lower',
            title=t("regional_heatmap_title", dtype=tipo_dado_selecionado)
        )

        # Ajustes visuais: exibir valores no hover
        fig_heatmap.update_traces(hovertemplate='Região: %{y}<br>Ano: %{x}<br>Representatividade: %{z:.2f}%')

        st.plotly_chart(fig_heatmap, use_container_width=True, key=f"regional_heatmap_{tipo_dado_selecionado}")

    else:
        st.info(t("no_data_year", year=ano_selecionado, dtype=tipo_dado_selecionado))

# Nota: a função `analise_regional_page` é chamada a partir de `app.py`.

