import streamlit as st
import psycopg2
import pandas as pd
import os # Para gerenciar variáveis de ambiente

# 1. Configuração da Conexão com o NEON
# É altamente recomendável usar variáveis de ambiente (como no Node.js)
# para a string de conexão, especialmente na hospedagem.
DATABASE_URL = "postgresql://neondb_owner:npg_Iflxy7RMmnH6@ep-delicate-resonance-ahxuy5yh-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"

# 2. Função para Estabelecer a Conexão (usando cache do Streamlit)
# O decorador @st.cache_resource garante que a conexão seja criada apenas uma vez.
@st.cache_resource
def init_connection():
    # Retira o parâmetro 'channel_binding=require' para o driver Python 'psycopg2'
    # que costuma ser mais sensível à URL de conexão pura.
    return psycopg2.connect(DATABASE_URL)

# Inicializa a conexão
conn = init_connection()

# 3. Função para Executar a Query e Retornar como DataFrame
# O decorador @st.cache_data garante que a busca só seja refeita se a query mudar.
@st.cache_data(ttl=600) # O cache dura 10 minutos
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        # Pega os nomes das colunas
        columns = [desc[0] for desc in cur.description]
        # Pega os dados
        data = cur.fetchall()
        
        return pd.DataFrame(data, columns=columns)

# =========================================================================
# 4. Interface Streamlit
# =========================================================================

st.set_page_config(
    page_title="One Piece Database Dashboard 🏴‍☠️",
    layout="wide"
)

st.title("One Piece Database Dashboard 🏴‍☠️")
st.markdown("## Análise de Recompensas e Afilições")

# --- SELECTBOX PARA BUSCA INTERATIVA ---
st.sidebar.header("Filtros de Busca")

# Pega todos os nomes de Bandos existentes para o filtro
bandos_df = run_query("SELECT NomeBando FROM Bando ORDER BY NomeBando;")
bandos = bandos_df['nomebando'].tolist()
# Adiciona uma opção para ver todos
bandos.insert(0, "Todos os Bandos")

selected_bando = st.sidebar.selectbox(
    "Selecione o Bando:",
    bandos
)

# --- QUERY COMPLEXA COM BASE NA SELEÇÃO ---
if selected_bando == "Todos os Bandos":
    # Query para todos os piratas (simples)
    query_piratas = """
        SELECT
            p.NomePersonagem,
            p.Recompensa,
            b.NomeBando,
            a.NomeAlianca,
            n.NomeNavio
        FROM
            Pirata p
        LEFT JOIN
            Bando b ON p.NomeBando = b.NomeBando
        LEFT JOIN
            Alianca a ON b.NomeAlianca = a.NomeAlianca
        LEFT JOIN
            Navio n ON b.NomeBando = n.NomeBando
        ORDER BY
            p.Recompensa DESC;
    """
    st.subheader(f"Todos os Piratas ({len(bandos) - 1} Bandos)")
else:
    # Query complexa (3 JOINs) para um Bando específico
    query_piratas = f"""
        SELECT
            p.NomePersonagem,
            p.Recompensa,
            b.NomeBando,
            a.NomeAlianca,
            n.NomeNavio
        FROM
            Pirata p
        JOIN
            Bando b ON p.NomeBando = b.NomeBando
        LEFT JOIN
            Alianca a ON b.NomeAlianca = a.NomeAlianca
        LEFT JOIN
            Navio n ON b.NomeBando = n.NomeBando
        WHERE
            b.NomeBando = '{selected_bando}'
        ORDER BY
            p.Recompensa DESC;
    """
    st.subheader(f"Piratas do Bando: {selected_bando}")


# Executa a query e exibe os resultados
piratas_df = run_query(query_piratas)

# 5. Visualização de Dados
if not piratas_df.empty:
    st.dataframe(piratas_df)
    
    st.markdown("---")
    
    # Gráfico de Recompensas (Análise Visual)
    st.subheader("Visualização da Recompensa por Pirata")
    # Usa a função `st.bar_chart` do Streamlit para um gráfico rápido
    st.bar_chart(piratas_df.set_index('nomepersonagem')['recompensa'])

else:
    st.warning("Nenhum pirata encontrado com os filtros selecionados ou o pirata não está em um bando com navio/aliança.")

# --- ESTATÍSTICAS GLOBAIS (Requisito de Análise Estatística) ---
st.sidebar.markdown("---")
st.sidebar.header("Estatísticas Rápidas")

# Busca o valor da maior recompensa total de um bando
query_max_recompensa = "SELECT NomeBando, RecompensaTotalBando FROM Bando ORDER BY RecompensaTotalBando DESC LIMIT 1;"
max_recompensa_df = run_query(query_max_recompensa)
if not max_recompensa_df.empty:
    max_bando = max_recompensa_df.iloc[0]['nomebando']
    max_valor = max_recompensa_df.iloc[0]['recompensatotalbando']
    st.sidebar.metric(
        label="Maior Recompensa Total de Bando",
        value=f"B$ {max_valor:,.0f}",
        delta=max_bando
    )