
import streamlit as st
import pandas as pd
import plotly.express as px

def analise_institucional_page():
    st.title("Análise por Tipo de Instituição")

    if 'data' not in st.session_state or st.session_state['data'].empty:
        st.warning("Dados não carregados. Por favor, retorne à página inicial.")
        return

    df = st.session_state['data']
    ano_selecionado = st.session_state.get('ano_selecionado', df['nu_ano_censo'].max())
    tipo_dado_selecionado = st.session_state.get('tipo_dado_selecionado', 'Ingressantes')

    st.header(f"Representatividade de {tipo_dado_selecionado} por Tipo de Instituição - Ano: {ano_selecionado}")

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

    df_filtrado = df[df['nu_ano_censo'] == ano_selecionado].copy()

    if not df_filtrado.empty:
        # Mapear códigos para nomes descritivos
        map_instituicao = {
            1: 'Pública Federal',
            2: 'Pública Estadual',
            3: 'Pública Municipal',
            4: 'Privada com fins lucrativos',
            5: 'Privada sem fins lucrativos',
            6: 'Privada - Particular em sentido estrito',
            7: 'Especial',
            8: 'Privada comunitária',
            9: 'Privada confessional'
        }
        df_filtrado['tipo_instituicao_descricao'] = df_filtrado['tp_categoria_administrativa'].map(map_instituicao)

        # Agrupar tipos em 'Pública' e 'Privada' (qualquer descrição que não comece com 'Pública' será considerada 'Privada'; 'Especial' fica como 'Privada')
        def classificar_pub_priv(desc):
            try:
                if isinstance(desc, str) and desc.strip().lower().startswith('pública'):
                    return 'Pública'
                # Tratar explicitamente 'Especial' como 'Privada'
                if isinstance(desc, str) and desc.strip().lower() == 'especial':
                    return 'Privada'
                if isinstance(desc, str) and desc.strip() != '':
                    # Qualquer outro texto é considerado 'Privada'
                    return 'Privada'
            except Exception:
                pass
            return 'Outro'

        df_filtrado['grupo_admin'] = df_filtrado['tipo_instituicao_descricao'].apply(classificar_pub_priv)

        # Agregação simplificada por Pública vs Privada
        inst_pubpriv = df_filtrado.groupby('grupo_admin').agg({
            coluna_total: 'sum',
            coluna_negros_pardos: 'sum'
        }).reset_index()

        inst_pubpriv['percentual'] = (inst_pubpriv[coluna_negros_pardos] / inst_pubpriv[coluna_total] * 100).round(2)

        # Garantir ordem (Pública, Privada, Outro)
        ordem = ['Pública', 'Privada', 'Outro']
        inst_pubpriv['grupo_admin'] = pd.Categorical(inst_pubpriv['grupo_admin'], categories=ordem, ordered=True)
        inst_pubpriv = inst_pubpriv.sort_values('grupo_admin')

        st.subheader(f"Representatividade de Pretos ({tipo_dado_selecionado}) - Pública vs Privada")
        fig_pubpriv = px.bar(
            inst_pubpriv,
            x='grupo_admin',
            y='percentual',
            color='percentual',
            color_continuous_scale='Plasma',
            title=f'Representatividade de Pretos ({tipo_dado_selecionado}) - Pública vs Privada em {ano_selecionado}',
            labels={
                'grupo_admin': 'Categoria Administrativa',
                'percentual': 'Representatividade (%)'
            }
        )
        st.plotly_chart(fig_pubpriv, use_container_width=True, key=f"institucional_pubpriv_{ano_selecionado}_{tipo_dado_selecionado}")

        # Agrupar por tipo de instituição
        inst_agrupado = df_filtrado.groupby('tipo_instituicao_descricao').agg({
            coluna_total: 'sum',
            coluna_negros_pardos: 'sum'
        }).reset_index()

        inst_agrupado['percentual_negros_pardos'] = (
            inst_agrupado[coluna_negros_pardos] / inst_agrupado[coluna_total] * 100
        ).round(2)

        inst_agrupado = inst_agrupado.sort_values('percentual_negros_pardos', ascending=False)

        st.subheader(f"Representatividade de Pretos ({tipo_dado_selecionado}) por Tipo de Instituição")
        fig_inst = px.bar(
            inst_agrupado,
            x='tipo_instituicao_descricao',
            y='percentual_negros_pardos',
            color='percentual_negros_pardos',
            color_continuous_scale='Plasma',
            title=f'Representatividade de Pretos ({tipo_dado_selecionado}) por Tipo de Instituição em {ano_selecionado}',
            labels={
                'tipo_instituicao_descricao': 'Tipo de Instituição',
                'percentual_negros_pardos': 'Representatividade (%)'
            }
        )
        import uuid
        chart_key = f"institucional_bar_{ano_selecionado}_{tipo_dado_selecionado}_{uuid.uuid4()}"
        st.plotly_chart(fig_inst, use_container_width=True, key=chart_key)

        st.subheader("Evolução da Representatividade por Tipo de Instituição ao Longo dos Anos")
        # Dados para evolução temporal por tipo de instituição
        inst_evolution = df.groupby(['nu_ano_censo', 'tp_categoria_administrativa']).agg({
            coluna_total: 'sum',
            coluna_negros_pardos: 'sum'
        }).reset_index()
        inst_evolution['tipo_instituicao_descricao'] = inst_evolution['tp_categoria_administrativa'].map(map_instituicao)

        inst_evolution['percentual_negros_pardos'] = (
            inst_evolution[coluna_negros_pardos] / inst_evolution[coluna_total] * 100
        ).round(2)

        # Agrupar a evolução por Pública vs Privada (usar a função classificar_pub_priv definida acima)
        inst_evolution = inst_evolution.dropna(subset=['tipo_instituicao_descricao']).copy()
        inst_evolution['grupo_admin'] = inst_evolution['tipo_instituicao_descricao'].apply(classificar_pub_priv)

        inst_evol_grouped = inst_evolution.groupby(['nu_ano_censo', 'grupo_admin']).agg({
            coluna_total: 'sum',
            coluna_negros_pardos: 'sum'
        }).reset_index()

        inst_evol_grouped['percentual'] = (
            inst_evol_grouped[coluna_negros_pardos] / inst_evol_grouped[coluna_total] * 100
        ).round(2)

        # Garantir ordem de categorias
        inst_evol_grouped['grupo_admin'] = pd.Categorical(inst_evol_grouped['grupo_admin'], categories=['Pública', 'Privada', 'Outro'], ordered=True)

        fig_inst_evol = px.line(
            inst_evol_grouped,
            x='nu_ano_censo',
            y='percentual',
            color='grupo_admin',
            title=f'Evolução da Representatividade de Pretos ({tipo_dado_selecionado}) - Pública vs Privada',
            labels={
                'nu_ano_censo': 'Ano',
                'percentual': 'Representatividade (%)',
                'grupo_admin': 'Categoria'
            },
            markers=True
        )
        st.plotly_chart(fig_inst_evol, use_container_width=True, key=f"institucional_evol_pubpriv_{tipo_dado_selecionado}")
    else:
        st.info(f"Não há dados disponíveis para o ano {ano_selecionado} e tipo de dado {tipo_dado_selecionado}.")

# Nota: a função `analise_institucional_page` é chamada a partir de `app.py`.

