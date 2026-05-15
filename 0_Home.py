import streamlit as st
from i18n import t

_CSS = """
<style>
/* ── variáveis de tema ────────────────────────────────────────────── */
:root {
    --dash-title-color:      #1a1a2e;
    --dash-subtitle-color:   #444444;
    --dash-card-bg:          #ffffff;
    --dash-card-border:      #d0d0d0;
    --dash-card-title-color: #1a1a2e;
    --dash-card-text-color:  #333333;
    --dash-footer-color:     #666666;
    --dash-footer-link:      #1a73e8;
}

@media (prefers-color-scheme: dark) {
    :root {
        --dash-title-color:      #e8e8f5;
        --dash-subtitle-color:   #b0b8cc;
        --dash-card-bg:          #1e2130;
        --dash-card-border:      #3a4060;
        --dash-card-title-color: #f0f0ff;
        --dash-card-text-color:  #c8cce0;
        --dash-footer-color:     #9099b0;
        --dash-footer-link:      #7ab4f5;
    }
}

.dash-title {
    text-align: center;
    color: var(--dash-title-color);
    font-size: 2rem;
    line-height: 1.3;
    margin-bottom: 0.3rem;
}
.dash-subtitle {
    text-align: center;
    font-size: 1.1rem;
    color: var(--dash-subtitle-color);
    margin-top: 0;
    margin-bottom: 1rem;
}
.dash-card {
    border: 1px solid var(--dash-card-border);
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 12px;
    background: var(--dash-card-bg);
}
.dash-card h4 {
    margin: 0 0 6px 0;
    color: var(--dash-card-title-color);
    font-size: 1rem;
}
.dash-card p {
    margin: 0;
    color: var(--dash-card-text-color);
    font-size: 0.93rem;
    line-height: 1.5;
}
.dash-footer {
    text-align: center;
    color: var(--dash-footer-color);
    font-size: 0.85rem;
    margin-top: 0.5rem;
}
.dash-footer a {
    color: var(--dash-footer-link);
    text-decoration: none;
}
</style>
"""


def home_page():
    st.markdown(_CSS, unsafe_allow_html=True)

    # ── Cabeçalho ─────────────────────────────────────────────────────────────
    st.markdown(
        """
        <h1 class='dash-title'>
            {t('home_main_title')}
        </h1>
        <p class='dash-subtitle'>
            {t('home_subtitle')}
        </p>
        <hr>
        """,
        unsafe_allow_html=True,
    )

    # ── Sobre o dashboard ─────────────────────────────────────────────────────
    st.markdown(f"## {t('home_about_title')}")
    col_text, col_info = st.columns([2, 1])

    with col_text:
        st.markdown(t("home_about_body"))

    with col_info:
        st.info(t("home_source"))

    st.markdown("---")

    # ── Contexto e motivação ──────────────────────────────────────────────────
    st.markdown(f"## {t('home_context_title')}")
    st.markdown(t("home_context_body"))

    st.markdown("---")

    # ── Análises disponíveis ──────────────────────────────────────────────────
    st.markdown(f"## {t('home_pages_title')}")

    pages_info = [
        {"icon": "📈", "title": t("page_overview").split(" ", 1)[1],  "desc": t("home_card_overview_desc")},
        {"icon": "🎓", "title": t("page_by_course").split(" ", 1)[1], "desc": t("home_card_course_desc")},
        {"icon": "🗺️", "title": t("page_regional").split(" ", 1)[1],  "desc": t("home_card_regional_desc")},
        {"icon": "🏛️", "title": t("page_institutional").split(" ", 1)[1], "desc": t("home_card_inst_desc")},
        {"icon": "🖥️", "title": t("page_format").split(" ", 1)[1],    "desc": t("home_card_format_desc")},
        {"icon": "⚖️", "title": t("page_general").split(" ", 1)[1],   "desc": t("home_card_general_desc")},
        {"icon": "🔮", "title": t("page_projection").split(" ", 1)[1],"desc": t("home_card_proj_desc")},
    ]

    # Grade 2 × N de cartões
    for i in range(0, len(pages_info), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            if i + j < len(pages_info):
                p = pages_info[i + j]
                col.markdown(
                    f"""
                    <div class='dash-card'>
                        <h4>{p['icon']} {p['title']}</h4>
                        <p>{p['desc']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    # ── Como usar ─────────────────────────────────────────────────────────────
    st.markdown(f"## {t('home_how_title')}")
    st.markdown(t("home_how_body"))

    st.markdown("---")

    # ── Rodapé ────────────────────────────────────────────────────────────────
    st.markdown(
        f"<p class='dash-footer'>{t('home_footer')}</p>",
        unsafe_allow_html=True,
    )
