
import streamlit as st
import pandas as pd
import plotly.express as px
import hashlib
import colorsys

def comparativo_geral_page():
    st.title("Comparativo Geral")

    if 'data' not in st.session_state or st.session_state['data'].empty:
        st.warning("Dados não carregados. Por favor, retorne à página inicial.")
        return

    df = st.session_state['data']
    ano_selecionado = st.session_state.get('ano_selecionado', df['nu_ano_censo'].max())

    st.header(f"Comparação de Dados para o Ano: {ano_selecionado}")

    # Opções de tipo de dado para comparação
    tipos_dados_opcoes = {
        'Ingressantes': 'qt_ing',
        'Concluintes': 'qt_conc',
        'Matriculados': 'qt_mat'
    }
    tipos_dados_negros_pardos_opcoes = {
        'Ingressantes': 'qt_ing_preta',
        'Concluintes': 'qt_conc_preta',
        'Matriculados': 'qt_mat_preta'
    }

    # Não precisamos mais selecionar apenas dois tipos; iremos mostrar os três
    st.sidebar.subheader("Configurações de Comparação")
    st.sidebar.markdown("Mostrando: Ingressantes, Concluintes e Matriculados")

    # Seleção do grupo para comparação
    grupo_comparacao_opcoes = {
        'Região': 'no_regiao',
        'Tipo de Instituição': 'tp_categoria_administrativa',
        'Curso': 'no_curso_standardized',
        'Formato': 'formato_ensino'
    }
    grupo_selecionado_label = st.sidebar.selectbox(
        "Comparar por Grupo",
        list(grupo_comparacao_opcoes.keys()),
        index=0
    )
    grupo_selecionado_col = grupo_comparacao_opcoes[grupo_selecionado_label]

    df_ano = df[df['nu_ano_censo'] == ano_selecionado].copy()

    if not df_ano.empty:
        # Mapear códigos para nomes descritivos se for tipo de instituição
        # Mapear tipos de dado para colunas (usado nos casos especiais)
        tipos_dados_opcoes = {
            'Ingressantes': 'qt_ing',
            'Concluintes': 'qt_conc',
            'Matriculados': 'qt_mat'
        }
        tipos_dados_negros_pardos_opcoes = {
            'Ingressantes': 'qt_ing_preta',
            'Concluintes': 'qt_conc_preta',
            'Matriculados': 'qt_mat_preta'
        }

        # Tratamento especial: Curso
        if grupo_selecionado_label == 'Curso':
            # criar coluna padronizada do curso
            def standardize_course_name(course_name):
                return str(course_name).upper().strip()

            if 'no_curso' in df.columns:
                df_ano['no_curso_upper'] = df_ano['no_curso'].apply(standardize_course_name)
                df_ano['no_curso_standardized'] = df_ano['no_curso_upper'].apply(standardize_course_name)
            else:
                df_ano['no_curso_standardized'] = 'Desconhecido'

            # vamos construir os gráficos de área para os três tipos (Ingressantes, Concluintes, Matriculados)
            # Primeiro, determinar os top10 do último ano com base no total de pretos somando os três tipos (referência)
            try:
                top_n_area = 10
                latest_year = df_time['nu_ano_censo'].max()
                # somar os três tipos de pretos no último ano
                preta_cols = [tipos_dados_negros_pardos_opcoes[t] for t in tipos_dados_opcoes.keys()]
                temp_latest_all = df_time[df_time['nu_ano_censo'] == latest_year].groupby('no_curso_standardized')[preta_cols].sum()
                # soma total de pretos por curso no último ano
                total_latest_all = temp_latest_all.sum(axis=1)
                total_latest_all = total_latest_all[total_latest_all > 0]
                if total_latest_all.empty:
                    # fallback: usar total acumulado (soma de pretos em todo o período)
                    total_by_course = df_time.groupby('no_curso_standardized')[preta_cols].sum().sum(axis=1)
                    total_by_course = total_by_course[total_by_course > 0]
                    top_courses_overall = total_by_course.nlargest(top_n_area).index.tolist() if not total_by_course.empty else []
                else:
                    top_courses_overall = total_latest_all.nlargest(top_n_area).index.tolist()
            except Exception:
                top_courses_overall = []
            # Mostrar gráficos de pizza lado a lado para os três tipos: Ingressantes, Concluintes, Matriculados
            top_n = st.slider('Top N cursos para os gráficos de pizza', 5, 30, 10, key='comparativo_geral_curso_top_n')

            pies = {}
            series = {}
            for nome, col in tipos_dados_opcoes.items():
                col_pretos = tipos_dados_negros_pardos_opcoes[nome]
                df_temp = df_ano.groupby('no_curso_standardized').agg(
                    total_geral=(col, 'sum'),
                    total_pretos=(col_pretos, 'sum')
                ).reset_index()
                df_temp = df_temp[df_temp['total_geral'] > 0]
                df_temp[f'percentual_pretos_{nome}'] = (df_temp['total_pretos'] / df_temp['total_geral'] * 100).round(2)
                df_temp = df_temp.sort_values('total_geral', ascending=False)
                series[nome] = df_temp

                top = df_temp.head(top_n).copy()
                others = df_temp.iloc[top_n:]
                if not others.empty:
                    outros_row = pd.DataFrame([{
                        'no_curso_standardized': 'Outros Cursos',
                        'total_geral': others['total_geral'].sum(),
                        'total_pretos': others['total_pretos'].sum()
                    }])
                    pie_df = pd.concat([top[['no_curso_standardized', 'total_pretos']], outros_row[['no_curso_standardized', 'total_pretos']]], ignore_index=True)
                else:
                    pie_df = top[['no_curso_standardized', 'total_pretos']]

                pies[nome] = pie_df

            # --- não plotar as pizzas ainda; iremos construir um mapa de cores consistente e depois desenhar pies e área ---

            # Tabela combinada com os três tipos
            # Mesclar as três séries em um único DataFrame
            combined = series['Ingressantes'][['no_curso_standardized', 'total_geral', 'total_pretos']].rename(columns={'total_geral': 'total_ing', 'total_pretos': 'pretos_ing'})
            combined = combined.merge(series['Concluintes'][['no_curso_standardized', 'total_geral', 'total_pretos']].rename(columns={'total_geral': 'total_conc', 'total_pretos': 'pretos_conc'}), on='no_curso_standardized', how='outer')
            combined = combined.merge(series['Matriculados'][['no_curso_standardized', 'total_geral', 'total_pretos']].rename(columns={'total_geral': 'total_mat', 'total_pretos': 'pretos_mat'}), on='no_curso_standardized', how='outer')
            combined = combined.fillna(0)
            # calcular percentuais (protegendo divisão por zero e substituindo NaN/inf por 0)
            def safe_pct(num, den):
                try:
                    num = pd.to_numeric(num, errors='coerce').fillna(0)
                    den = pd.to_numeric(den, errors='coerce').fillna(0)
                    pct = pd.Series(0.0, index=num.index)
                    nonzero = den != 0
                    pct.loc[nonzero] = (num.loc[nonzero] / den.loc[nonzero] * 100).round(2)
                    return pct.fillna(0)
                except Exception:
                    return pd.Series(0.0, index=num.index)

            combined['pct_pretos_ing'] = safe_pct(combined['pretos_ing'], combined['total_ing'])
            combined['pct_pretos_conc'] = safe_pct(combined['pretos_conc'], combined['total_conc'])
            combined['pct_pretos_mat'] = safe_pct(combined['pretos_mat'], combined['total_mat'])

            st.subheader('Tabela combinada por Curso (Ingressantes / Concluintes / Matriculados)')
            st.dataframe(combined.sort_values('total_ing', ascending=False).rename(columns={'no_curso_standardized': 'Curso'}).head(200))

            # Evolução temporal: área mostrando participação de cada curso no total de pretos por ano
            df_time = df.copy()
            if 'no_curso' in df_time.columns:
                df_time['no_curso_standardized'] = df_time['no_curso'].apply(standardize_course_name)
            else:
                df_time['no_curso_standardized'] = 'Desconhecido'

            tipo_dado = st.session_state.get('tipo_dado_selecionado', 'Ingressantes')
            temp = df_time.groupby(['nu_ano_censo', 'no_curso_standardized']).agg(
                total_pretos=(tipos_dados_negros_pardos_opcoes[tipo_dado], 'sum')
            ).reset_index()

            # remover o ano de 2009 da série temporal conforme solicitado
            temp = temp[temp['nu_ano_censo'] != 2009]

            # escolher top courses com base no último ano disponível (mais relevante para participação atual)
            try:
                top_n_area = 10
                latest_year = temp['nu_ano_censo'].max()
                temp_latest = temp[temp['nu_ano_censo'] == latest_year]
                total_latest = temp_latest.groupby('no_curso_standardized')['total_pretos'].sum()
                # remover cursos com soma zero
                total_latest = total_latest[total_latest > 0]
                if total_latest.empty:
                    # fallback: usar total acumulado caso o último ano não tenha dados
                    total_by_course = temp.groupby('no_curso_standardized')['total_pretos'].sum()
                    total_by_course = total_by_course[total_by_course > 0]
                    top_courses_overall = total_by_course.nlargest(top_n_area).index.tolist() if not total_by_course.empty else []
                else:
                    top_courses_overall = total_latest.nlargest(top_n_area).index.tolist()
            except Exception:
                top_courses_overall = []

            # marcar como 'Outros Cursos' aqueles que não estão no top escolhido
            temp['course_group'] = temp['no_curso_standardized'].where(temp['no_curso_standardized'].isin(top_courses_overall), 'Outros Cursos')

            stacked = temp.groupby(['nu_ano_censo', 'course_group']).agg(total_pretos=('total_pretos', 'sum')).reset_index()
            # calcular participação percentual por ano, protegendo divisão por zero
            total_por_ano = stacked.groupby('nu_ano_censo')['total_pretos'].transform('sum')
            # evitar inf/NaN quando total_por_ano == 0
            stacked['percent'] = 0.0
            nonzero_mask = total_por_ano > 0
            stacked.loc[nonzero_mask, 'percent'] = (stacked.loc[nonzero_mask, 'total_pretos'] / total_por_ano[nonzero_mask] * 100)
            stacked['percent'] = stacked['percent'].fillna(0)

            # construir mapa de cores consistente para cursos (inclui cursos exibidos nas pizzas e no área)
            # coletar nomes de cursos presentes nas pizzas
            courses_in_pies = set()
            for dfp in pies.values():
                if not dfp.empty and 'no_curso_standardized' in dfp.columns:
                    courses_in_pies.update(dfp['no_curso_standardized'].astype(str).tolist())

            # incluir top courses do área
            courses_for_colors = list(courses_in_pies.union(set(top_courses_overall)))

            def name_to_hex(name, s=0.65, l=0.5):
                # deterministic hash -> hue
                try:
                    h = int(hashlib.md5(str(name).encode('utf-8')).hexdigest()[:8], 16) % 360
                except Exception:
                    h = abs(hash(str(name))) % 360
                r, g, b = colorsys.hls_to_rgb(h/360.0, l, s)
                return '#%02x%02x%02x' % (int(r*255), int(g*255), int(b*255))

            color_map = {}
            for cname in courses_for_colors:
                if cname == 'Outros Cursos':
                    color_map[cname] = '#BDBDBD'
                else:
                    color_map[cname] = name_to_hex(cname)

            # garantir que 'Outros Cursos' tenha cor se ainda não estiver
            if 'Outros Cursos' not in color_map:
                color_map['Outros Cursos'] = '#BDBDBD'

            # desenhar as pizzas usando o mesmo mapa de cores
            cols = st.columns(3)
            tipos_ord = list(tipos_dados_opcoes.keys())
            for i, nome in enumerate(tipos_ord):
                with cols[i]:
                    title = f'Pretos ({nome}) por Curso - Top {top_n} + Outros ({ano_selecionado})'
                    fig = px.pie(pies[nome], names='no_curso_standardized', values='total_pretos', title=title, hole=0.3, color='no_curso_standardized', color_discrete_map=color_map)
                    st.plotly_chart(fig, use_container_width=True, key=f'comparativo_geral_curso_pie_{nome}')

            # omitimos o gráfico agregado único para evitar duplicação; exibiremos os três gráficos por tipo abaixo

            # Desenhar as três áreas (Ingressantes, Concluintes, Matriculados) uma abaixo da outra
            tipos_para_area = list(tipos_dados_opcoes.keys())
            if 'stacked_dict' not in locals():
                # reconstruir stacked_dict caso não exista (defensivo)
                stacked_dict = {}
                for nome in tipos_para_area:
                    temp_tipo = df_time.groupby(['nu_ano_censo', 'no_curso_standardized']).agg(
                        total_pretos=(tipos_dados_negros_pardos_opcoes[nome], 'sum')
                    ).reset_index()
                    temp_tipo = temp_tipo[temp_tipo['nu_ano_censo'] != 2009]
                    temp_tipo['course_group'] = temp_tipo['no_curso_standardized'].where(temp_tipo['no_curso_standardized'].isin(top_courses_overall), 'Outros Cursos')
                    stacked_tmp = temp_tipo.groupby(['nu_ano_censo', 'course_group']).agg(total_pretos=('total_pretos', 'sum')).reset_index()
                    total_por_ano_tmp = stacked_tmp.groupby('nu_ano_censo')['total_pretos'].transform('sum')
                    stacked_tmp['percent'] = 0.0
                    nonzero_mask_tmp = total_por_ano_tmp > 0
                    stacked_tmp.loc[nonzero_mask_tmp, 'percent'] = (stacked_tmp.loc[nonzero_mask_tmp, 'total_pretos'] / total_por_ano_tmp[nonzero_mask_tmp] * 100)
                    stacked_tmp['percent'] = stacked_tmp['percent'].fillna(0)
                    stacked_dict[nome] = stacked_tmp

            for idx, nome in enumerate(tipos_para_area):
                stacked_tmp = stacked_dict.get(nome)
                if stacked_tmp is None or stacked_tmp.empty:
                    st.info(f"Sem dados para {nome} ao longo do tempo.")
                    continue
                fig_tmp = px.area(stacked_tmp.sort_values(['nu_ano_censo', 'course_group']), x='nu_ano_censo', y='percent', color='course_group', labels={'percent': 'Participação (%)', 'nu_ano_censo': 'Ano', 'course_group': 'Curso'}, title=f'Participação dos Cursos no Total de Pretos ({nome}) ao Longo do Tempo', color_discrete_map=color_map)
                st.plotly_chart(fig_tmp, use_container_width=True, key=f'comparativo_geral_curso_area_{idx}_{nome}')

            return

        # Tratamento especial: Formato
        if grupo_selecionado_label == 'Formato':
            # detectar coluna de modalidade e criar formato_ensino
            possible_modal_cols = [
                'tp_modalidade', 'in_presencial', 'modalidade', 'tp_modalidade_ensino',
                'forma_ensino', 'no_modalidade', 'in_modalidade', 'tp_forma_ensino'
            ]
            modal_col = None
            for c in possible_modal_cols:
                if c in df.columns:
                    modal_col = c
                    break

            def map_formato(val):
                if pd.isna(val):
                    return 'Outro'
                s = str(val).strip().lower()
                if any(k in s for k in ['dist', 'ead', 'a distância', 'a distancia', 'à distância']):
                    return 'A Distância'
                if any(k in s for k in ['pres', 'presencial']):
                    return 'Presencial'
                try:
                    n = int(float(s))
                    if n == 1:
                        return 'Presencial'
                    if n == 2:
                        return 'A Distância'
                except Exception:
                    pass
                return 'Outro'

            if modal_col is not None:
                df_ano['formato_ensino'] = df_ano[modal_col].apply(map_formato)
                df['formato_ensino'] = df[modal_col].apply(map_formato)
            else:
                df_ano['formato_ensino'] = 'Outro'
                df['formato_ensino'] = 'Outro'

            # Calcular representatividade para os três tipos de dado (Ingressantes, Concluintes, Matriculados)
            series = {}
            for nome, col in tipos_dados_opcoes.items():
                temp = df_ano.groupby('formato_ensino').agg(
                    total_geral=(col, 'sum'),
                    total_pretos=(tipos_dados_negros_pardos_opcoes[nome], 'sum')
                ).reset_index()
                # calcular representatividade protegendo divisão por zero
                temp[f'Representatividade {nome} (%)'] = 0.0
                nonzero_mask_temp = temp['total_geral'] != 0
                if nonzero_mask_temp.any():
                    temp.loc[nonzero_mask_temp, f'Representatividade {nome} (%)'] = (temp.loc[nonzero_mask_temp, 'total_pretos'] / temp.loc[nonzero_mask_temp, 'total_geral'] * 100).round(2)
                series[nome] = temp[['formato_ensino', f'Representatividade {nome} (%)']]

            # Mesclar em um único DataFrame para barras lado a lado
            comparativo_fmt = series['Ingressantes']
            comparativo_fmt = comparativo_fmt.merge(series['Concluintes'], on='formato_ensino', how='outer')
            comparativo_fmt = comparativo_fmt.merge(series['Matriculados'], on='formato_ensino', how='outer')
            comparativo_fmt = comparativo_fmt.fillna(0)

            st.subheader(f'Representatividade por Formato (lado a lado) - {ano_selecionado}')
            fig_bar = px.bar(
                comparativo_fmt,
                x='formato_ensino',
                y=[f'Representatividade Ingressantes (%)', f'Representatividade Concluintes (%)', f'Representatividade Matriculados (%)'],
                barmode='group',
                labels={'value': 'Representatividade (%)', 'variable': 'Tipo de Dado', 'formato_ensino': 'Formato'},
                title=f'Representatividade de Pretos por Formato em {ano_selecionado}'
            )
            st.plotly_chart(fig_bar, use_container_width=True, key='comparativo_geral_formato_bar')

            st.subheader('Tabela por Formato')
            st.dataframe(comparativo_fmt.sort_values(f'Representatividade Ingressantes (%)', ascending=False))

            # Evolução temporal por formato para cada tipo de dado (linhas facetas)
            rows = []
            for nome, col in tipos_dados_opcoes.items():
                temp = df.groupby(['nu_ano_censo', 'formato_ensino']).agg(
                    total_geral=(col, 'sum'),
                    total_pretos=(tipos_dados_negros_pardos_opcoes[nome], 'sum')
                ).reset_index()
                temp['percentual'] = 0.0
                nonzero_mask_temp = temp['total_geral'] != 0
                if nonzero_mask_temp.any():
                    temp.loc[nonzero_mask_temp, 'percentual'] = (temp.loc[nonzero_mask_temp, 'total_pretos'] / temp.loc[nonzero_mask_temp, 'total_geral'] * 100).round(2)
                temp['tipo'] = nome
                rows.append(temp[['nu_ano_censo', 'formato_ensino', 'tipo', 'percentual']])

            if rows:
                long_time = pd.concat(rows, ignore_index=True)
                st.subheader('Evolução Temporal por Formato e Tipo de Dado')
                fig_evo = px.line(
                    long_time,
                    x='nu_ano_censo',
                    y='percentual',
                    color='formato_ensino',
                    facet_col='tipo',
                    facet_col_wrap=3,
                    labels={'nu_ano_censo': 'Ano', 'percentual': 'Representatividade (%)', 'formato_ensino': 'Formato'},
                    title='Evolução da Representatividade por Formato',
                    markers=True
                )
                fig_evo.update_layout(legend_title_text='Formato')
                st.plotly_chart(fig_evo, use_container_width=True, key='comparativo_geral_formato_line')

            return

        # --- fim tratamentos especiais ---
        if grupo_selecionado_col == 'tp_categoria_administrativa':
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
            df_ano['grupo_descricao'] = df_ano[grupo_selecionado_col].map(map_instituicao)

            # Classificar em Pública / Privada (seguir mesma lógica da análise institucional)
            def classificar_pub_priv(desc):
                try:
                    if isinstance(desc, str) and desc.strip().lower().startswith('pública'):
                        return 'Pública'
                    if isinstance(desc, str) and desc.strip().lower() == 'especial':
                        return 'Privada'
                    if isinstance(desc, str) and desc.strip() != '':
                        return 'Privada'
                except Exception:
                    pass
                return 'Outro'

            df_ano['grupo_admin'] = df_ano['grupo_descricao'].apply(classificar_pub_priv)
            coluna_agrupamento = 'grupo_admin'
        else:
            coluna_agrupamento = grupo_selecionado_col

        # Calcular representatividade para os três tipos de dados
        series = {}
        for nome, col in tipos_dados_opcoes.items():
            temp = df_ano.groupby(coluna_agrupamento).agg(
                total_geral=(col, 'sum'),
                total_negros_pardos=(tipos_dados_negros_pardos_opcoes[nome], 'sum')
            ).reset_index()
            # calcular representatividade protegendo divisão por zero
            temp[f'Representatividade {nome} (%)'] = 0.0
            nonzero_mask_local = temp['total_geral'] != 0
            if nonzero_mask_local.any():
                temp.loc[nonzero_mask_local, f'Representatividade {nome} (%)'] = (temp.loc[nonzero_mask_local, 'total_negros_pardos'] / temp.loc[nonzero_mask_local, 'total_geral'] * 100).round(2)
            series[nome] = temp[[coluna_agrupamento, f'Representatividade {nome} (%)']]

        # Mesclar as três séries em um único DataFrame
        comparativo = series['Ingressantes']
        comparativo = comparativo.merge(series['Concluintes'], on=coluna_agrupamento, how='outer')
        comparativo = comparativo.merge(series['Matriculados'], on=coluna_agrupamento, how='outer')
        comparativo = comparativo.fillna(0)

        st.subheader(f"Comparação de Representatividade de Pretos por {grupo_selecionado_label}")
        fig_comparativo = px.bar(
            comparativo,
            x=coluna_agrupamento,
            y=[f'Representatividade Ingressantes (%)', f'Representatividade Concluintes (%)', f'Representatividade Matriculados (%)'],
            barmode='group',
            title=f'Comparativo de Representatividade de Pretos por {grupo_selecionado_label} em {ano_selecionado}',
            labels={
                coluna_agrupamento: grupo_selecionado_label,
                'value': 'Representatividade (%)',
                'variable': 'Tipo de Dado'
            }
        )
        st.plotly_chart(fig_comparativo, use_container_width=True)

        st.subheader("Tabela Comparativa")
        # Ordenar por Ingressantes por padrão
        sort_col = 'Representatividade Ingressantes (%)' if 'Representatividade Ingressantes (%)' in comparativo.columns else comparativo.columns[1]
        # Preparar cópia para exibição e renomear rótulo da coluna de região quando aplicável
        comparativo_display = comparativo.sort_values(sort_col, ascending=False).copy()
        if coluna_agrupamento == 'no_regiao' and 'no_regiao' in comparativo_display.columns:
            comparativo_display = comparativo_display.rename(columns={'no_regiao': 'Nome da Região'})
        st.dataframe(comparativo_display)

        # Comparativo temporal por Tipo de Instituição (Pública vs Privada)
        if grupo_selecionado_col == 'tp_categoria_administrativa':
            # Recriar mapa de códigos -> descrição
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

            def classificar_pub_priv(desc):
                try:
                    if isinstance(desc, str) and desc.strip().lower().startswith('pública'):
                        return 'Pública'
                    if isinstance(desc, str) and desc.strip().lower() == 'especial':
                        return 'Privada'
                    if isinstance(desc, str) and desc.strip() != '':
                        return 'Privada'
                except Exception:
                    pass
                return 'Outro'

            df_time = df.copy()
            df_time['grupo_descricao'] = df_time['tp_categoria_administrativa'].map(map_instituicao)
            df_time['grupo_admin'] = df_time['grupo_descricao'].apply(classificar_pub_priv)

            # Construir série temporal long-form para os três tipos
            rows = []
            for nome, col in tipos_dados_opcoes.items():
                temp = df_time.groupby(['nu_ano_censo', 'grupo_admin']).agg(
                    total_geral=(col, 'sum'),
                    total_negros_pardos=(tipos_dados_negros_pardos_opcoes[nome], 'sum')
                ).reset_index()
                temp['percentual'] = 0.0
                nonzero_mask_local = temp['total_geral'] != 0
                if nonzero_mask_local.any():
                    temp.loc[nonzero_mask_local, 'percentual'] = (temp.loc[nonzero_mask_local, 'total_negros_pardos'] / temp.loc[nonzero_mask_local, 'total_geral'] * 100).round(2)
                temp['tipo'] = nome
                rows.append(temp[['nu_ano_censo', 'grupo_admin', 'tipo', 'percentual']])

            if rows:
                long_time = pd.concat(rows, ignore_index=True)
                # Garantir ordem das categorias
                long_time['grupo_admin'] = pd.Categorical(long_time['grupo_admin'], categories=['Pública', 'Privada', 'Outro'], ordered=True)

                st.subheader('Evolução Temporal - Pública vs Privada por Tipo de Dado')
                fig_time = px.line(
                    long_time,
                    x='nu_ano_censo',
                    y='percentual',
                    color='grupo_admin',
                    facet_col='tipo',
                    facet_col_wrap=3,
                    title=f'Evolução da Representatividade por Categoria Administrativa - Pública vs Privada',
                    labels={
                        'nu_ano_censo': 'Ano',
                        'percentual': 'Representatividade (%)',
                        'grupo_admin': 'Categoria'
                    },
                    markers=True
                )
                fig_time.update_layout(legend_title_text='Categoria')
                st.plotly_chart(fig_time, use_container_width=True, key='comparativo_geral_evol_pubpriv')

        # Comparativo temporal por Região
        if grupo_selecionado_col == 'no_regiao':
            df_time = df.copy()
            df_time['regiao'] = df_time['no_regiao'].dropna()

            rows = []
            for nome, col in tipos_dados_opcoes.items():
                temp = df_time.groupby(['nu_ano_censo', 'regiao']).agg(
                    total_geral=(col, 'sum'),
                    total_negros_pardos=(tipos_dados_negros_pardos_opcoes[nome], 'sum')
                ).reset_index()
                temp['percentual'] = 0.0
                nonzero_mask_local = temp['total_geral'] != 0
                if nonzero_mask_local.any():
                    temp.loc[nonzero_mask_local, 'percentual'] = (temp.loc[nonzero_mask_local, 'total_negros_pardos'] / temp.loc[nonzero_mask_local, 'total_geral'] * 100).round(2)
                temp['tipo'] = nome
                rows.append(temp[['nu_ano_censo', 'regiao', 'tipo', 'percentual']])

            if rows:
                long_time_reg = pd.concat(rows, ignore_index=True)
                # Garantir ordem das regiões (alfabética)
                long_time_reg['regiao'] = pd.Categorical(long_time_reg['regiao'], categories=sorted(long_time_reg['regiao'].unique()), ordered=True)

                st.subheader('Evolução Temporal por Região e Tipo de Dado')
                fig_reg_time = px.line(
                    long_time_reg,
                    x='nu_ano_censo',
                    y='percentual',
                    color='regiao',
                    facet_col='tipo',
                    facet_col_wrap=3,
                    title=f'Evolução da Representatividade por Região',
                    labels={
                        'nu_ano_censo': 'Ano',
                        'percentual': 'Representatividade (%)',
                        'regiao': 'Região'
                    },
                    markers=True
                )
                fig_reg_time.update_layout(legend_title_text='Região')
                st.plotly_chart(fig_reg_time, use_container_width=True, key='comparativo_geral_evol_regiao')

    else:
        st.info(f"Não há dados disponíveis para o ano {ano_selecionado}.")

# Nota: a função `comparativo_geral_page` é chamada a partir de `app.py`.

