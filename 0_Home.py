import streamlit as st


def home_page():
    # ── Cabeçalho ─────────────────────────────────────────────────────────────
    st.markdown(
        """
        <h1 style='text-align:center; color:#1a1a2e;'>
            📊 Representatividade de Estudantes Negros<br>nos Cursos de Computação no Brasil
        </h1>
        <p style='text-align:center; font-size:1.1rem; color:#555;'>
            Análise do Censo da Educação Superior &nbsp;|&nbsp; 2009 – 2023
        </p>
        <hr>
        """,
        unsafe_allow_html=True,
    )

    # ── Sobre o dashboard ─────────────────────────────────────────────────────
    st.markdown("## Sobre este Dashboard")
    col_text, col_info = st.columns([2, 1])

    with col_text:
        st.markdown(
            """
            Este dashboard foi desenvolvido para analisar de forma aprofundada a
            **representatividade de estudantes autodeclarados pretos** nos cursos de
            Computação das instituições de ensino superior brasileiras.

            Os dados provêm do **Censo da Educação Superior** (INEP/MEC), cobrindo
            **15 anos consecutivos** (2009 a 2023), e permitem acompanhar como essa
            população se posiciona nas etapas de **ingresso**, **matrícula** e
            **conclusão** dos cursos.

            A análise é realizada em múltiplas dimensões: temporal, regional,
            institucional e por tipo de curso, oferecendo uma visão abrangente
            das desigualdades ainda existentes e das tendências ao longo do tempo.
            """
        )

    with col_info:
        st.info(
            """
            **Fonte dos dados**
            Censo da Educação Superior
            INEP / MEC

            **Período coberto**
            2009 a 2023

            **Área analisada**
            Cursos de Computação
            (graduação presencial e EaD)

            **Recorte racial**
            Cor/raça *preta* (IBGE)
            """
        )

    st.markdown("---")

    # ── Contexto e motivação ──────────────────────────────────────────────────
    st.markdown("## Contexto e Motivação")
    st.markdown(
        """
        Apesar de representarem mais de **10% da população brasileira** segundo o IBGE,
        estudantes autodeclarados *pretos* historicamente ocupam uma parcela
        desproporcional das vagas nos cursos de tecnologia. Compreender essa dinâmica
        é o primeiro passo para promover políticas de inclusão efetivas.

        O dashboard cruza dados de **ingresso**, **matrícula** e **conclusão** por
        raça/cor ao longo dos anos, permitindo identificar:

        - Se houve avanço na entrada de estudantes negros após marcos como a
          **Lei de Cotas (Lei 12.711/2012)**;
        - Quais regiões e estados apresentam maior ou menor representatividade;
        - Como diferentes tipos de instituição (pública × privada) se comportam;
        - Se a retenção e conclusão acompanham o crescimento no ingresso.
        """
    )

    st.markdown("---")

    # ── Análises disponíveis ──────────────────────────────────────────────────
    st.markdown("## Análises Disponíveis")

    pages_info = [
        {
            "icon": "📈",
            "title": "Visão Geral",
            "desc": (
                "Evolução temporal da representatividade de estudantes pretos em todos "
                "os cursos de Computação, comparando ingressantes, matriculados e concluintes "
                "ao longo dos 15 anos de dados."
            ),
        },
        {
            "icon": "🎓",
            "title": "Comparativo por Curso",
            "desc": (
                "Distribuição da representatividade por nome de curso (Ciência da Computação, "
                "Sistemas de Informação, Engenharia de Computação, etc.), revelando quais "
                "cursos concentram mais ou menos diversidade racial."
            ),
        },
        {
            "icon": "🗺️",
            "title": "Análise Regional",
            "desc": (
                "Mapa e ranking das cinco regiões brasileiras, mostrando como a presença de "
                "estudantes pretos varia entre Norte, Nordeste, Centro-Oeste, Sudeste e Sul."
            ),
        },
        {
            "icon": "🏛️",
            "title": "Análise Institucional",
            "desc": (
                "Comparação entre categorias administrativas (federal, estadual, municipal e "
                "privada), indicando qual tipo de instituição é mais inclusivo no recorte "
                "racial analisado."
            ),
        },
        {
            "icon": "🖥️",
            "title": "Comparativo por Formato",
            "desc": (
                "Análise da modalidade de ensino — presencial versus EaD — e como cada "
                "formato se diferencia em termos de representatividade de estudantes pretos."
            ),
        },
        {
            "icon": "⚖️",
            "title": "Comparativo Geral",
            "desc": (
                "Visão consolidada que reúne todas as dimensões, permitindo cruzar recortes "
                "temporais, regionais e institucionais em um único painel comparativo."
            ),
        },
        {
            "icon": "🔮",
            "title": "Projeção e Tendências",
            "desc": (
                "Modelagem estatística (regressão linear) das tendências históricas para "
                "projetar o percentual esperado de estudantes pretos nos próximos anos, "
                "com intervalo de confiança."
            ),
        },
    ]

    # Grade 2 × N de cartões
    for i in range(0, len(pages_info), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            if i + j < len(pages_info):
                p = pages_info[i + j]
                col.markdown(
                    f"""
                    <div style='
                        border: 1px solid #e0e0e0;
                        border-radius: 10px;
                        padding: 18px 20px;
                        margin-bottom: 12px;
                        background: #fafafa;
                    '>
                        <h4 style='margin:0 0 6px 0'>{p['icon']} {p['title']}</h4>
                        <p style='margin:0; color:#444; font-size:0.93rem'>{p['desc']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    # ── Como usar ─────────────────────────────────────────────────────────────
    st.markdown("## Como Usar")
    st.markdown(
        """
        1. **Selecione a análise** desejada no menu lateral em *Selecione a Página*.
        2. Use o **slider de ano** para filtrar um ano específico nas visualizações por corte temporal.
        3. Escolha o **tipo de dado** — *Ingressantes*, *Concluintes* ou *Matriculados* — para
           alternar entre as diferentes etapas da jornada acadêmica.
        4. Todas as análises se atualizam automaticamente com os filtros selecionados.
        5. Os gráficos são **interativos**: passe o mouse para ver detalhes, clique na legenda
           para ocultar séries, e use o zoom para explorar intervalos específicos.
        """
    )

    st.markdown("---")

    # ── Rodapé ────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <p style='text-align:center; color:#888; font-size:0.85rem;'>
            Dados: INEP — Censo da Educação Superior &nbsp;|&nbsp;
            Desenvolvido com <a href='https://streamlit.io' target='_blank'>Streamlit</a>
        </p>
        """,
        unsafe_allow_html=True,
    )
