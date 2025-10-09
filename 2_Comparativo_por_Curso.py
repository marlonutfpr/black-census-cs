
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def comparativo_curso_page():
    st.title("Comparativo por Curso")

    if 'data' not in st.session_state or st.session_state['data'].empty:
        st.warning("Dados não carregados. Por favor, retorne à página inicial.")
        return

    df = st.session_state['data']
    ano_selecionado = st.session_state.get('ano_selecionado', df['nu_ano_censo'].max())
    tipo_dado_selecionado = st.session_state.get('tipo_dado_selecionado', 'Ingressantes')

    st.header(f"Comparativo de {tipo_dado_selecionado} por Curso - Ano: {ano_selecionado}")

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
        # Padronizar nomes de cursos (função do notebook)
        def standardize_course_name(course_name):
            return str(course_name).upper().strip()

        df_ano['no_curso_upper'] = df_ano['no_curso'].apply(standardize_course_name)
        df_ano['no_curso_standardized'] = df_ano['no_curso_upper'].apply(standardize_course_name)

        # Agrupar por curso (usando a coluna padronizada) e somar
        comparativo_curso = df_ano.groupby('no_curso_standardized').agg({
            coluna_total: 'sum',
            coluna_negros_pardos: 'sum'
        }).reset_index()

        comparativo_curso['percentual_negros_pardos'] = (
            comparativo_curso[coluna_negros_pardos] / comparativo_curso[coluna_total] * 100
        ).round(1)

        # Renomear colunas para melhor legibilidade
        tabela_cursos = comparativo_curso.rename(columns={
            'no_curso_standardized': 'Curso',
            coluna_total: f'Total {tipo_dado_selecionado}',
            coluna_negros_pardos: f'Pretos {tipo_dado_selecionado}',
            'percentual_negros_pardos': 'Representatividade (%)'
        })

        tabela_cursos = tabela_cursos.sort_values(f'Total {tipo_dado_selecionado}', ascending=False)

        st.subheader(f"Tabela de {tipo_dado_selecionado} por Curso")
        st.dataframe(tabela_cursos)

        # Gráfico de pizza para os top N cursos
        top_n = st.slider("Número de Cursos para o Gráfico de Pizza", 5, 20, 10, key="comparativo_curso_page_top_n_slider")

        # Filtrar cursos com valores maiores que 0 para evitar erros no gráfico
        tabela_cursos_filtrada = tabela_cursos[tabela_cursos[f'Pretos {tipo_dado_selecionado}'] > 0]

        if not tabela_cursos_filtrada.empty:
            top_cursos_para_pizza = tabela_cursos_filtrada.head(top_n)
            outros_cursos = tabela_cursos_filtrada.iloc[top_n:]

            if not outros_cursos.empty:
                total_outros = outros_cursos[f'Pretos {tipo_dado_selecionado}'].sum()
                outros_row = pd.DataFrame([{
                    'Curso': 'Outros Cursos',
                    f'Total {tipo_dado_selecionado}': outros_cursos[f'Total {tipo_dado_selecionado}'].sum(),
                    f'Pretos {tipo_dado_selecionado}': total_outros,
                    'Representatividade (%)': (total_outros / outros_cursos[f'Total {tipo_dado_selecionado}'].sum() * 100).round(1) if outros_cursos[f'Total {tipo_dado_selecionado}'].sum() > 0 else 0
                }])
                dados_pizza = pd.concat([top_cursos_para_pizza, outros_row], ignore_index=True)
            else:
                dados_pizza = top_cursos_para_pizza

            fig_pizza = px.pie(
                dados_pizza,
                values=f'Pretos {tipo_dado_selecionado}',
                names='Curso',
                title=f'Distribuição de Pretos ({tipo_dado_selecionado}) por Curso (Top {top_n} + Outros) em {ano_selecionado}',
                hole=0.3
            )
            st.plotly_chart(fig_pizza, use_container_width=True)
        else:
            st.info(f"Não há dados de Pretos para {tipo_dado_selecionado} para gerar o gráfico de pizza neste ano.")

    else:
        st.info(f"Não há dados disponíveis para o ano {ano_selecionado} e tipo de dado {tipo_dado_selecionado}.")


# Nota: a função `comparativo_curso_page` é chamada a partir de `app.py`.

