"""
chart_theme.py
Define e registra um template Plotly personalizado com fontes maiores para
títulos, eixos e legendas. Basta chamar `apply()` uma vez na entrada do app.
"""

import plotly.io as pio
import plotly.graph_objects as go


def apply() -> None:
    """Registra e ativa o template 'censo' como padrão global do Plotly."""

    base = go.layout.Template(pio.templates["plotly"])

    base.layout.update(
        # ── Título do gráfico ──────────────────────────────────────────────
        title=dict(
            font=dict(size=20),
            x=0.5,
            xanchor="center",
        ),
        # ── Eixos ─────────────────────────────────────────────────────────
        xaxis=dict(
            title=dict(font=dict(size=15)),
            tickfont=dict(size=13),
        ),
        yaxis=dict(
            title=dict(font=dict(size=15)),
            tickfont=dict(size=13),
        ),
        # ── Legenda ───────────────────────────────────────────────────────
        legend=dict(
            title=dict(font=dict(size=14)),
            font=dict(size=13),
        ),
        # ── Tooltips ──────────────────────────────────────────────────────
        hoverlabel=dict(font=dict(size=13)),
    )

    pio.templates["censo"] = base
    pio.templates.default = "censo"
