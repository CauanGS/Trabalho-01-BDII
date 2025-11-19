import streamlit as st
import psycopg2
import pandas as pd

#Configuração do banco NEON
DATABASE_URL = "postgresql://neondb_owner:npg_Iflxy7RMmnH6@ep-delicate-resonance-ahxuy5yh-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"

@st.cache_resource
def init_connection():
    return psycopg2.connect(DATABASE_URL)

conn = init_connection()

#Função geral de execução
@st.cache_data(ttl=600)
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        columns = [desc[0] for desc in cur.description]
        data = cur.fetchall()
        return pd.DataFrame(data, columns=columns)


# Dicionário para renomear as colunas para um formato mais legível
col_names = {
    'nomepersonagem': 'Nome do Personagem',
    'recompensa': 'Recompensa',
    'nomebando': 'Nome do Bando',
    'nomealianca': 'Nome da Aliança',
    'nomenavio': 'Nome do Navio',
    'alcunha': 'Alcunha',
    'recompensaindividual': 'Recompensa Individual',
    'recompensatotalbando': 'Recompensa Total do Bando',
    'nomeespecie': 'Espécie',
    'nomefruta': 'Nome da Fruta',
    'tipofruta': 'Tipo da Fruta',
    'recompensacombinada': 'Recompensa Combinada',
    'rn': 'Ranking'
}

# Configuração da página
st.set_page_config(page_title="One Piece Database Dashboard", layout="wide")

st.title("One Piece Database Dashboard")
st.markdown("## Análise de Recompensas e Afilições")



#Consulta1 - Filtro de piratas por recompensa do banco
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
    #renomeação
    st.dataframe(piratas_bando_df.rename(columns=col_names))
else:
    st.info("Nenhum pirata encontrado com essa recompensa total de bando mínima.")

st.markdown("---")


#Consulta2 - Filtro de personagens com Akuma no Mi por espécie e tipo de fruta
st.markdown("## Personagens com Akuma no Mi – Espécie e Tipo de Fruta")

#Carregar espécies disponíveis
especies_df = run_query("SELECT DISTINCT NomeEspecie FROM Filiacao_Especie ORDER BY NomeEspecie;")
frutas_df = run_query("SELECT DISTINCT TipoFruta FROM AkumaNoMi ORDER BY TipoFruta;")

especies = ["Todas"] + especies_df["nomeespecie"].dropna().tolist()
tipos_fruta = ["Todos"] + frutas_df["tipofruta"].dropna().tolist()

col1, col2 = st.columns(2)
with col1:
    filtro_especie = st.selectbox("Filtrar por espécie:", especies)
with col2:
    filtro_fruta = st.selectbox("Filtrar por tipo de fruta:", tipos_fruta)

#Query base
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

#filtros
condicoes = []
if filtro_especie != "Todas":
    condicoes.append(f"f.NomeEspecie = '{filtro_especie}'")
if filtro_fruta != "Todos":
    condicoes.append(f"a.TipoFruta = '{filtro_fruta}'")

if condicoes:
    query_personagens_fruta += " WHERE " + " AND ".join(condicoes)

query_personagens_fruta += " ORDER BY p.NomePersonagem ASC;"


personagens_fruta_df = run_query(query_personagens_fruta)


if not personagens_fruta_df.empty:
    #renomeação
    st.dataframe(personagens_fruta_df.rename(columns=col_names))
else:
    st.info("Nenhum personagem encontrado com os filtros aplicados.")

st.markdown("---")



#Consulta 3 — Filtro de capitães de Bando por ranking por recompensa total cpm filtro de aliança
st.markdown("## Capitães de Bando – Ranking por Recompensa Total do Bando")

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

# query base 
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


query_capitaes += " ORDER BY b.RecompensaTotalBando DESC;"


capitaes_df = run_query(query_capitaes)


if not capitaes_df.empty:
    # Aplica a renomeação
    st.dataframe(capitaes_df.rename(columns=col_names))
else:
    st.info("Nenhum capitão encontrado com esse filtro.")

st.markdown("---")



st.markdown("## Periculosidade do Bando – Soma das Maiores Recompensas")

#Novo slider para definir o 'N' (quantos membros somar)
num_membros = st.slider(
    "Considerar os N membros com maiores recompensas:",
    min_value=1,
    max_value=20,
    value=3, # Valor padrão (Top 3)
    step=1
)

min_perigo = st.slider(
    f"Recompensa Combinada Mínima (Soma do TOP {num_membros}):",
    min_value=0,
    max_value=10000000000,
    value=0,
    step=50000000
)

filtro_alianca2 = st.selectbox("Filtrar por aliança (Periculosidade):", aliancas)

query_perigo = f"""
    WITH rank_piratas AS (
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
        SUM(rp.Recompensa) AS RecompensaCombinada
    FROM rank_piratas rp
    JOIN Bando b ON b.NomeBando = rp.NomeBando
    WHERE rp.rn <= {num_membros}
"""

if filtro_alianca2 != "Todas":
    query_perigo += f" AND b.NomeAlianca = '{filtro_alianca2}'\n"

query_perigo += f"""
GROUP BY b.NomeBando, b.NomeAlianca
HAVING SUM(rp.Recompensa) >= {min_perigo}
ORDER BY RecompensaCombinada DESC;
"""

perigo_df = run_query(query_perigo)

if not perigo_df.empty:
    # Renomeia as colunas antes de exibir
    perigo_display = perigo_df.rename(columns=col_names)
    
    st.dataframe(
        perigo_display,
        column_config={
            # Nota: Aqui usamos o NOVO nome da coluna após o rename
            "Recompensa Combinada": st.column_config.NumberColumn(
                f"Soma (Top {num_membros})",
                format="$%d" # Formata como moeda
            )
        }
    )
else:
    st.info("Nenhum bando encontrado com esse critério.")

st.markdown("---")


# Consulta 4 — Rastreamento de Poneglyphs e Contexto Histórico


st.sidebar.header("Estatísticas do Mundo")

#Recordes de recompensa
st.sidebar.subheader("Os Mais Procurados")

# Consulta para Maior Bando e Maior Pirata
query_recordes = """
    SELECT 
        -- Maior Bando
        (SELECT NomeBando FROM Bando ORDER BY RecompensaTotalBando DESC LIMIT 1) as nome_bando,
        (SELECT RecompensaTotalBando FROM Bando ORDER BY RecompensaTotalBando DESC LIMIT 1) as valor_bando,
        -- Maior Pirata
        (SELECT p.NomePersonagem FROM Pirata pi JOIN Personagem p ON pi.NomePersonagem = p.NomePersonagem ORDER BY pi.Recompensa DESC LIMIT 1) as nome_pirata,
        (SELECT Recompensa FROM Pirata ORDER BY Recompensa DESC LIMIT 1) as valor_pirata
"""
recordes_df = run_query(query_recordes)

if not recordes_df.empty:
    # Dados do Bando
    nome_bando = recordes_df.iloc[0]['nome_bando']
    valor_bando = recordes_df.iloc[0]['valor_bando']
    
    # Dados do Pirata
    nome_pirata = recordes_df.iloc[0]['nome_pirata']
    valor_pirata = recordes_df.iloc[0]['valor_pirata']

    st.sidebar.metric(
        label="Maior Recompensa (Bando)",
        value=f"B$ {valor_bando:,.0f}",
        delta=nome_bando
    )
    
    st.sidebar.metric(
        label="Maior Recompensa (Individual)",
        value=f"B$ {valor_pirata:,.0f}",
        delta=nome_pirata
    )

#Pop e frutas
st.sidebar.markdown("---")
st.sidebar.subheader("População & Poder")

# Nota: Usamos ILIKE '%Zoan%' para pegar 'Zoan Mítica', 'Zoan Ancestral', etc.
query_counts = """
    SELECT 
        (SELECT COUNT(*) FROM Pirata) as qtd_piratas,
        (SELECT COUNT(*) FROM Marinheiro) as qtd_marinha,
        (SELECT COUNT(*) FROM AkumaNoMi) as qtd_frutas,
        (SELECT COUNT(*) FROM AkumaNoMi WHERE TipoFruta ILIKE '%Logia%') as qtd_logia,
        (SELECT COUNT(*) FROM AkumaNoMi WHERE TipoFruta ILIKE '%Zoan%') as qtd_zoan,
        (SELECT COUNT(*) FROM AkumaNoMi WHERE TipoFruta ILIKE '%Paramecia%') as qtd_paramecia
"""
counts_df = run_query(query_counts)

if not counts_df.empty:
    #Totais Gerais
    c1, c2 = st.sidebar.columns(2)
    c1.metric(" Piratas", counts_df.iloc[0]['qtd_piratas'])
    c2.metric("Marinha", counts_df.iloc[0]['qtd_marinha'])
    
    st.sidebar.markdown("---")
    # Detalhe Akuma no Mi
    st.sidebar.markdown("**Akuma no Mi (Distribuição)**")
    col_f1, col_f2, col_f3 = st.sidebar.columns(3)
    
    #métricas
    col_f1.metric("Paramecia", counts_df.iloc[0]['qtd_paramecia'])
    col_f2.metric("Zoan", counts_df.iloc[0]['qtd_zoan'], help="Inclui Míticas, Ancestrais e Artificiais")
    col_f3.metric("Logia", counts_df.iloc[0]['qtd_logia'])

#Geografia e navios
st.sidebar.markdown("---")
st.sidebar.subheader(" Geografia & Navios")

query_geo = """
    SELECT 
        (SELECT COUNT(*) FROM Ilha) as total_ilhas,
        (SELECT COUNT(*) FROM Navio WHERE Navegando = TRUE) as navios_ativos
"""
geo_df = run_query(query_geo)

if not geo_df.empty:
    g1, g2 = st.sidebar.columns(2)
    g1.metric("Ilhas Registradas", geo_df.iloc[0]['total_ilhas'])
    g2.metric("Navios no Mar", geo_df.iloc[0]['navios_ativos'])