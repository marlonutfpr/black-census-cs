
import streamlit as st
import pandas as pd
import plotly.express as px

def analise_regional_page():
    st.title("Análise Regional")

    if 'data' not in st.session_state or st.session_state['data'].empty:
        st.warning("Dados não carregados. Por favor, retorne à página inicial.")
        return

    df = st.session_state['data']
    ano_selecionado = st.session_state.get('ano_selecionado', df['nu_ano_censo'].max())
    tipo_dado_selecionado = st.session_state.get('tipo_dado_selecionado', 'Ingressantes')

    st.header(f"Representatividade de Pretos ({tipo_dado_selecionado}) por Região - Ano: {ano_selecionado}")

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

        st.subheader(f"Representatividade de Pretos ({tipo_dado_selecionado}) por Região")
        fig_regional = px.bar(
            regional_data,
            x='no_regiao',
            y='percentual_negros_pardos',
            color='percentual_negros_pardos',
            color_continuous_scale='Viridis',
                title=f'Representatividade de Pretos ({tipo_dado_selecionado}) por Região em {ano_selecionado}',
            labels={
                'no_regiao': 'Região',
                'percentual_negros_pardos': 'Representatividade (%)'
            }
        )
        st.plotly_chart(fig_regional, use_container_width=True)

        st.subheader("Evolução da Representatividade por Região ao Longo dos Anos")
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
                title=f'Evolução da Representatividade de Pretos ({tipo_dado_selecionado}) por Região',
            labels={
                'nu_ano_censo': 'Ano',
                'percentual_negros_pardos': 'Representatividade (%)',
                'no_regiao': 'Região'
            },
            markers=True
        )
        st.plotly_chart(fig_regional_evol, use_container_width=True)

        # Mapa de calor: matriz 2D (Regiões x Anos) com percentual de Pretos
        st.subheader("Mapa de Calor: Representatividade por Região ao Longo dos Anos")
        heatmap_df = regional_evolution.pivot(index='no_regiao', columns='nu_ano_censo', values='percentual_negros_pardos').fillna(0)

        # Ordenar colunas (anos) e linhas (regiões) para apresentação consistente
        heatmap_df = heatmap_df.reindex(sorted(heatmap_df.columns), axis=1)
        heatmap_df = heatmap_df.reindex(sorted(heatmap_df.index), axis=0)

        # Usar px.imshow para criar o heatmap
        fig_heatmap = px.imshow(
            heatmap_df,
            labels=dict(x="Ano", y="Região", color="Representatividade (%)"),
            x=heatmap_df.columns.astype(str),
            y=heatmap_df.index,
            color_continuous_scale='Turbo',
            aspect='auto',
            origin='lower',
            title=f'Mapa de Calor - Representatividade de Pretos ({tipo_dado_selecionado}) por Região x Ano'
        )

        # Ajustes visuais: exibir valores no hover
        fig_heatmap.update_traces(hovertemplate='Região: %{y}<br>Ano: %{x}<br>Representatividade: %{z:.2f}%')

        st.plotly_chart(fig_heatmap, use_container_width=True, key=f"regional_heatmap_{tipo_dado_selecionado}")

    else:
        st.info(f"Não há dados disponíveis para o ano {ano_selecionado} e tipo de dado {tipo_dado_selecionado}.")

# Nota: a função `analise_regional_page` é chamada a partir de `app.py`.

