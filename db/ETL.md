# ETL — Microdados → Consolidado → Banco Relacional

Documentação do pipeline de dados do projeto. As três etapas:

```
  MICRODADOS (INEP, 1 CSV por ano)
        │  (filtro + harmonização + concatenação)
        ▼
  dados_censo_computacao_consolidado.csv   (1 CSV "wide", 227 colunas)
        │  (db/etl.py)
        ▼
  db/censo.db   (SQLite — modelo relacional normalizado)
```

> A análise da Etapa A abaixo foi feita **somente sobre os cabeçalhos** dos
> microdados (não sobre o conteúdo).

---

## Etapa A — Microdados → Consolidado

### Fonte

`dados/microdados/MICRODADOS_CADASTRO_CURSOS_<ANO>.CSV`, anos **2009 a 2023**
no repositório (o consolidado também contém **2024** — ver nota adiante).

- **Separador:** `;`
- **Encoding:** `latin-1` (ISO-8859-1) — caracteres acentuados confirmados
  ao ler os cabeçalhos.
- **Granularidade:** uma linha por curso/oferta. O INEP chama este conjunto
  de *Cadastro de Cursos da Educação Superior*.

### Evolução do schema entre anos (via cabeçalhos)

| Período      | Nº de colunas | Observação |
|--------------|---------------|------------|
| 2009 – 2022  | 200           | Conjunto base estável |
| 2023         | 202           | Adiciona `IN_COMUNITARIA`, `IN_CONFESSIONAL` |
| 2024 (fora do repo) | +25 | Adiciona subcategorias de reserva de vaga |

Fatos relevantes detectados na comparação de cabeçalhos:

1. **A ordem das colunas muda entre anos** (2009 ≠ 2023 na ordem, embora as
   200 colunas comuns sejam as mesmas). Logo, a consolidação **alinha por
   nome de coluna, não por posição**.
2. **2009 não tem nenhuma coluna ausente em 2023** — o schema só cresce
   (aditivo); nenhuma coluna foi removida no período.
3. As 25 colunas extras presentes só no consolidado são:
   - `CO_CINE_ROTULO2` — coluna **derivada** (versão "limpa" de
     `CO_CINE_ROTULO`, que no CSV vem com aspas extras, ex.: `"""0615S02"""`).
   - 24 subcategorias de reserva de vaga:
     `QT_{ING,MAT,CONC}_RV{PPI,QUILO,REFU,POVT,IDOSO,INTERN,MEDAL,TRANS}`
     — introduzidas no microdado de **2024** (arquivo não versionado no
     repositório, mas cujos dados aparecem no consolidado: ~63 mil linhas de
     2024).

### Etapas inferidas do processamento

O script original de consolidação não está versionado; o processo abaixo é
**inferido** a partir do formato de entrada/saída e dos cabeçalhos:

1. **Para cada ano**, ler o microdado (`sep=';'`, `encoding='latin-1'`).
2. **Filtrar** apenas cursos de computação:
   `CO_CINE_AREA_GERAL == 6` ("Computação e Tecnologias da Informação e
   Comunicação (TIC)"). No banco gerado, `cine_area_geral` tem exatamente 1
   linha (código 6), confirmando o filtro.
3. **Harmonizar** os nomes de coluna para minúsculas
   (`NU_ANO_CENSO` → `nu_ano_censo`).
4. **Reindexar** cada ano para o *superset* de colunas de todos os anos
   (preenchendo com vazio onde a coluna não existia naquele ano — por isso
   anos antigos têm `in_comunitaria`/`qt_*_rvppi` nulos).
5. **Concatenar** todos os anos num único DataFrame.
6. **Derivar** `co_cine_rotulo2` a partir de `co_cine_rotulo` (remoção das
   aspas extras).
7. **Persistir** como `dados_censo_computacao_consolidado.csv`
   (`sep=','`, `encoding='utf-8'`, **227 colunas**, **319.196 linhas**).

### Grão do consolidado

A chave natural única do CSV consolidado é:

```
(nu_ano_censo, co_curso, co_municipio, tp_dimensao)
```

Verificado: 319.196 combinações distintas = 319.196 linhas (**0 duplicatas**).

Por que `co_curso` sozinho **não** é único por ano: cursos EaD têm uma linha
por **município de oferta (polo)** — um único `co_curso` chega a ter >1.100
municípios num mesmo ano. Isso explica o crescimento das linhas por ano
(3.012 em 2009 → 66.790 em 2023).

---

## Etapa B — Consolidado → SQLite (`db/etl.py`)

### Leitura e limpeza

- `pd.read_csv(..., encoding='utf-8', low_memory=False)`.
- `co_cine_rotulo` / `co_cine_rotulo2`: remoção de aspas (`"`) e strip;
  string vazia → `NULL`.
- Colunas `qt_*`, `co_*`, `tp_*`, `in_*`, `nu_*` (exceto `co_cine_rotulo*`):
  `pd.to_numeric(errors='coerce')` → `Int64` (inteiro nullable). Resolve os
  valores como `80.0`, `11.0` do CSV.
- Colunas `no_*`, `sg_*`: mantidas como texto; `NaN` → `NULL`.

### Construção das dimensões

Cada dimensão é derivada por `drop_duplicates()` sobre sua chave:

| Tabela | Origem | Tratamento de dado sujo |
|--------|--------|-------------------------|
| `ref_tp_*` | códigos distintos observados | descrição via **dicionário oficial do Censo 2024** (aba `cadastro_cursos`, coluna *Categoria*); código desconhecido → `"Código N"` |
| `regiao` / `uf` / `municipio` | colunas geográficas | nome ausente → `"Não informado"` (preserva ~980 linhas com `co_regiao=0`) |
| `cine_area_geral`/`_especifica`/`_detalhada`/`rotulo` | hierarquia CINE | idem fallback de nome |
| `ies` | `co_ies` distintos | — |
| `curso` | `co_curso` + nome representativo | grafia mais frequente (≈67% dos cursos variam o nome entre anos) |

> `tp_dimensao` (do dicionário oficial): 1 = cursos presenciais no Brasil;
> 2 = cursos a distância no Brasil; 3 = cursos a distância com dimensão de
> dados só a nível Brasil; 4 = cursos a distância ofertados por instituições
> brasileiras no exterior. Isso explica por que dimensões EaD (3/4) têm
> `co_municipio` nulo/0.

### Decisões de modelagem

- **Atributos que variam ano a ano ficam no FATO**, não em dimensões:
  `co_ies` (121 cursos mudam de IES), `co_cine_rotulo` (≈42% dos cursos
  mudam a classificação CINE), `co_municipio`, `tp_grau_academico`,
  `tp_modalidade_ensino` etc. `curso` guarda só `co_curso` + um nome
  representativo para rótulo.
- **PK do fato:** surrogate `id INTEGER PRIMARY KEY AUTOINCREMENT`. A chave
  natural `(nu_ano_censo, co_curso, co_municipio, tp_dimensao)` **não** é
  declarada `UNIQUE` porque `co_municipio` é nulo em ~4.681 linhas e o
  SQLite trata `NULL` como distinto (quebraria o `UNIQUE`). Em vez disso há
  um índice não-único cobrindo a chave; a unicidade já foi verificada na
  origem.
- **Ordem de carga:** lookups → geografia → CINE → IES → curso → fato.
- **Foreign keys** ficam desabilitadas durante a carga (`PRAGMA
  foreign_keys = OFF`); ao final roda-se `PRAGMA foreign_key_check` que
  apenas **reporta** órfãos sem abortar. Na carga atual: `integridade
  referencial: OK`.

### Validação automática (rodada ao final do script)

- Contagem total e por ano (16 censos, 2009–2024).
- `PRAGMA foreign_key_check`.

Conferência manual: a soma de `qt_ing` por ano via SQL é **idêntica** à
soma via pandas no CSV original (todos os 16 anos).

---

## Etapa C — Modelo relacional

```
regiao ─1:N─ uf ─1:N─ municipio ──────┐
                                       │ (co_municipio)
ies ──────────┐                        │
              │ (co_ies)               │
cine_area_geral ─1:N─ cine_area_especifica ─1:N─ cine_area_detalhada ─1:N─ cine_rotulo
              │                                                            │ (co_cine_rotulo)
              ▼                                                            │
        ┌──────────────────────── fato_curso_ano ──────────────────────────┘
        │  PK: id (surrogate)
        │  chave natural: (nu_ano_censo, co_curso, co_municipio, tp_dimensao)
        │  FKs: co_curso→curso, co_ies→ies, co_municipio→municipio,
        │       co_cine_rotulo→cine_rotulo, tp_*→ref_tp_*
        │  + ~180 métricas qt_*
        └──────────────── curso (co_curso, no_curso representativo)

ref_tp_dimensao · ref_tp_organizacao_academica · ref_tp_categoria_administrativa
ref_tp_rede · ref_tp_grau_academico · ref_tp_modalidade_ensino · ref_tp_nivel_academico
   (tabelas de lookup — code→descrição, referenciadas pelo fato)
```

**Tabelas (17) + 1 view:**

- Lookup: `ref_tp_dimensao`, `ref_tp_organizacao_academica`,
  `ref_tp_categoria_administrativa`, `ref_tp_rede`, `ref_tp_grau_academico`,
  `ref_tp_modalidade_ensino`, `ref_tp_nivel_academico`
- Geografia: `regiao`, `uf`, `municipio`
- CINE: `cine_area_geral`, `cine_area_especifica`, `cine_area_detalhada`,
  `cine_rotulo`
- Núcleo: `ies`, `curso`, `fato_curso_ano`
- View: `v_censo_consolidado` — reproduz a forma "wide" do CSV original
  (fato + todos os joins de dimensão já resolvidos).

---

## Etapa D — Como rodar e consultar

### Gerar o banco

```bash
pip install pandas                       # sqlite3 é stdlib
python db/etl.py                         # usa o CSV padrão e gera db/censo.db
python db/etl.py --csv <csv> --db <out>  # caminhos custom
```

O caminho padrão do CSV aponta para
`dados/dados_censo_computacao_consolidado.csv` na raiz do projeto principal.

### Consultar

```sql
-- Representatividade de pretos entre ingressantes, por ano
SELECT nu_ano_censo,
       SUM(qt_ing)               AS ingressantes,
       SUM(qt_ing_preta)         AS ingressantes_pretos,
       ROUND(100.0 * SUM(qt_ing_preta) / NULLIF(SUM(qt_ing), 0), 2) AS pct_pretos
FROM fato_curso_ano
GROUP BY nu_ano_censo
ORDER BY nu_ano_censo;
```

A view facilita análises que precisam dos rótulos de dimensão:

```sql
SELECT nu_ano_censo, no_regiao, no_cine_rotulo, SUM(qt_mat) AS matriculados
FROM v_censo_consolidado
GROUP BY nu_ano_censo, no_regiao, no_cine_rotulo;
```

### Leitura local pelo SQLite

O dashboard publicado lê do PostgreSQL no Supabase (materialized view
`mv_censo_rollup`, criada por `db/load_supabase.py`; ver o README da raiz).
Para ler o banco SQLite localmente:

```python
import sqlite3, pandas as pd
con = sqlite3.connect('db/censo.db')
df = pd.read_sql('SELECT * FROM v_censo_consolidado', con)
```

A `v_censo_consolidado` devolve as mesmas colunas esperadas pelas páginas
(`nu_ano_censo`, `qt_ing`, `qt_ing_preta`, `qt_conc`, `qt_mat`, etc.).
