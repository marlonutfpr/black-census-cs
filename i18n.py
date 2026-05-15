"""
i18n.py — Internacionalização centralizada do dashboard.

Uso:
    from i18n import t, LANGUAGES, set_language, get_language

    t("page_home")          # retorna a string no idioma ativo
"""

import inspect
import streamlit as st

LANGUAGES = {
    "🇧🇷 Português": "pt",
    "🇺🇸 English": "en",
    "🇪🇸 Español": "es",
    "🇫🇷 Français": "fr",
    "🇮🇹 Italiano": "it",
}

_STRINGS: dict[str, dict[str, str]] = {
    # ── Navegação / sidebar ───────────────────────────────────────────────────
    "nav_title": {
        "pt": "Navegação",
        "en": "Navigation",
        "es": "Navegación",
        "fr": "Navigation",
        "it": "Navigazione",
    },
    "nav_select_page": {
        "pt": "Selecione a Página",
        "en": "Select Page",
        "es": "Seleccione la Página",
        "fr": "Sélectionnez la Page",
        "it": "Seleziona la Pagina",
    },
    "nav_select_year": {
        "pt": "Selecione o Ano",
        "en": "Select Year",
        "es": "Seleccione el Año",
        "fr": "Sélectionnez l'Année",
        "it": "Seleziona l'Anno",
    },
    "nav_data_type": {
        "pt": "Tipo de Dado",
        "en": "Data Type",
        "es": "Tipo de Dato",
        "fr": "Type de Donnée",
        "it": "Tipo di Dato",
    },
    "nav_global_filters": {
        "pt": "Filtros Globais",
        "en": "Global Filters",
        "es": "Filtros Globales",
        "fr": "Filtres Globaux",
        "it": "Filtri Globali",
    },
    "nav_language": {
        "pt": "Idioma / Language",
        "en": "Idioma / Language",
        "es": "Idioma / Language",
        "fr": "Idioma / Language",
        "it": "Idioma / Language",
    },
    # ── Nomes das páginas ─────────────────────────────────────────────────────
    "page_home": {
        "pt": "🏠 Página Inicial",
        "en": "🏠 Home",
        "es": "🏠 Inicio",
        "fr": "🏠 Accueil",
        "it": "🏠 Home",
    },
    "page_overview": {
        "pt": "📈 Visão Geral",
        "en": "📈 Overview",
        "es": "📈 Visión General",
        "fr": "📈 Vue d'Ensemble",
        "it": "📈 Panoramica",
    },
    "page_by_course": {
        "pt": "🎓 Comparativo por Curso",
        "en": "🎓 Comparison by Course",
        "es": "🎓 Comparativo por Curso",
        "fr": "🎓 Comparaison par Cours",
        "it": "🎓 Confronto per Corso",
    },
    "page_regional": {
        "pt": "🗺️ Análise Regional",
        "en": "🗺️ Regional Analysis",
        "es": "🗺️ Análisis Regional",
        "fr": "🗺️ Analyse Régionale",
        "it": "🗺️ Analisi Regionale",
    },
    "page_institutional": {
        "pt": "🏛️ Análise Institucional",
        "en": "🏛️ Institutional Analysis",
        "es": "🏛️ Análisis Institucional",
        "fr": "🏛️ Analyse Institutionnelle",
        "it": "🏛️ Analisi Istituzionale",
    },
    "page_format": {
        "pt": "🖥️ Comparativo por Formato",
        "en": "🖥️ Comparison by Format",
        "es": "🖥️ Comparativo por Formato",
        "fr": "🖥️ Comparaison par Format",
        "it": "🖥️ Confronto per Formato",
    },
    "page_projection": {
        "pt": "🔮 Projeção e Tendências",
        "en": "🔮 Projection & Trends",
        "es": "🔮 Proyección y Tendencias",
        "fr": "🔮 Projection et Tendances",
        "it": "🔮 Proiezione e Tendenze",
    },
    "page_general": {
        "pt": "⚖️ Comparativo Geral",
        "en": "⚖️ General Comparison",
        "es": "⚖️ Comparativo General",
        "fr": "⚖️ Comparaison Générale",
        "it": "⚖️ Confronto Generale",
    },
    # ── Tipos de dado ─────────────────────────────────────────────────────────
    "dtype_entrants": {
        "pt": "Ingressantes",
        "en": "Entrants",
        "es": "Ingresantes",
        "fr": "Entrants",
        "it": "Immatricolati",
    },
    "dtype_graduates": {
        "pt": "Concluintes",
        "en": "Graduates",
        "es": "Egresados",
        "fr": "Diplômés",
        "it": "Laureati",
    },
    "dtype_enrolled": {
        "pt": "Matriculados",
        "en": "Enrolled",
        "es": "Matriculados",
        "fr": "Inscrits",
        "it": "Iscritti",
    },
    # ── Strings genéricas ─────────────────────────────────────────────────────
    "year": {"pt": "Ano", "en": "Year", "es": "Año", "fr": "Année", "it": "Anno"},
    "region": {"pt": "Região", "en": "Region", "es": "Región", "fr": "Région", "it": "Regione"},
    "representativeness": {
        "pt": "Representatividade (%)",
        "en": "Representativeness (%)",
        "es": "Representatividad (%)",
        "fr": "Représentativité (%)",
        "it": "Rappresentatività (%)",
    },
    "black_students": {
        "pt": "Pretos",
        "en": "Black Students",
        "es": "Estudiantes Negros",
        "fr": "Étudiants Noirs",
        "it": "Studenti Neri",
    },
    "others": {"pt": "Outros", "en": "Others", "es": "Otros", "fr": "Autres", "it": "Altri"},
    "total": {"pt": "Total", "en": "Total", "es": "Total", "fr": "Total", "it": "Totale"},
    "course": {"pt": "Curso", "en": "Course", "es": "Curso", "fr": "Cours", "it": "Corso"},
    "other_courses": {
        "pt": "Outros Cursos",
        "en": "Other Courses",
        "es": "Otros Cursos",
        "fr": "Autres Cours",
        "it": "Altri Corsi",
    },
    "race_color": {
        "pt": "Cor/Raça",
        "en": "Race/Color",
        "es": "Raza/Color",
        "fr": "Race/Couleur",
        "it": "Razza/Colore",
    },
    "participation_pct": {
        "pt": "Participação (%)",
        "en": "Share (%)",
        "es": "Participación (%)",
        "fr": "Part (%)",
        "it": "Quota (%)",
    },
    "annual_growth": {
        "pt": "Taxa de Crescimento (%)",
        "en": "Growth Rate (%)",
        "es": "Tasa de Crecimiento (%)",
        "fr": "Taux de Croissance (%)",
        "it": "Tasso di Crescita (%)",
    },
    "count": {"pt": "Contagem", "en": "Count", "es": "Conteo", "fr": "Nombre", "it": "Conteggio"},
    "institution_type": {
        "pt": "Tipo de Instituição",
        "en": "Institution Type",
        "es": "Tipo de Institución",
        "fr": "Type d'Institution",
        "it": "Tipo di Istituzione",
    },
    "admin_category": {
        "pt": "Categoria Administrativa",
        "en": "Administrative Category",
        "es": "Categoría Administrativa",
        "fr": "Catégorie Administrative",
        "it": "Categoria Amministrativa",
    },
    "public": {"pt": "Pública", "en": "Public", "es": "Pública", "fr": "Publique", "it": "Pubblica"},
    "private": {"pt": "Privada", "en": "Private", "es": "Privada", "fr": "Privée", "it": "Privata"},
    "other": {"pt": "Outro", "en": "Other", "es": "Otro", "fr": "Autre", "it": "Altro"},
    "teaching_format": {
        "pt": "Formato de Ensino",
        "en": "Teaching Format",
        "es": "Formato de Enseñanza",
        "fr": "Format d'Enseignement",
        "it": "Formato di Insegnamento",
    },
    "in_person": {
        "pt": "Presencial",
        "en": "In-Person",
        "es": "Presencial",
        "fr": "Présentiel",
        "it": "In Presenza",
    },
    "distance": {
        "pt": "A Distância",
        "en": "Distance",
        "es": "A Distancia",
        "fr": "À Distance",
        "it": "A Distanza",
    },
    "no_data_year": {
        "pt": "Não há dados disponíveis para o ano {year} e tipo de dado {dtype}.",
        "en": "No data available for year {year} and data type {dtype}.",
        "es": "No hay datos disponibles para el año {year} y tipo de dato {dtype}.",
        "fr": "Aucune donnée disponible pour l'année {year} et le type {dtype}.",
        "it": "Nessun dato disponibile per l'anno {year} e il tipo {dtype}.",
    },
    "data_not_loaded": {
        "pt": "Dados não carregados. Por favor, retorne à página inicial.",
        "en": "Data not loaded. Please go back to the home page.",
        "es": "Datos no cargados. Por favor, regrese a la página de inicio.",
        "fr": "Données non chargées. Veuillez retourner à la page d'accueil.",
        "it": "Dati non caricati. Si prega di tornare alla pagina iniziale.",
    },
    # ── Visão Geral ───────────────────────────────────────────────────────────
    "overview_title": {
        "pt": "Visão Geral e Evolução Temporal",
        "en": "Overview & Temporal Evolution",
        "es": "Visión General y Evolución Temporal",
        "fr": "Vue d'Ensemble et Évolution Temporelle",
        "it": "Panoramica ed Evoluzione Temporale",
    },
    "overview_header": {
        "pt": "Dados para {dtype} - Ano: {year}",
        "en": "Data for {dtype} - Year: {year}",
        "es": "Datos para {dtype} - Año: {year}",
        "fr": "Données pour {dtype} - Année : {year}",
        "it": "Dati per {dtype} - Anno: {year}",
    },
    "overview_evolution_sub": {
        "pt": "Evolução da Representatividade de Pretos ao Longo dos Anos",
        "en": "Evolution of Black Students' Representativeness Over the Years",
        "es": "Evolución de la Representatividad de Negros a lo Largo de los Años",
        "fr": "Évolution de la Représentativité des Étudiants Noirs au Fil des Ans",
        "it": "Evoluzione della Rappresentatività degli Studenti Neri nel Tempo",
    },
    "overview_evolution_title": {
        "pt": "Representatividade de Pretos ({dtype})",
        "en": "Black Students Representativeness ({dtype})",
        "es": "Representatividad de Negros ({dtype})",
        "fr": "Représentativité des Étudiants Noirs ({dtype})",
        "it": "Rappresentatività degli Studenti Neri ({dtype})",
    },
    "overview_detail_sub": {
        "pt": "Dados Detalhados para o Ano {year}",
        "en": "Detailed Data for Year {year}",
        "es": "Datos Detallados para el Año {year}",
        "fr": "Données Détaillées pour l'Année {year}",
        "it": "Dati Dettagliati per l'Anno {year}",
    },
    "overview_metric_label": {
        "pt": "Representatividade de Pretos ({dtype}) em {year}",
        "en": "Black Students Representativeness ({dtype}) in {year}",
        "es": "Representatividad de Negros ({dtype}) en {year}",
        "fr": "Représentativité des Étudiants Noirs ({dtype}) en {year}",
        "it": "Rappresentatività degli Studenti Neri ({dtype}) in {year}",
    },
    "overview_total_label": {
        "pt": "Total de {dtype} em {year}: {val}",
        "en": "Total {dtype} in {year}: {val}",
        "es": "Total de {dtype} en {year}: {val}",
        "fr": "Total {dtype} en {year} : {val}",
        "it": "Totale {dtype} in {year}: {val}",
    },
    "overview_total_black_label": {
        "pt": "Total de Pretos ({dtype}) em {year}: {val}",
        "en": "Total Black ({dtype}) in {year}: {val}",
        "es": "Total Negros ({dtype}) en {year}: {val}",
        "fr": "Total Noirs ({dtype}) en {year} : {val}",
        "it": "Totale Neri ({dtype}) in {year}: {val}",
    },
    "overview_race_sub": {
        "pt": "Comparativo de Representatividade por Raça/Cor",
        "en": "Representativeness Comparison by Race/Color",
        "es": "Comparativo de Representatividad por Raza/Color",
        "fr": "Comparaison de Représentativité par Race/Couleur",
        "it": "Confronto di Rappresentatività per Razza/Colore",
    },
    "overview_race_pie_title": {
        "pt": "Distribuição de {dtype} por Raça/Cor em {year}",
        "en": "Distribution of {dtype} by Race/Color in {year}",
        "es": "Distribución de {dtype} por Raza/Color en {year}",
        "fr": "Distribution de {dtype} par Race/Couleur en {year}",
        "it": "Distribuzione di {dtype} per Razza/Colore in {year}",
    },
    "overview_area_title": {
        "pt": "Participação percentual por Cor/Raça ao longo do tempo ({dtype})",
        "en": "Percentage Share by Race/Color Over Time ({dtype})",
        "es": "Participación porcentual por Raza/Color a lo largo del tiempo ({dtype})",
        "fr": "Part en % par Race/Couleur au fil du temps ({dtype})",
        "it": "Quota percentuale per Razza/Colore nel tempo ({dtype})",
    },
    "overview_temporal_sub": {
        "pt": "Evolução Temporal Detalhada - {dtype} Pretos vs Outros",
        "en": "Detailed Temporal Evolution - {dtype} Black vs Others",
        "es": "Evolución Temporal Detallada - {dtype} Negros vs Otros",
        "fr": "Évolution Temporelle Détaillée - {dtype} Noirs vs Autres",
        "it": "Evoluzione Temporale Dettagliata - {dtype} Neri vs Altri",
    },
    "overview_pct_title": {
        "pt": "Evolução da Representatividade (%)",
        "en": "Evolution of Representativeness (%)",
        "es": "Evolución de la Representatividad (%)",
        "fr": "Évolution de la Représentativité (%)",
        "it": "Evoluzione della Rappresentatività (%)",
    },
    "overview_abs_title": {
        "pt": "Comparação: Pretos vs Outros ({dtype})",
        "en": "Comparison: Black vs Others ({dtype})",
        "es": "Comparación: Negros vs Otros ({dtype})",
        "fr": "Comparaison : Noirs vs Autres ({dtype})",
        "it": "Confronto: Neri vs Altri ({dtype})",
    },
    "overview_growth_title": {
        "pt": "Taxa de Crescimento Anual (%) - {dtype}",
        "en": "Annual Growth Rate (%) - {dtype}",
        "es": "Tasa de Crecimiento Anual (%) - {dtype}",
        "fr": "Taux de Croissance Annuel (%) - {dtype}",
        "it": "Tasso di Crescita Annuale (%) - {dtype}",
    },
    "overview_table_sub": {
        "pt": "Dados da Evolução Temporal",
        "en": "Temporal Evolution Data",
        "es": "Datos de Evolución Temporal",
        "fr": "Données d'Évolution Temporelle",
        "it": "Dati dell'Evoluzione Temporale",
    },
    "overview_col_black_pct": {
        "pt": "Representatividade (%) - Pretos",
        "en": "Representativeness (%) - Black",
        "es": "Representatividad (%) - Negros",
        "fr": "Représentativité (%) - Noirs",
        "it": "Rappresentatività (%) - Neri",
    },
    "overview_col_other_pct": {
        "pt": "Representatividade (%) - Outros",
        "en": "Representativeness (%) - Others",
        "es": "Representatividad (%) - Otros",
        "fr": "Représentativité (%) - Autres",
        "it": "Rappresentatività (%) - Altri",
    },
    "legend_black_pct": {
        "pt": "Pretos (%)",
        "en": "Black (%)",
        "es": "Negros (%)",
        "fr": "Noirs (%)",
        "it": "Neri (%)",
    },
    "legend_other_pct": {
        "pt": "Outros (%)",
        "en": "Others (%)",
        "es": "Otros (%)",
        "fr": "Autres (%)",
        "it": "Altri (%)",
    },
    "legend_black_abs": {
        "pt": "Pretos (Abs)",
        "en": "Black (Abs)",
        "es": "Negros (Abs)",
        "fr": "Noirs (Abs)",
        "it": "Neri (Ass)",
    },
    "legend_other_abs": {
        "pt": "Outros (Abs)",
        "en": "Others (Abs)",
        "es": "Otros (Abs)",
        "fr": "Autres (Abs)",
        "it": "Altri (Ass)",
    },
    "legend_historical": {
        "pt": "Histórico",
        "en": "Historical",
        "es": "Histórico",
        "fr": "Historique",
        "it": "Storico",
    },
    "legend_future_proj": {
        "pt": "Projeção Futura",
        "en": "Future Projection",
        "es": "Proyección Futura",
        "fr": "Projection Future",
        "it": "Proiezione Futura",
    },
    "legend_parity_est": {
        "pt": "Estimativa de Paridade",
        "en": "Parity Estimate",
        "es": "Estimativa de Paridad",
        "fr": "Estimation de Parité",
        "it": "Stima di Parità",
    },
    # ── Comparativo por Curso ─────────────────────────────────────────────────
    "course_title": {
        "pt": "Comparativo por Curso",
        "en": "Comparison by Course",
        "es": "Comparativo por Curso",
        "fr": "Comparaison par Cours",
        "it": "Confronto per Corso",
    },
    "course_header": {
        "pt": "Comparativo de {dtype} por Curso - Ano: {year}",
        "en": "Comparison of {dtype} by Course - Year: {year}",
        "es": "Comparativo de {dtype} por Curso - Año: {year}",
        "fr": "Comparaison de {dtype} par Cours - Année : {year}",
        "it": "Confronto di {dtype} per Corso - Anno: {year}",
    },
    "course_table_sub": {
        "pt": "Tabela de {dtype} por Curso",
        "en": "Table of {dtype} by Course",
        "es": "Tabla de {dtype} por Curso",
        "fr": "Tableau de {dtype} par Cours",
        "it": "Tabella di {dtype} per Corso",
    },
    "course_slider": {
        "pt": "Número de Cursos para o Gráfico de Pizza",
        "en": "Number of Courses for Pie Chart",
        "es": "Número de Cursos para el Gráfico de Pastel",
        "fr": "Nombre de Cours pour le Graphique Circulaire",
        "it": "Numero di Corsi per il Grafico a Torta",
    },
    "course_pie_title": {
        "pt": "Distribuição de Pretos ({dtype}) por Curso (Top {n} + Outros) em {year}",
        "en": "Distribution of Black ({dtype}) by Course (Top {n} + Others) in {year}",
        "es": "Distribución de Negros ({dtype}) por Curso (Top {n} + Otros) en {year}",
        "fr": "Distribution de Noirs ({dtype}) par Cours (Top {n} + Autres) en {year}",
        "it": "Distribuzione di Neri ({dtype}) per Corso (Top {n} + Altri) in {year}",
    },
    # ── Análise Regional ──────────────────────────────────────────────────────
    "regional_title": {
        "pt": "Análise Regional",
        "en": "Regional Analysis",
        "es": "Análisis Regional",
        "fr": "Analyse Régionale",
        "it": "Analisi Regionale",
    },
    "regional_header": {
        "pt": "Representatividade de Pretos ({dtype}) por Região - Ano: {year}",
        "en": "Black Students Representativeness ({dtype}) by Region - Year: {year}",
        "es": "Representatividad de Negros ({dtype}) por Región - Año: {year}",
        "fr": "Représentativité des Étudiants Noirs ({dtype}) par Région - Année : {year}",
        "it": "Rappresentatività degli Studenti Neri ({dtype}) per Regione - Anno: {year}",
    },
    "regional_bar_sub": {
        "pt": "Representatividade de Pretos ({dtype}) por Região",
        "en": "Black Students Representativeness ({dtype}) by Region",
        "es": "Representatividad de Negros ({dtype}) por Región",
        "fr": "Représentativité des Étudiants Noirs ({dtype}) par Région",
        "it": "Rappresentatività degli Studenti Neri ({dtype}) per Regione",
    },
    "regional_bar_title": {
        "pt": "Representatividade de Pretos ({dtype}) por Região em {year}",
        "en": "Black Students Representativeness ({dtype}) by Region in {year}",
        "es": "Representatividad de Negros ({dtype}) por Región en {year}",
        "fr": "Représentativité des Étudiants Noirs ({dtype}) par Région en {year}",
        "it": "Rappresentatività degli Studenti Neri ({dtype}) per Regione in {year}",
    },
    "regional_evol_sub": {
        "pt": "Evolução da Representatividade por Região ao Longo dos Anos",
        "en": "Evolution of Representativeness by Region Over the Years",
        "es": "Evolución de la Representatividad por Región a lo Largo de los Años",
        "fr": "Évolution de la Représentativité par Région au Fil des Ans",
        "it": "Evoluzione della Rappresentatività per Regione nel Tempo",
    },
    "regional_evol_title": {
        "pt": "Evolução da Representatividade de Pretos ({dtype}) por Região",
        "en": "Evolution of Black Students Representativeness ({dtype}) by Region",
        "es": "Evolución de la Representatividad de Negros ({dtype}) por Región",
        "fr": "Évolution de la Représentativité des Étudiants Noirs ({dtype}) par Région",
        "it": "Evoluzione della Rappresentatività degli Studenti Neri ({dtype}) per Regione",
    },
    "regional_heatmap_sub": {
        "pt": "Mapa de Calor: Representatividade por Região ao Longo dos Anos",
        "en": "Heatmap: Representativeness by Region Over the Years",
        "es": "Mapa de Calor: Representatividad por Región a lo Largo de los Años",
        "fr": "Carte de Chaleur : Représentativité par Région au Fil des Ans",
        "it": "Mappa di Calore: Rappresentatività per Regione nel Tempo",
    },
    "regional_heatmap_title": {
        "pt": "Mapa de Calor - Representatividade de Pretos ({dtype}) por Região x Ano",
        "en": "Heatmap - Black Students Representativeness ({dtype}) by Region × Year",
        "es": "Mapa de Calor - Representatividad de Negros ({dtype}) por Región × Año",
        "fr": "Carte de Chaleur - Représentativité des Étudiants Noirs ({dtype}) par Région × Année",
        "it": "Mappa di Calore - Rappresentatività degli Studenti Neri ({dtype}) per Regione × Anno",
    },
    # ── Análise Institucional ─────────────────────────────────────────────────
    "inst_title": {
        "pt": "Análise por Tipo de Instituição",
        "en": "Analysis by Institution Type",
        "es": "Análisis por Tipo de Institución",
        "fr": "Analyse par Type d'Institution",
        "it": "Analisi per Tipo di Istituzione",
    },
    "inst_header": {
        "pt": "Representatividade de {dtype} por Tipo de Instituição - Ano: {year}",
        "en": "Representativeness of {dtype} by Institution Type - Year: {year}",
        "es": "Representatividad de {dtype} por Tipo de Institución - Año: {year}",
        "fr": "Représentativité de {dtype} par Type d'Institution - Année : {year}",
        "it": "Rappresentatività di {dtype} per Tipo di Istituzione - Anno: {year}",
    },
    "inst_pubpriv_sub": {
        "pt": "Representatividade de Pretos ({dtype}) - Pública vs Privada",
        "en": "Black Students Representativeness ({dtype}) - Public vs Private",
        "es": "Representatividad de Negros ({dtype}) - Pública vs Privada",
        "fr": "Représentativité des Étudiants Noirs ({dtype}) - Public vs Privé",
        "it": "Rappresentatività degli Studenti Neri ({dtype}) - Pubblica vs Privata",
    },
    "inst_pubpriv_title": {
        "pt": "Representatividade de Pretos ({dtype}) - Pública vs Privada em {year}",
        "en": "Black Students Representativeness ({dtype}) - Public vs Private in {year}",
        "es": "Representatividad de Negros ({dtype}) - Pública vs Privada en {year}",
        "fr": "Représentativité des Étudiants Noirs ({dtype}) - Public vs Privé en {year}",
        "it": "Rappresentatività degli Studenti Neri ({dtype}) - Pubblica vs Privata in {year}",
    },
    "inst_detail_sub": {
        "pt": "Representatividade de Pretos ({dtype}) por Tipo de Instituição",
        "en": "Black Students Representativeness ({dtype}) by Institution Type",
        "es": "Representatividad de Negros ({dtype}) por Tipo de Institución",
        "fr": "Représentativité des Étudiants Noirs ({dtype}) par Type d'Institution",
        "it": "Rappresentatività degli Studenti Neri ({dtype}) per Tipo di Istituzione",
    },
    "inst_detail_title": {
        "pt": "Representatividade de Pretos ({dtype}) por Tipo de Instituição em {year}",
        "en": "Black Students Representativeness ({dtype}) by Institution Type in {year}",
        "es": "Representatividad de Negros ({dtype}) por Tipo de Institución en {year}",
        "fr": "Représentativité des Étudiants Noirs ({dtype}) par Type d'Institution en {year}",
        "it": "Rappresentatività degli Studenti Neri ({dtype}) per Tipo di Istituzione in {year}",
    },
    "inst_evol_sub": {
        "pt": "Evolução da Representatividade por Tipo de Instituição ao Longo dos Anos",
        "en": "Evolution of Representativeness by Institution Type Over the Years",
        "es": "Evolución de la Representatividad por Tipo de Institución a lo Largo de los Años",
        "fr": "Évolution de la Représentativité par Type d'Institution au Fil des Ans",
        "it": "Evoluzione della Rappresentatività per Tipo di Istituzione nel Tempo",
    },
    "inst_evol_title": {
        "pt": "Evolução da Representatividade de Pretos ({dtype}) - Pública vs Privada",
        "en": "Evolution of Black Students Representativeness ({dtype}) - Public vs Private",
        "es": "Evolución de la Representatividad de Negros ({dtype}) - Pública vs Privada",
        "fr": "Évolution de la Représentativité des Étudiants Noirs ({dtype}) - Public vs Privé",
        "it": "Evoluzione della Rappresentatività degli Studenti Neri ({dtype}) - Pubblica vs Privata",
    },
    # ── Comparativo por Formato ───────────────────────────────────────────────
    "format_title": {
        "pt": "Comparativo por Formato de Ensino (Presencial vs A Distância)",
        "en": "Comparison by Teaching Format (In-Person vs Distance)",
        "es": "Comparativo por Formato de Enseñanza (Presencial vs A Distancia)",
        "fr": "Comparaison par Format d'Enseignement (Présentiel vs À Distance)",
        "it": "Confronto per Formato di Insegnamento (In Presenza vs A Distanza)",
    },
    "format_bar_sub": {
        "pt": "Representatividade de Pretos por Formato de Ensino - {dtype} ({year})",
        "en": "Black Students Representativeness by Teaching Format - {dtype} ({year})",
        "es": "Representatividad de Negros por Formato de Enseñanza - {dtype} ({year})",
        "fr": "Représentativité des Étudiants Noirs par Format d'Enseignement - {dtype} ({year})",
        "it": "Rappresentatività degli Studenti Neri per Formato di Insegnamento - {dtype} ({year})",
    },
    "format_bar_title": {
        "pt": "Representatividade de Pretos ({dtype}) por Formato de Ensino em {year}",
        "en": "Black Students Representativeness ({dtype}) by Teaching Format in {year}",
        "es": "Representatividad de Negros ({dtype}) por Formato de Enseñanza en {year}",
        "fr": "Représentativité des Étudiants Noirs ({dtype}) par Format d'Enseignement en {year}",
        "it": "Rappresentatività degli Studenti Neri ({dtype}) per Formato di Insegnamento in {year}",
    },
    "format_table_sub": {
        "pt": "Tabela Resumo",
        "en": "Summary Table",
        "es": "Tabla Resumen",
        "fr": "Tableau Résumé",
        "it": "Tabella Riassuntiva",
    },
    "format_evol_sub": {
        "pt": "Evolução Temporal por Formato de Ensino",
        "en": "Temporal Evolution by Teaching Format",
        "es": "Evolución Temporal por Formato de Enseñanza",
        "fr": "Évolution Temporelle par Format d'Enseignement",
        "it": "Evoluzione Temporale per Formato di Insegnamento",
    },
    "format_evol_title": {
        "pt": "Evolução da Representatividade de Pretos por Formato de Ensino - {dtype}",
        "en": "Evolution of Black Students Representativeness by Teaching Format - {dtype}",
        "es": "Evolución de la Representatividad de Negros por Formato de Enseñanza - {dtype}",
        "fr": "Évolution de la Représentativité des Étudiants Noirs par Format d'Enseignement - {dtype}",
        "it": "Evoluzione della Rappresentatività degli Studenti Neri per Formato di Insegnamento - {dtype}",
    },
    "format_col_total": {
        "pt": "Total Geral",
        "en": "Grand Total",
        "es": "Total General",
        "fr": "Total Général",
        "it": "Totale Generale",
    },
    "format_col_total_black": {
        "pt": "Total de Pretos",
        "en": "Total Black",
        "es": "Total Negros",
        "fr": "Total Noirs",
        "it": "Totale Neri",
    },
    "format_col_pct_black": {
        "pt": "Percentual de Pretos",
        "en": "Black Percentage",
        "es": "Porcentaje de Negros",
        "fr": "Pourcentage de Noirs",
        "it": "Percentuale di Neri",
    },
    # ── Projeção ──────────────────────────────────────────────────────────────
    "proj_title": {
        "pt": "Projeção e Tendências",
        "en": "Projection & Trends",
        "es": "Proyección y Tendencias",
        "fr": "Projection et Tendances",
        "it": "Proiezione e Tendenze",
    },
    "proj_subtitle": {
        "pt": "Projeção para: {dtype}",
        "en": "Projection for: {dtype}",
        "es": "Proyección para: {dtype}",
        "fr": "Projection pour : {dtype}",
        "it": "Proiezione per: {dtype}",
    },
    "proj_chart_title": {
        "pt": "Tendência e Projeção de Representatividade ({dtype})",
        "en": "Representativeness Trend & Projection ({dtype})",
        "es": "Tendencia y Proyección de Representatividad ({dtype})",
        "fr": "Tendance et Projection de Représentativité ({dtype})",
        "it": "Tendenza e Proiezione della Rappresentatività ({dtype})",
    },
    "proj_stats_sub": {
        "pt": "Estatísticas da Tendência",
        "en": "Trend Statistics",
        "es": "Estadísticas de la Tendencia",
        "fr": "Statistiques de la Tendance",
        "it": "Statistiche della Tendenza",
    },
    "proj_meta_sub": {
        "pt": "Comparação com meta populacional",
        "en": "Comparison with Population Target",
        "es": "Comparación con meta poblacional",
        "fr": "Comparaison avec l'objectif démographique",
        "it": "Confronto con il target demografico",
    },
    "proj_data_sub": {
        "pt": "Dados Utilizados",
        "en": "Data Used",
        "es": "Datos Utilizados",
        "fr": "Données Utilisées",
        "it": "Dati Utilizzati",
    },
    "proj_col_year": {
        "pt": "Ano",
        "en": "Year",
        "es": "Año",
        "fr": "Année",
        "it": "Anno",
    },
    "proj_col_repr": {
        "pt": "Representatividade (%)",
        "en": "Representativeness (%)",
        "es": "Representatividad (%)",
        "fr": "Représentativité (%)",
        "it": "Rappresentatività (%)",
    },
    # ── Comparativo Geral ─────────────────────────────────────────────────────
    "general_title": {
        "pt": "Comparativo Geral",
        "en": "General Comparison",
        "es": "Comparativo General",
        "fr": "Comparaison Générale",
        "it": "Confronto Generale",
    },
    "general_header": {
        "pt": "Comparação de Dados para o Ano: {year}",
        "en": "Data Comparison for Year: {year}",
        "es": "Comparación de Datos para el Año: {year}",
        "fr": "Comparaison de Données pour l'Année : {year}",
        "it": "Confronto Dati per l'Anno: {year}",
    },
    "general_compare_by": {
        "pt": "Comparar por Grupo",
        "en": "Compare by Group",
        "es": "Comparar por Grupo",
        "fr": "Comparer par Groupe",
        "it": "Confronta per Gruppo",
    },
    "general_config_sub": {
        "pt": "Configurações de Comparação",
        "en": "Comparison Settings",
        "es": "Configuración de Comparación",
        "fr": "Paramètres de Comparaison",
        "it": "Impostazioni di Confronto",
    },
    "general_group_region": {
        "pt": "Região",
        "en": "Region",
        "es": "Región",
        "fr": "Région",
        "it": "Regione",
    },
    "general_group_inst": {
        "pt": "Tipo de Instituição",
        "en": "Institution Type",
        "es": "Tipo de Institución",
        "fr": "Type d'Institution",
        "it": "Tipo di Istituzione",
    },
    "general_group_course": {
        "pt": "Curso",
        "en": "Course",
        "es": "Curso",
        "fr": "Cours",
        "it": "Corso",
    },
    "general_group_format": {
        "pt": "Formato",
        "en": "Format",
        "es": "Formato",
        "fr": "Format",
        "it": "Formato",
    },
    "general_showing": {
        "pt": "Mostrando: Ingressantes, Concluintes e Matriculados",
        "en": "Showing: Entrants, Graduates and Enrolled",
        "es": "Mostrando: Ingresantes, Egresados y Matriculados",
        "fr": "Affichage : Entrants, Diplômés et Inscrits",
        "it": "Visualizzazione: Immatricolati, Laureati e Iscritti",
    },
    "general_comp_sub": {
        "pt": "Comparação de Representatividade de Pretos por {group}",
        "en": "Black Students Representativeness Comparison by {group}",
        "es": "Comparación de Representatividad de Negros por {group}",
        "fr": "Comparaison de Représentativité des Étudiants Noirs par {group}",
        "it": "Confronto della Rappresentatività degli Studenti Neri per {group}",
    },
    "general_comp_title": {
        "pt": "Comparativo de Representatividade de Pretos por {group} em {year}",
        "en": "Black Students Representativeness Comparison by {group} in {year}",
        "es": "Comparativo de Representatividad de Negros por {group} en {year}",
        "fr": "Comparaison de Représentativité des Étudiants Noirs par {group} en {year}",
        "it": "Confronto della Rappresentatività degli Studenti Neri per {group} in {year}",
    },
    "general_table_sub": {
        "pt": "Tabela Comparativa",
        "en": "Comparative Table",
        "es": "Tabla Comparativa",
        "fr": "Tableau Comparatif",
        "it": "Tabella Comparativa",
    },
    # ── Home page ─────────────────────────────────────────────────────────────
    "home_main_title": {
        "pt": "📊 Representatividade de Estudantes Negros<br>nos Cursos de Computação no Brasil",
        "en": "📊 Black Students' Representativeness<br>in Computer Science Courses in Brazil",
        "es": "📊 Representatividad de Estudiantes Negros<br>en Cursos de Computación en Brasil",
        "fr": "📊 Représentativité des Étudiants Noirs<br>dans les Formations en Informatique au Brésil",
        "it": "📊 Rappresentatività degli Studenti Neri<br>nei Corsi di Informatica in Brasile",
    },
    "home_subtitle": {
        "pt": "Análise do Censo da Educação Superior &nbsp;|&nbsp; 2009 – 2024",
        "en": "Higher Education Census Analysis &nbsp;|&nbsp; 2009 – 2024",
        "es": "Análisis del Censo de Educación Superior &nbsp;|&nbsp; 2009 – 2024",
        "fr": "Analyse du Recensement de l'Enseignement Supérieur &nbsp;|&nbsp; 2009 – 2024",
        "it": "Analisi del Censimento dell'Istruzione Superiore &nbsp;|&nbsp; 2009 – 2024",
    },
    "home_about_title": {
        "pt": "Sobre este Dashboard",
        "en": "About this Dashboard",
        "es": "Acerca de este Dashboard",
        "fr": "À propos de ce Dashboard",
        "it": "Informazioni su questo Dashboard",
    },
    "home_about_body": {
        "pt": """Este dashboard foi desenvolvido para analisar de forma aprofundada a
            **representatividade de estudantes autodeclarados pretos** nos cursos de
            Computação das instituições de ensino superior brasileiras.

            Os dados provêm do **Censo da Educação Superior** (INEP/MEC), cobrindo
            **16 anos consecutivos** (2009 a 2024), e permitem acompanhar como essa
            população se posiciona nas etapas de **ingresso**, **matrícula** e
            **conclusão** dos cursos.

            A análise é realizada em múltiplas dimensões: temporal, regional,
            institucional e por tipo de curso, oferecendo uma visão abrangente
            das desigualdades ainda existentes e das tendências ao longo do tempo.""",
        "en": """This dashboard was developed to deeply analyze the
            **representativeness of self-declared Black students** in Computer Science
            courses at Brazilian higher education institutions.

            Data comes from the **Higher Education Census** (INEP/MEC), covering
            **16 consecutive years** (2009 to 2024), tracking how this population
            is positioned at the stages of **entry**, **enrollment**, and
            **graduation**.

            The analysis covers multiple dimensions: temporal, regional,
            institutional, and by course type, offering a comprehensive view
            of existing inequalities and trends over time.""",
        "es": """Este dashboard fue desarrollado para analizar en profundidad la
            **representatividad de estudiantes autodeclarados negros** en los cursos de
            Computación de las instituciones de educación superior brasileñas.

            Los datos provienen del **Censo de Educación Superior** (INEP/MEC), cubriendo
            **16 años consecutivos** (2009 a 2024), y permiten seguir cómo esta
            población se posiciona en las etapas de **ingreso**, **matrícula** y
            **egreso** de los cursos.

            El análisis se realiza en múltiples dimensiones: temporal, regional,
            institucional y por tipo de curso, ofreciendo una visión integral
            de las desigualdades existentes y las tendencias a lo largo del tiempo.""",
        "fr": """Ce dashboard a été développé pour analyser en profondeur la
            **représentativité des étudiants se déclarant noirs** dans les formations
            en informatique des établissements d'enseignement supérieur brésiliens.

            Les données proviennent du **Recensement de l'Enseignement Supérieur** (INEP/MEC),
            couvrant **16 années consécutives** (2009 à 2024), et permettent de suivre
            comment cette population se positionne aux étapes d'**entrée**, d'**inscription** et
            de **diplomation**.

            L'analyse est réalisée selon plusieurs dimensions : temporelle, régionale,
            institutionnelle et par type de formation, offrant une vue d'ensemble
            des inégalités existantes et des tendances au fil du temps.""",
        "it": """Questo dashboard è stato sviluppato per analizzare in modo approfondito la
            **rappresentatività degli studenti che si autodichiarano neri** nei corsi di
            Informatica delle istituzioni di istruzione superiore brasiliane.

            I dati provengono dal **Censimento dell'Istruzione Superiore** (INEP/MEC), coprendo
            **16 anni consecutivi** (dal 2009 al 2024), e permettono di seguire come questa
            popolazione si posiziona nelle fasi di **immatricolazione**, **iscrizione** e
            **laurea**.

            L'analisi è condotta su più dimensioni: temporale, regionale, istituzionale
            e per tipo di corso, offrendo una visione completa delle disuguaglianze esistenti
            e delle tendenze nel tempo.""",
    },
    "home_source": {
        "pt": "**Fonte dos dados**\nCenso da Educação Superior\nINEP / MEC\n\n**Período coberto**\n2009 a 2024\n\n**Área analisada**\nCursos de Computação\n(graduação presencial e EaD)\n\n**Recorte racial**\nCor/raça *preta* (IBGE)",
        "en": "**Data Source**\nHigher Education Census\nINEP / MEC\n\n**Period covered**\n2009 to 2024\n\n**Area analyzed**\nComputer Science Courses\n(in-person and distance learning)\n\n**Racial focus**\nRace/color *black* (IBGE)",
        "es": "**Fuente de datos**\nCenso de Educación Superior\nINEP / MEC\n\n**Período cubierto**\n2009 a 2024\n\n**Área analizada**\nCursos de Computación\n(presencial y a distancia)\n\n**Recorte racial**\nColor/raza *negra* (IBGE)",
        "fr": "**Source des données**\nRecensement de l'Enseignement Supérieur\nINEP / MEC\n\n**Période couverte**\n2009 à 2024\n\n**Domaine analysé**\nFormations en Informatique\n(présentiel et à distance)\n\n**Axe racial**\nCouleur/race *noire* (IBGE)",
        "it": "**Fonte dei dati**\nCensimento dell'Istruzione Superiore\nINEP / MEC\n\n**Periodo coperto**\ndal 2009 al 2024\n\n**Area analizzata**\nCorsi di Informatica\n(presenza e a distanza)\n\n**Focus razziale**\nColore/razza *nera* (IBGE)",
    },
    "home_context_title": {
        "pt": "Contexto e Motivação",
        "en": "Context & Motivation",
        "es": "Contexto y Motivación",
        "fr": "Contexte et Motivation",
        "it": "Contesto e Motivazione",
    },
    "home_context_body": {
        "pt": """Apesar de representarem mais de **10% da população brasileira** segundo o IBGE,
        estudantes autodeclarados *pretos* historicamente ocupam uma parcela
        desproporcional das vagas nos cursos de tecnologia. Compreender essa dinâmica
        é o primeiro passo para promover políticas de inclusão efetivas.

        O dashboard cruza dados de **ingresso**, **matrícula** e **conclusão** por
        raça/cor ao longo dos anos, permitindo identificar:

        - Se houve avanço na entrada de estudantes negros após marcos como a
          **Lei de Cotas (Lei 12.711/2012)**;
        - Quais regiões e estados apresentam maior ou menor representatividade;
        - Como diferentes tipos de instituição (pública × privada) se comportam;
        - Se a retenção e conclusão acompanham o crescimento no ingresso.""",
        "en": """Despite representing more than **10% of the Brazilian population** according to IBGE,
        self-declared *Black* students have historically occupied a disproportionate share
        of places in technology courses. Understanding this dynamic is the first step
        toward effective inclusion policies.

        The dashboard crosses data on **entry**, **enrollment**, and **graduation** by
        race/color over the years, enabling us to identify:

        - Whether there has been progress in the admission of Black students after milestones like
          the **Quota Law (Law 12.711/2012)**;
        - Which regions and states show greater or lesser representativeness;
        - How different types of institutions (public × private) behave;
        - Whether retention and graduation track the growth in admissions.""",
        "es": """A pesar de representar más del **10% de la población brasileña** según el IBGE,
        los estudiantes autodeclarados *negros* históricamente ocupan una parte
        desproporcionada de los cupos en los cursos de tecnología. Comprender esta dinámica
        es el primer paso para promover políticas de inclusión efectivas.

        El dashboard cruza datos de **ingreso**, **matrícula** y **egreso** por
        raza/color a lo largo de los años, permitiendo identificar:

        - Si hubo avances en la entrada de estudiantes negros tras hitos como la
          **Ley de Cuotas (Ley 12.711/2012)**;
        - Qué regiones y estados presentan mayor o menor representatividad;
        - Cómo se comportan los diferentes tipos de institución (pública × privada);
        - Si la retención y el egreso acompañan el crecimiento en el ingreso.""",
        "fr": """Bien qu'ils représentent plus de **10 % de la population brésilienne** selon l'IBGE,
        les étudiants se déclarant *noirs* occupent historiquement une part disproportionnée
        des places dans les formations technologiques. Comprendre cette dynamique est la première
        étape pour promouvoir des politiques d'inclusion efficaces.

        Le dashboard croise des données sur l'**entrée**, l'**inscription** et la **diplomation** par
        race/couleur au fil des années, permettant d'identifier :

        - Si des progrès ont été réalisés dans l'admission des étudiants noirs après des jalons tels que
          la **Loi sur les quotas (Loi 12.711/2012)** ;
        - Quelles régions et quels États présentent une représentativité plus ou moins grande ;
        - Comment se comportent les différents types d'établissements (public × privé) ;
        - Si la rétention et la diplomation suivent la croissance des admissions.""",
        "it": """Nonostante rappresentino più del **10% della popolazione brasiliana** secondo l'IBGE,
        gli studenti che si autodichiarano *neri* hanno storicamente occupato una quota sproporzionata
        dei posti nei corsi di tecnologia. Comprendere questa dinamica è il primo passo
        verso politiche di inclusione efficaci.

        Il dashboard incrocia i dati su **immatricolazione**, **iscrizione** e **laurea** per
        razza/colore nel corso degli anni, permettendo di identificare:

        - Se vi siano stati progressi nell'ammissione degli studenti neri dopo traguardi come la
          **Legge sulle quote (Legge 12.711/2012)**;
        - Quali regioni e stati mostrano una rappresentatività maggiore o minore;
        - Come si comportano i diversi tipi di istituzione (pubblica × privata);
        - Se la ritenzione e la laurea seguono la crescita nelle ammissioni.""",
    },
    "home_pages_title": {
        "pt": "Análises Disponíveis",
        "en": "Available Analyses",
        "es": "Análisis Disponibles",
        "fr": "Analyses Disponibles",
        "it": "Analisi Disponibili",
    },
    "home_how_title": {
        "pt": "Como Usar",
        "en": "How to Use",
        "es": "Cómo Usar",
        "fr": "Comment Utiliser",
        "it": "Come Usare",
    },
    "home_how_body": {
        "pt": """1. **Selecione a análise** desejada no menu lateral em *Selecione a Página*.
        2. Use o **slider de ano** para filtrar um ano específico nas visualizações por corte temporal.
        3. Escolha o **tipo de dado** — *Ingressantes*, *Concluintes* ou *Matriculados* — para
           alternar entre as diferentes etapas da jornada acadêmica.
        4. Todas as análises se atualizam automaticamente com os filtros selecionados.
        5. Os gráficos são **interativos**: passe o mouse para ver detalhes, clique na legenda
           para ocultar séries, e use o zoom para explorar intervalos específicos.""",
        "en": """1. **Select the analysis** you want from the sidebar under *Select Page*.
        2. Use the **year slider** to filter a specific year in temporal visualizations.
        3. Choose the **data type** — *Entrants*, *Graduates*, or *Enrolled* — to
           switch between different stages of the academic journey.
        4. All analyses update automatically with the selected filters.
        5. Charts are **interactive**: hover to see details, click the legend
           to hide series, and use zoom to explore specific intervals.""",
        "es": """1. **Seleccione el análisis** deseado en el menú lateral en *Seleccione la Página*.
        2. Use el **deslizador de año** para filtrar un año específico en las visualizaciones temporales.
        3. Elija el **tipo de dato** — *Ingresantes*, *Egresados* o *Matriculados* — para
           alternar entre las diferentes etapas del recorrido académico.
        4. Todos los análisis se actualizan automáticamente con los filtros seleccionados.
        5. Los gráficos son **interactivos**: pase el ratón para ver detalles, haga clic en la leyenda
           para ocultar series, y use el zoom para explorar intervalos específicos.""",
        "fr": """1. **Sélectionnez l'analyse** souhaitée dans le menu latéral sous *Sélectionnez la Page*.
        2. Utilisez le **curseur d'année** pour filtrer une année spécifique dans les visualisations temporelles.
        3. Choisissez le **type de donnée** — *Entrants*, *Diplômés* ou *Inscrits* — pour
           alterner entre les différentes étapes du parcours académique.
        4. Toutes les analyses se mettent à jour automatiquement avec les filtres sélectionnés.
        5. Les graphiques sont **interactifs** : survolez pour voir les détails, cliquez sur la légende
           pour masquer des séries, et utilisez le zoom pour explorer des intervalles spécifiques.""",
        "it": """1. **Selezionate l'analisi** desiderata nel menu laterale sotto *Seleziona la Pagina*.
        2. Usate il **cursore dell'anno** per filtrare un anno specifico nelle visualizzazioni temporali.
        3. Scegliete il **tipo di dato** — *Immatricolati*, *Laureati* o *Iscritti* — per
           passare tra le diverse fasi del percorso accademico.
        4. Tutte le analisi si aggiornano automaticamente con i filtri selezionati.
        5. I grafici sono **interattivi**: passate il mouse per vedere i dettagli, cliccate sulla legenda
           per nascondere le serie e usate lo zoom per esplorare intervalli specifici.""",
    },
    "home_footer": {
        "pt": "Dados: INEP — Censo da Educação Superior &nbsp;|&nbsp; Desenvolvido com <a href='https://streamlit.io' target='_blank'>Streamlit</a>",
        "en": "Data: INEP — Higher Education Census &nbsp;|&nbsp; Built with <a href='https://streamlit.io' target='_blank'>Streamlit</a>",
        "es": "Datos: INEP — Censo de Educación Superior &nbsp;|&nbsp; Desarrollado con <a href='https://streamlit.io' target='_blank'>Streamlit</a>",
        "fr": "Données : INEP — Recensement de l'Enseignement Supérieur &nbsp;|&nbsp; Développé avec <a href='https://streamlit.io' target='_blank'>Streamlit</a>",
        "it": "Dati: INEP — Censimento dell'Istruzione Superiore &nbsp;|&nbsp; Sviluppato con <a href='https://streamlit.io' target='_blank'>Streamlit</a>",
    },
    # ── Descrições das páginas (cards na home) ────────────────────────────────
    "home_card_overview_desc": {
        "pt": "Evolução temporal da representatividade de estudantes pretos em todos os cursos de Computação, comparando ingressantes, matriculados e concluintes ao longo dos 16 anos de dados.",
        "en": "Temporal evolution of Black students' representativeness across all Computer Science courses, comparing entrants, enrolled, and graduates over 16 years of data.",
        "es": "Evolución temporal de la representatividad de estudiantes negros en todos los cursos de Computación, comparando ingresantes, matriculados y egresados a lo largo de 16 años de datos.",
        "fr": "Évolution temporelle de la représentativité des étudiants noirs dans tous les cours d'informatique, comparant entrants, inscrits et diplômés sur 16 ans de données.",
        "it": "Evoluzione temporale della rappresentatività degli studenti neri in tutti i corsi di Informatica, confrontando immatricolati, iscritti e laureati nel corso di 16 anni di dati.",
    },
    "home_card_course_desc": {
        "pt": "Distribuição da representatividade por nome de curso (Ciência da Computação, Sistemas de Informação, Engenharia de Computação, etc.), revelando quais cursos concentram mais ou menos diversidade racial.",
        "en": "Distribution of representativeness by course name (Computer Science, Information Systems, Computer Engineering, etc.), revealing which courses concentrate more or less racial diversity.",
        "es": "Distribución de la representatividad por nombre de curso (Ciencias de la Computación, Sistemas de Información, Ingeniería de Computación, etc.), revelando qué cursos concentran más o menos diversidad racial.",
        "fr": "Distribution de la représentativité par nom de cours (Sciences Informatiques, Systèmes d'Information, Génie Informatique, etc.), révélant quels cours concentrent plus ou moins de diversité raciale.",
        "it": "Distribuzione della rappresentatività per nome del corso (Informatica, Sistemi Informativi, Ingegneria Informatica, ecc.), rivelando quali corsi concentrano più o meno diversità razziale.",
    },
    "home_card_regional_desc": {
        "pt": "Mapa e ranking das cinco regiões brasileiras, mostrando como a presença de estudantes pretos varia entre Norte, Nordeste, Centro-Oeste, Sudeste e Sul.",
        "en": "Map and ranking of the five Brazilian regions, showing how the presence of Black students varies between North, Northeast, Center-West, Southeast, and South.",
        "es": "Mapa y ranking de las cinco regiones brasileñas, mostrando cómo varía la presencia de estudiantes negros entre Norte, Nordeste, Centro-Oeste, Sudeste y Sur.",
        "fr": "Carte et classement des cinq régions brésiliennes, montrant comment la présence d'étudiants noirs varie entre le Nord, le Nord-Est, le Centre-Ouest, le Sud-Est et le Sud.",
        "it": "Mappa e classifica delle cinque regioni brasiliane, mostrando come la presenza di studenti neri varia tra Nord, Nordest, Centro-Ovest, Sudest e Sud.",
    },
    "home_card_inst_desc": {
        "pt": "Comparação entre categorias administrativas (federal, estadual, municipal e privada), indicando qual tipo de instituição é mais inclusivo no recorte racial analisado.",
        "en": "Comparison between administrative categories (federal, state, municipal, and private), indicating which institution type is more inclusive in the racial focus analyzed.",
        "es": "Comparación entre categorías administrativas (federal, estadual, municipal y privada), indicando qué tipo de institución es más inclusivo en el recorte racial analizado.",
        "fr": "Comparaison entre les catégories administratives (fédérale, d'État, municipale et privée), indiquant quel type d'établissement est le plus inclusif dans l'axe racial analysé.",
        "it": "Confronto tra categorie amministrative (federale, statale, municipale e privata), indicando quale tipo di istituzione è più inclusivo nel focus razziale analizzato.",
    },
    "home_card_format_desc": {
        "pt": "Análise da modalidade de ensino — presencial versus EaD — e como cada formato se diferencia em termos de representatividade de estudantes pretos.",
        "en": "Analysis of the teaching modality — in-person versus distance learning — and how each format differs in terms of Black students' representativeness.",
        "es": "Análisis de la modalidad de enseñanza — presencial versus educación a distancia — y cómo cada formato se diferencia en términos de representatividad de estudiantes negros.",
        "fr": "Analyse de la modalité d'enseignement — présentiel versus à distance — et comment chaque format se distingue en termes de représentativité des étudiants noirs.",
        "it": "Analisi della modalità di insegnamento — in presenza versus a distanza — e come ogni formato si differenzia in termini di rappresentatività degli studenti neri.",
    },
    "home_card_general_desc": {
        "pt": "Visão consolidada que reúne todas as dimensões, permitindo cruzar recortes temporais, regionais e institucionais em um único painel comparativo.",
        "en": "Consolidated view that brings together all dimensions, allowing you to cross temporal, regional, and institutional cuts in a single comparative panel.",
        "es": "Visión consolidada que reúne todas las dimensiones, permitiendo cruzar recortes temporales, regionales e institucionales en un único panel comparativo.",
        "fr": "Vue consolidée qui rassemble toutes les dimensions, permettant de croiser les découpages temporels, régionaux et institutionnels dans un seul panneau comparatif.",
        "it": "Vista consolidata che riunisce tutte le dimensioni, consentendo di incrociare tagli temporali, regionali e istituzionali in un unico pannello comparativo.",
    },
    "home_card_proj_desc": {
        "pt": "Modelagem estatística (regressão linear) das tendências históricas para projetar o percentual esperado de estudantes pretos nos próximos anos, com intervalo de confiança.",
        "en": "Statistical modeling (linear regression) of historical trends to project the expected percentage of Black students in the coming years, with confidence interval.",
        "es": "Modelado estadístico (regresión lineal) de las tendencias históricas para proyectar el porcentaje esperado de estudiantes negros en los próximos años, con intervalo de confianza.",
        "fr": "Modélisation statistique (régression linéaire) des tendances historiques pour projeter le pourcentage attendu d'étudiants noirs dans les prochaines années, avec intervalle de confiance.",
        "it": "Modellazione statistica (regressione lineare) delle tendenze storiche per proiettare la percentuale attesa di studenti neri nei prossimi anni, con intervallo di confidenza.",
    },
    # ── Aliases and missing keys ───────────────────────────────────────────────
    "general_comparison_settings": {
        "pt": "Configurações de Comparação",
        "en": "Comparison Settings",
        "es": "Configuración de Comparación",
        "fr": "Paramètres de Comparaison",
        "it": "Impostazioni di Confronto",
    },
    "general_showing_all": {
        "pt": "Mostrando: Ingressantes, Concluintes e Matriculados",
        "en": "Showing: Entrants, Graduates and Enrolled",
        "es": "Mostrando: Ingresantes, Egresados y Matriculados",
        "fr": "Affichage : Entrants, Diplômés et Inscrits",
        "it": "Visualizzazione: Immatricolati, Laureati e Iscritti",
    },
    "general_comparison_sub": {
        "pt": "Comparação de Representatividade de Pretos por {group}",
        "en": "Black Students Representativeness Comparison by {group}",
        "es": "Comparación de Representatividad de Negros por {group}",
        "fr": "Comparaison de Représentativité des Étudiants Noirs par {group}",
        "it": "Confronto della Rappresentatività degli Studenti Neri per {group}",
    },
    "general_comparison_title": {
        "pt": "Comparativo de Representatividade de Pretos por {group} em {year}",
        "en": "Black Students Representativeness Comparison by {group} in {year}",
        "es": "Comparativo de Representatividad de Negros por {group} en {year}",
        "fr": "Comparaison de Représentativité des Étudiants Noirs par {group} en {year}",
        "it": "Confronto della Rappresentatività degli Studenti Neri per {group} in {year}",
    },
    "general_top_n_slider": {
        "pt": "Top N cursos para os gráficos de pizza",
        "en": "Top N courses for pie charts",
        "es": "Top N cursos para los gráficos de pastel",
        "fr": "Top N cours pour les graphiques circulaires",
        "it": "Top N corsi per i grafici a torta",
    },
    "general_course_table_sub": {
        "pt": "Tabela combinada por Curso (Ingressantes / Concluintes / Matriculados)",
        "en": "Combined table by Course (Entrants / Graduates / Enrolled)",
        "es": "Tabla combinada por Curso (Ingresantes / Egresados / Matriculados)",
        "fr": "Tableau combiné par Cours (Entrants / Diplômés / Inscrits)",
        "it": "Tabella combinata per Corso (Immatricolati / Laureati / Iscritti)",
    },
    "general_course_pie_title": {
        "pt": "Pretos ({dtype}) por Curso - Top {n} + Outros ({year})",
        "en": "Black Students ({dtype}) by Course - Top {n} + Others ({year})",
        "es": "Negros ({dtype}) por Curso - Top {n} + Otros ({year})",
        "fr": "Étudiants Noirs ({dtype}) par Cours - Top {n} + Autres ({year})",
        "it": "Studenti Neri ({dtype}) per Corso - Top {n} + Altri ({year})",
    },
    "general_course_area_title": {
        "pt": "Participação dos Cursos no Total de Pretos ({dtype}) ao Longo do Tempo",
        "en": "Courses' Share of Total Black Students ({dtype}) Over Time",
        "es": "Participación de los Cursos en el Total de Negros ({dtype}) a lo Largo del Tiempo",
        "fr": "Part des Cours dans le Total des Étudiants Noirs ({dtype}) au Fil du Temps",
        "it": "Quota dei Corsi nel Totale degli Studenti Neri ({dtype}) nel Tempo",
    },
    "general_no_data_dtype": {
        "pt": "Sem dados para {dtype} ao longo do tempo.",
        "en": "No data for {dtype} over time.",
        "es": "Sin datos para {dtype} a lo largo del tiempo.",
        "fr": "Aucune donnée pour {dtype} au fil du temps.",
        "it": "Nessun dato per {dtype} nel tempo.",
    },
    "general_format_bar_sub": {
        "pt": "Representatividade por Formato (lado a lado) - {year}",
        "en": "Representativeness by Format (side by side) - {year}",
        "es": "Representatividad por Formato (lado a lado) - {year}",
        "fr": "Représentativité par Format (côte à côte) - {year}",
        "it": "Rappresentatività per Formato (fianco a fianco) - {year}",
    },
    "general_format_bar_title": {
        "pt": "Representatividade de Pretos por Formato em {year}",
        "en": "Black Students Representativeness by Format in {year}",
        "es": "Representatividad de Negros por Formato en {year}",
        "fr": "Représentativité des Étudiants Noirs par Format en {year}",
        "it": "Rappresentatività degli Studenti Neri per Formato in {year}",
    },
    "general_format_table_sub": {
        "pt": "Tabela por Formato",
        "en": "Table by Format",
        "es": "Tabla por Formato",
        "fr": "Tableau par Format",
        "it": "Tabella per Formato",
    },
    "general_format_evol_sub": {
        "pt": "Evolução Temporal por Formato e Tipo de Dado",
        "en": "Temporal Evolution by Format and Data Type",
        "es": "Evolución Temporal por Formato y Tipo de Dato",
        "fr": "Évolution Temporelle par Format et Type de Donnée",
        "it": "Evoluzione Temporale per Formato e Tipo di Dato",
    },
    "general_format_evol_title": {
        "pt": "Evolução da Representatividade por Formato",
        "en": "Evolution of Representativeness by Format",
        "es": "Evolución de la Representatividad por Formato",
        "fr": "Évolution de la Représentativité par Format",
        "it": "Evoluzione della Rappresentatività per Formato",
    },
    "general_inst_evol_sub": {
        "pt": "Evolução Temporal - Pública vs Privada por Tipo de Dado",
        "en": "Temporal Evolution - Public vs Private by Data Type",
        "es": "Evolución Temporal - Pública vs Privada por Tipo de Dato",
        "fr": "Évolution Temporelle - Public vs Privé par Type de Donnée",
        "it": "Evoluzione Temporale - Pubblica vs Privata per Tipo di Dato",
    },
    "general_inst_evol_title": {
        "pt": "Evolução da Representatividade por Categoria Administrativa - Pública vs Privada",
        "en": "Evolution of Representativeness by Administrative Category - Public vs Private",
        "es": "Evolución de la Representatividad por Categoría Administrativa - Pública vs Privada",
        "fr": "Évolution de la Représentativité par Catégorie Administrative - Public vs Privé",
        "it": "Evoluzione della Rappresentatività per Categoria Amministrativa - Pubblica vs Privata",
    },
    "general_region_evol_sub": {
        "pt": "Evolução Temporal por Região e Tipo de Dado",
        "en": "Temporal Evolution by Region and Data Type",
        "es": "Evolución Temporal por Región y Tipo de Dato",
        "fr": "Évolution Temporelle par Région et Type de Donnée",
        "it": "Evoluzione Temporale per Regione e Tipo di Dato",
    },
    "general_region_evol_title": {
        "pt": "Evolução da Representatividade por Região",
        "en": "Evolution of Representativeness by Region",
        "es": "Evolución de la Representatividad por Región",
        "fr": "Évolution de la Représentativité par Région",
        "it": "Evoluzione della Rappresentatività per Regione",
    },
    "participation_pct": {
        "pt": "Participação (%)",
        "en": "Share (%)",
        "es": "Participación (%)",
        "fr": "Part (%)",
        "it": "Quota (%)",
    },
    "category": {
        "pt": "Categoria",
        "en": "Category",
        "es": "Categoría",
        "fr": "Catégorie",
        "it": "Categoria",
    },
    "count": {
        "pt": "Contagem",
        "en": "Count",
        "es": "Conteo",
        "fr": "Nombre",
        "it": "Conteggio",
    },
    "annual_growth": {
        "pt": "Taxa de Crescimento (%)",
        "en": "Growth Rate (%)",
        "es": "Tasa de Crecimiento (%)",
        "fr": "Taux de Croissance (%)",
        "it": "Tasso di Crescita (%)",
    },
    "course": {
        "pt": "Curso",
        "en": "Course",
        "es": "Curso",
        "fr": "Cours",
        "it": "Corso",
    },
    # ── Institutional page missing keys ──────────────────────────────────────
    "inst_admin_category": {
        "pt": "Categoria Administrativa",
        "en": "Administrative Category",
        "es": "Categoría Administrativa",
        "fr": "Catégorie Administrative",
        "it": "Categoria Amministrativa",
    },
    "inst_type": {
        "pt": "Tipo de Instituição",
        "en": "Institution Type",
        "es": "Tipo de Institución",
        "fr": "Type d'Institution",
        "it": "Tipo di Istituzione",
    },
    # ── Format page missing keys ──────────────────────────────────────────────
    "format_label": {
        "pt": "Formato de Ensino",
        "en": "Teaching Format",
        "es": "Formato de Enseñanza",
        "fr": "Format d'Enseignement",
        "it": "Formato di Insegnamento",
    },
    "format_no_modal_col": {
        "pt": "Nenhuma coluna de modalidade encontrada no conjunto de dados. Colunas procuradas",
        "en": "No modality column found in dataset. Columns searched",
        "es": "No se encontró columna de modalidad en el conjunto de datos. Columnas buscadas",
        "fr": "Aucune colonne de modalité trouvée dans le jeu de données. Colonnes recherchées",
        "it": "Nessuna colonna di modalità trovata nel dataset. Colonne cercate",
    },
    # ── Projection page missing keys ──────────────────────────────────────────
    "proj_col_missing": {
        "pt": "Coluna '{col}' não encontrada. A projeção será baseada em zeros.",
        "en": "Column '{col}' not found. Projection will be based on zeros.",
        "es": "Columna '{col}' no encontrada. La proyección se basará en ceros.",
        "fr": "Colonne '{col}' introuvable. La projection sera basée sur des zéros.",
        "it": "Colonna '{col}' non trovata. La proiezione sarà basata su zeri.",
    },
    "proj_no_data": {
        "pt": "Sem dados temporais disponíveis para projeção.",
        "en": "No temporal data available for projection.",
        "es": "Sin datos temporales disponibles para proyección.",
        "fr": "Aucune donnée temporelle disponible pour la projection.",
        "it": "Nessun dato temporale disponibile per la proiezione.",
    },
    "proj_scipy_missing": {
        "pt": "O pacote scipy não está disponível. Instale via `pip install scipy` para habilitar regressão linear e projeções.",
        "en": "The scipy package is not available. Install via `pip install scipy` to enable linear regression and projections.",
        "es": "El paquete scipy no está disponible. Instálelo con `pip install scipy` para habilitar la regresión lineal y proyecciones.",
        "fr": "Le package scipy n'est pas disponible. Installez-le via `pip install scipy` pour activer la régression linéaire et les projections.",
        "it": "Il pacchetto scipy non è disponibile. Installarlo con `pip install scipy` per abilitare la regressione lineare e le proiezioni.",
    },
    "proj_regression_error": {
        "pt": "Erro ao calcular regressão: {error}",
        "en": "Error calculating regression: {error}",
        "es": "Error al calcular regresión: {error}",
        "fr": "Erreur lors du calcul de la régression : {error}",
        "it": "Errore nel calcolo della regressione: {error}",
    },
    "proj_history": {
        "pt": "Histórico",
        "en": "Historical",
        "es": "Histórico",
        "fr": "Historique",
        "it": "Storico",
    },
    "proj_trend": {
        "pt": "Tendência Linear (R²={r2})",
        "en": "Linear Trend (R²={r2})",
        "es": "Tendencia Lineal (R²={r2})",
        "fr": "Tendance Linéaire (R²={r2})",
        "it": "Tendenza Lineare (R²={r2})",
    },
    "proj_future": {
        "pt": "Projeção Futura",
        "en": "Future Projection",
        "es": "Proyección Futura",
        "fr": "Projection Future",
        "it": "Proiezione Futura",
    },
    "proj_meta": {
        "pt": "Meta populacional ({meta}%)",
        "en": "Population Target ({meta}%)",
        "es": "Meta poblacional ({meta}%)",
        "fr": "Objectif de population ({meta}%)",
        "it": "Obiettivo demografico ({meta}%)",
    },
    "proj_parity_label": {
        "pt": "Estimativa de Paridade",
        "en": "Parity Estimate",
        "es": "Estimación de Paridad",
        "fr": "Estimation de Parité",
        "it": "Stima di Parità",
    },
    "proj_chart_title": {
        "pt": "Tendência e Projeção de Representatividade ({dtype})",
        "en": "Representativeness Trend and Projection ({dtype})",
        "es": "Tendencia y Proyección de Representatividad ({dtype})",
        "fr": "Tendance et Projection de Représentativité ({dtype})",
        "it": "Tendenza e Proiezione della Rappresentatività ({dtype})",
    },
    "proj_stats_header": {
        "pt": "Estatísticas da Tendência",
        "en": "Trend Statistics",
        "es": "Estadísticas de la Tendencia",
        "fr": "Statistiques de la Tendance",
        "it": "Statistiche della Tendenza",
    },
    "proj_slope": {
        "pt": "Coeficiente angular (slope)",
        "en": "Slope coefficient",
        "es": "Coeficiente angular (slope)",
        "fr": "Coefficient directeur (pente)",
        "it": "Coefficiente angolare (slope)",
    },
    "proj_pvalue": {
        "pt": "P-valor",
        "en": "P-value",
        "es": "P-valor",
        "fr": "P-valeur",
        "it": "P-valore",
    },
    "proj_std_err": {
        "pt": "Erro padrão",
        "en": "Standard error",
        "es": "Error estándar",
        "fr": "Erreur standard",
        "it": "Errore standard",
    },
    "proj_significant_positive": {
        "pt": "Tendência estatisticamente significativa (p < 0.05). Crescimento estimado de +{slope}% ao ano.",
        "en": "Statistically significant trend (p < 0.05). Estimated growth of +{slope}% per year.",
        "es": "Tendencia estadísticamente significativa (p < 0.05). Crecimiento estimado de +{slope}% al año.",
        "fr": "Tendance statistiquement significative (p < 0,05). Croissance estimée de +{slope}% par an.",
        "it": "Tendenza statisticamente significativa (p < 0,05). Crescita stimata di +{slope}% all'anno.",
    },
    "proj_significant_negative": {
        "pt": "Tendência estatisticamente significativa (p < 0.05). Redução estimada de {slope}% ao ano.",
        "en": "Statistically significant trend (p < 0.05). Estimated reduction of {slope}% per year.",
        "es": "Tendencia estadísticamente significativa (p < 0.05). Reducción estimada de {slope}% al año.",
        "fr": "Tendance statistiquement significative (p < 0,05). Réduction estimée de {slope}% par an.",
        "it": "Tendenza statisticamente significativa (p < 0,05). Riduzione stimata di {slope}% all'anno.",
    },
    "proj_not_significant": {
        "pt": "Tendência não estatisticamente significativa (p ≥ 0.05).",
        "en": "Trend not statistically significant (p ≥ 0.05).",
        "es": "Tendencia no estadísticamente significativa (p ≥ 0.05).",
        "fr": "Tendance non statistiquement significative (p ≥ 0,05).",
        "it": "Tendenza non statisticamente significativa (p ≥ 0,05).",
    },
    "proj_meta_header": {
        "pt": "Comparação com meta populacional",
        "en": "Comparison with Population Target",
        "es": "Comparación con meta poblacional",
        "fr": "Comparaison avec l'objectif de population",
        "it": "Confronto con l'obiettivo demografico",
    },
    "proj_meta_value": {
        "pt": "Meta populacional (Pretos): {meta}% (Censo 2022)",
        "en": "Population target (Black students): {meta}% (2022 Census)",
        "es": "Meta poblacional (Negros): {meta}% (Censo 2022)",
        "fr": "Objectif de population (Étudiants noirs) : {meta}% (Recensement 2022)",
        "it": "Obiettivo demografico (Studenti neri): {meta}% (Censimento 2022)",
    },
    "proj_current": {
        "pt": "Representatividade atual: {val}%",
        "en": "Current representativeness: {val}%",
        "es": "Representatividad actual: {val}%",
        "fr": "Représentativité actuelle : {val}%",
        "it": "Rappresentatività attuale: {val}%",
    },
    "proj_gap": {
        "pt": "Gap: {gap} pontos percentuais",
        "en": "Gap: {gap} percentage points",
        "es": "Brecha: {gap} puntos porcentuales",
        "fr": "Écart : {gap} points de pourcentage",
        "it": "Gap: {gap} punti percentuali",
    },
    "proj_parity_estimate": {
        "pt": "Tempo estimado para paridade: {years} anos (aproximadamente no ano {year})",
        "en": "Estimated time to parity: {years} years (approximately year {year})",
        "es": "Tiempo estimado para la paridad: {years} años (aproximadamente en el año {year})",
        "fr": "Délai estimé pour atteindre la parité : {years} ans (approximativement en {year})",
        "it": "Tempo stimato per la parità: {years} anni (approssimativamente nell'anno {year})",
    },
    "proj_data_header": {
        "pt": "Dados Utilizados",
        "en": "Data Used",
        "es": "Datos Utilizados",
        "fr": "Données Utilisées",
        "it": "Dati Utilizzati",
    },
    "proj_for": {
        "pt": "Projeção para: {dtype}",
        "en": "Projection for: {dtype}",
        "es": "Proyección para: {dtype}",
        "fr": "Projection pour : {dtype}",
        "it": "Proiezione per: {dtype}",
    },
    # ── Course page missing keys ──────────────────────────────────────────────
    "course_slider": {
        "pt": "Número de Cursos para o Gráfico de Pizza",
        "en": "Number of Courses for Pie Chart",
        "es": "Número de Cursos para el Gráfico de Pastel",
        "fr": "Nombre de Cours pour le Graphique Circulaire",
        "it": "Numero di Corsi per il Grafico a Torta",
    },
    "other_courses": {
        "pt": "Outros Cursos",
        "en": "Other Courses",
        "es": "Otros Cursos",
        "fr": "Autres Cours",
        "it": "Altri Corsi",
    },
}


def get_language() -> str:
    """Retorna o código de idioma ativo ('pt', 'en', etc.)."""
    return st.session_state.get("lang", "pt")


def set_language(label: str) -> None:
    """Define o idioma ativo a partir do label exibido ao usuário."""
    st.session_state["lang"] = LANGUAGES.get(label, "pt")


def translate_dtype(pt_val: str) -> str:
    """
    Traduz um valor de tipo de dado em Português (chave interna) para o idioma ativo.
    Ex.: 'Ingressantes' → 'Entrants' em inglês.
    """
    _PT_TO_KEY = {
        'Ingressantes': 'dtype_entrants',
        'Concluintes':  'dtype_graduates',
        'Matriculados': 'dtype_enrolled',
    }
    key = _PT_TO_KEY.get(pt_val)
    if key:
        lang = get_language()
        return _STRINGS[key].get(lang) or pt_val
    return pt_val


def t(key: str, **kwargs) -> str:
    """
    Retorna a string traduzida para o idioma ativo.
    Aceita kwargs para interpolação: t("overview_header", dtype="Ingressantes", year=2023)
    O kwarg 'dtype' é automaticamente traduzido do Português para o idioma ativo.
    """
    lang = get_language()
    entry = _STRINGS.get(key, {})
    text = entry.get(lang) or entry.get("pt") or key
    # Remove indentação Python de strings multilinha (fix para renderização Markdown)
    text = inspect.cleandoc(text)
    if kwargs:
        # Traduz automaticamente o dtype do Português para o idioma ativo
        if 'dtype' in kwargs:
            kwargs = dict(kwargs)
            kwargs['dtype'] = translate_dtype(str(kwargs['dtype']))
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return text


def dtype_keys(lang: str | None = None) -> list[str]:
    """Retorna os três rótulos de tipo de dado no idioma ativo."""
    if lang is None:
        lang = get_language()
    return [
        _STRINGS["dtype_entrants"][lang],
        _STRINGS["dtype_graduates"][lang],
        _STRINGS["dtype_enrolled"][lang],
    ]


def dtype_to_pt(label: str) -> str:
    """Converte o rótulo localizado de volta para o equivalente em PT (chave interna)."""
    mapping = {}
    for key in ("dtype_entrants", "dtype_graduates", "dtype_enrolled"):
        for lv in _STRINGS[key].values():
            mapping[lv] = _STRINGS[key]["pt"]
    return mapping.get(label, label)
