import streamlit as st
import psycopg2
import pandas as pd

# 1. Configuração do banco NEON
DATABASE_URL = "postgresql://neondb_owner:npg_Iflxy7RMmnH6@ep-delicate-resonance-ahxuy5yh-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"

@st.cache_resource
def init_connection():
    return psycopg2.connect(DATABASE_URL)

conn = init_connection()

# 2. Função geral de execução
@st.cache_data(ttl=600)
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        columns = [desc[0] for desc in cur.description]
        data = cur.fetchall()
        return pd.DataFrame(data, columns=columns)

# =====================================================================
# INTERFACE PRINCIPAL
# =====================================================================

st.set_page_config(page_title="One Piece Database Dashboard 🏴‍☠️", layout="wide")

st.title("One Piece Database Dashboard 🏴‍☠️")
st.markdown("## Análise de Recompensas e Afilições")

# =====================================================================
# FILTRO INICIAL POR BANDO (CÓDIGO ORIGINAL)
# =====================================================================

st.sidebar.header("Filtros de Busca")

bandos_df = run_query("SELECT NomeBando FROM Bando ORDER BY NomeBando;")
bandos = bandos_df['nomebando'].tolist()
bandos.insert(0, "Todos os Bandos")

selected_bando = st.sidebar.selectbox("Selecione o Bando:", bandos)

if selected_bando == "Todos os Bandos":
    query_piratas = """
        SELECT
            p.NomePersonagem,
            p.Recompensa,
            b.NomeBando,
            a.NomeAlianca,
            n.NomeNavio
        FROM Pirata p
        LEFT JOIN Bando b ON p.NomeBando = b.NomeBando
        LEFT JOIN Alianca a ON b.NomeAlianca = a.NomeAlianca
        LEFT JOIN Navio n ON b.NomeBando = n.NomeBando
        ORDER BY p.Recompensa DESC;
    """
    st.subheader("Todos os Piratas")
else:
    query_piratas = f"""
        SELECT
            p.NomePersonagem,
            p.Recompensa,
            b.NomeBando,
            a.NomeAlianca,
            n.NomeNavio
        FROM Pirata p
        JOIN Bando b ON p.NomeBando = b.NomeBando
        LEFT JOIN Alianca a ON b.NomeAlianca = a.NomeAlianca
        LEFT JOIN Navio n ON b.NomeBando = n.NomeBando
        WHERE b.NomeBando = '{selected_bando}'
        ORDER BY p.Recompensa DESC;
    """
    st.subheader(f"Piratas do Bando: {selected_bando}")

piratas_df = run_query(query_piratas)

if not piratas_df.empty:
    st.dataframe(piratas_df)
    st.markdown("---")
    st.subheader("Visualização da Recompensa por Pirata")
    st.bar_chart(piratas_df.set_index('nomepersonagem')['recompensa'])
else:
    st.warning("Nenhum pirata encontrado.")

# =====================================================================
# =====================================================================
# ====================  CONSULTAS DA HANNAH ===========================
# =====================================================================
# =====================================================================

# =====================================================================
# CONSULTA 1 — Piratas filtrados pela Recompensa Total do Bando
# =====================================================================

st.markdown("##  Piratas filtrados pela Recompensa Total do Bando")

min_recompensa_bando = st.slider(
    "Recompensa total mínima do bando (em berries):",
    min_value=0,
    max_value=8000000000,
    value=0,
    step=50000000
)

query_piratas_por_bando = f"""
    SELECT
        p.NomePersonagem,
        p.Alcunha,
        pir.Recompensa AS RecompensaIndividual,
        b.NomeBando,
        b.RecompensaTotalBando,
        b.NomeAlianca
    FROM Pirata pir
    JOIN Personagem p ON pir.NomePersonagem = p.NomePersonagem
    JOIN Bando b ON pir.NomeBando = b.NomeBando
    WHERE b.RecompensaTotalBando >= {min_recompensa_bando}
    ORDER BY b.RecompensaTotalBando DESC, pir.Recompensa DESC;
"""

piratas_bando_df = run_query(query_piratas_por_bando)

if not piratas_bando_df.empty:
    st.dataframe(piratas_bando_df)
else:
    st.info("Nenhum pirata encontrado com essa recompensa total de bando mínima.")

st.markdown("---")


# =====================================================================
# CONSULTA 2 — Personagens com Akuma no Mi filtrados por Espécie e Tipo de Fruta
# =====================================================================

st.markdown("## 🧬 Personagens com Akuma no Mi – Espécie e Tipo de Fruta")

# 1. Carregar espécies disponíveis
especies_df = run_query("SELECT DISTINCT NomeEspecie FROM Filiacao_Especie ORDER BY NomeEspecie;")
frutas_df = run_query("SELECT DISTINCT TipoFruta FROM AkumaNoMi ORDER BY TipoFruta;")

especies = ["Todas"] + especies_df["nomeespecie"].dropna().tolist()
tipos_fruta = ["Todos"] + frutas_df["tipofruta"].dropna().tolist()

col1, col2 = st.columns(2)
with col1:
    filtro_especie = st.selectbox("Filtrar por espécie:", especies)
with col2:
    filtro_fruta = st.selectbox("Filtrar por tipo de fruta:", tipos_fruta)

# 2. Query base (Personagem + Especie + Fruta)
query_personagens_fruta = """
    SELECT 
        p.NomePersonagem,
        p.Alcunha,
        f.NomeEspecie,
        pf.NomeFruta,
        a.TipoFruta
    FROM Personagem p
    JOIN Filiacao_Especie f ON p.NomePersonagem = f.NomePersonagem
    JOIN Posse_Fruta pf ON p.NomePersonagem = pf.NomePersonagem
    JOIN AkumaNoMi a ON pf.NomeFruta = a.NomeFruta
"""

# 3. Montar filtros
condicoes = []
if filtro_especie != "Todas":
    condicoes.append(f"f.NomeEspecie = '{filtro_especie}'")
if filtro_fruta != "Todos":
    condicoes.append(f"a.TipoFruta = '{filtro_fruta}'")

if condicoes:
    query_personagens_fruta += " WHERE " + " AND ".join(condicoes)

query_personagens_fruta += " ORDER BY p.NomePersonagem ASC;"

# 4. Executar
personagens_fruta_df = run_query(query_personagens_fruta)

# 5. Mostrar
if not personagens_fruta_df.empty:
    st.dataframe(personagens_fruta_df)
else:
    st.info("Nenhum personagem encontrado com os filtros aplicados.")

st.markdown("---")


# =====================================================================
# CONSULTA 3 — Capitães de Bando (ranking por recompensa total)
# =====================================================================

st.markdown("## 🏴‍☠️ Capitães de Bando – Ranking por Recompensa Total do Bando")

# Carregar alianças
aliancas_df = run_query("""
    SELECT DISTINCT NomeAlianca 
    FROM Bando 
    WHERE NomeAlianca IS NOT NULL 
    ORDER BY NomeAlianca;
""")
aliancas = ["Todas"] + aliancas_df["nomealianca"].dropna().tolist()

# Filtro por aliança
filtro_alianca = st.selectbox("Filtrar por aliança:", aliancas)

# Query base (sem filtro de recompensa!)
query_capitaes = """
    SELECT 
        pr.NomePersonagem,
        p.Alcunha,
        pr.Recompensa,
        b.NomeBando,
        b.RecompensaTotalBando,
        b.NomeAlianca
    FROM Pirata pr
    JOIN Personagem p ON pr.NomePersonagem = p.NomePersonagem
    JOIN Bando b ON pr.NomePersonagem = b.PirataCapitao
"""

# Filtro opcional por aliança
if filtro_alianca != "Todas":
    query_capitaes += f" WHERE b.NomeAlianca = '{filtro_alianca}'\n"

# Ordenação final
query_capitaes += " ORDER BY b.RecompensaTotalBando DESC;"

# Executar
capitaes_df = run_query(query_capitaes)

# Exibir
if not capitaes_df.empty:
    st.dataframe(capitaes_df)
else:
    st.info("Nenhum capitão encontrado com esse filtro.")

st.markdown("---")

# =====================================================================
# CONSULTA 4 — Periculosidade do Bando (TOP 3)
# =====================================================================

st.markdown("##  Periculosidade do Bando – TOP 3 Recompensas Mais Altas")

min_perigo = st.slider(
    "Índice mínimo de periculosidade (soma do TOP 3):",
    min_value=0,
    max_value=10000000000,
    value=0,
    step=50000000
)

filtro_alianca2 = st.selectbox("Filtrar por aliança (Periculosidade):", aliancas)

query_perigo = f"""
    WITH top3_por_bando AS (
        SELECT
            NomeBando,
            NomePersonagem,
            Recompensa,
            ROW_NUMBER() OVER (
                PARTITION BY NomeBando
                ORDER BY Recompensa DESC
            ) AS rn
        FROM Pirata
    )
    SELECT 
        b.NomeBando,
        b.NomeAlianca,
        SUM(t3.Recompensa) AS PericulosidadeTOP3
    FROM top3_por_bando t3
    JOIN Bando b ON b.NomeBando = t3.NomeBando
    WHERE t3.rn <= 3
"""

if filtro_alianca2 != "Todas":
    query_perigo += f" AND b.NomeAlianca = '{filtro_alianca2}'\n"

query_perigo += f"""
GROUP BY b.NomeBando, b.NomeAlianca
HAVING SUM(t3.Recompensa) >= {min_perigo}
ORDER BY PericulosidadeTOP3 DESC;
"""

perigo_df = run_query(query_perigo)

if not perigo_df.empty:
    st.dataframe(perigo_df)
else:
    st.info("Nenhum bando encontrado com esse índice de periculosidade.")

st.markdown("---")

# =====================================================================
# ESTATÍSTICAS RÁPIDAS (original)
# =====================================================================

st.sidebar.markdown("---")
st.sidebar.header("Estatísticas Rápidas")

query_max_recompensa = """
SELECT NomeBando, RecompensaTotalBando 
FROM Bando 
ORDER BY RecompensaTotalBando DESC LIMIT 1;
"""

max_recompensa_df = run_query(query_max_recompensa)
if not max_recompensa_df.empty:
    max_bando = max_recompensa_df.iloc[0]['nomebando']
    max_valor = max_recompensa_df.iloc[0]['recompensatotalbando']
    st.sidebar.metric(
        label="Maior Recompensa Total de Bando",
        value=f"B$ {max_valor:,.0f}",
        delta=max_bando
    )
