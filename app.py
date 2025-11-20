import streamlit as st
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import os
import plotly.express as px
from sklearn.cluster import KMeans

DATABASE_URL = os.environ.get("DATABASE_URL")

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
    'Recompensa': 'Recompensa Individual',
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


# CRIAÇÃO DAS ABAS DO DASHBOARD
aba_consultas, aba_dashboard, aba_estatisticas = st.tabs(
    ["Consultas", "Dashboard", "Estatísticas Avançadas"]
)

with aba_consultas:
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
            pir.Recompensa AS Recompensa,
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

    st.markdown("## 🗺️ Rastreamento de Poneglyphs e História Antiga")

    st.markdown("""
    Esta seção cruza a localização dos **Poneglyphs** com as **Ilhas**, a **Afiliação Política** do território 
    e a **Região** onde se encontram.
    """)

    # Filtros para Poneglyphs
    tipos_poneglyph_df = run_query("SELECT DISTINCT unnest(enum_range(NULL::tipo_poneglyph)) as tipo;")
    areas_df = run_query("SELECT DISTINCT NomeArea FROM Area ORDER BY NomeArea;")

    tipos_poneglyph = ["Todos"] + tipos_poneglyph_df["tipo"].tolist()
    areas = ["Todas"] + areas_df["nomearea"].tolist()

    col_p1, col_p2 = st.columns(2)

    with col_p1:
        filtro_tipo_pone = st.selectbox("Tipo de Poneglyph:", tipos_poneglyph)

    with col_p2:
        filtro_area = st.selectbox("Região (Área do Mar):", areas)

    # Query Simplificada (Sem JOIN com Capítulos)
    query_poneglyphs = """
        SELECT 
            p.Tipo,
            p.Conteudo,
            i.NomeIlha,
            i.Filiacao AS FiliacaoPolitica,
            a.NomeArea
        FROM Poneglyph p
        JOIN Ilha i ON p.NomeIlha = i.NomeIlha
        JOIN Area a ON i.NomeArea = a.NomeArea
    """

    condicoes_pone = []
    if filtro_tipo_pone != "Todos":
        condicoes_pone.append(f"p.Tipo = '{filtro_tipo_pone}'")
    if filtro_area != "Todas":
        condicoes_pone.append(f"a.NomeArea = '{filtro_area}'")

    if condicoes_pone:
        query_poneglyphs += " WHERE " + " AND ".join(condicoes_pone)

    query_poneglyphs += " ORDER BY p.Tipo, i.NomeIlha;"

    poneglyphs_df = run_query(query_poneglyphs)

    # Dicionário simplificado para renomear colunas
    col_names_pone = {
        'tipo': 'Tipo de Poneglyph',
        'conteudo': 'Conteúdo/Detalhe',
        'nomeilha': 'Localização (Ilha)',
        'filiacaopolitica': 'Controle da Ilha',
        'nomearea': 'Mar/Região'
    }

    if not poneglyphs_df.empty:
        # Exibe a tabela renomeada
        st.dataframe(poneglyphs_df.rename(columns=col_names_pone))
        
        # Visualização gráfica da distribuição por região
        st.markdown("### Distribuição de Poneglyphs por Região")
        distribuicao = poneglyphs_df['nomearea'].value_counts()
        st.bar_chart(distribuicao)
    else:
        st.info("Nenhum Poneglyph encontrado com os filtros selecionados.")

    st.markdown("---")

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


# Análise estatística e visualização
def stats_piratas():
    st.header("giPiratas — Estatísticas")

    df_count = run_query("SELECT COUNT(*) AS total_piratas FROM pirata;")
    st.metric("Total de Piratas", int(df_count.iloc[0]['total_piratas']))

    q = """
    SELECT
        AVG(recompensa) AS media,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY recompensa) AS mediana,
        STDDEV(recompensa) AS desvio,
        MIN(recompensa) AS minimo,
        MAX(recompensa) AS maximo
    FROM pirata;
    """
    stats = run_query(q)

    row = stats.iloc[0]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Média", f"{row['media']:,}")
    c2.metric("Mediana", f"{row['mediana']:,}")
    c3.metric("Desvio Padrão", f"{row['desvio']:,}")
    c4.metric("Menor", f"{row['minimo']:,}")
    c5.metric("Maior", f"{row['maximo']:,}")

    # Top 10 piratas
    top10 = run_query("""
        SELECT nomepersonagem AS nomepirata, recompensa AS recompensa
        FROM pirata
        ORDER BY recompensa DESC
        LIMIT 10;
    """)

    if not top10.empty:
        st.subheader("Top 10 Piratas por Recompensa")
        fig = px.bar(top10, x="nomepirata", y="recompensa", text="recompensa")
        fig.update_traces(texttemplate='%{text:,}')
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(top10)

    shichi = run_query("SELECT COUNT(*) AS total_shichibukai FROM Pirata WHERE Shichibukai = TRUE;")
    if not shichi.empty:
        st.metric("Shichibukai", int(shichi.iloc[0]['total_shichibukai']))


def stats_bandos():
    st.header("Bandos — Análises")

    total = run_query("SELECT COUNT(*) AS total_bandos FROM bando;")
    st.metric("Total de Bandos", int(total.iloc[0]['total_bandos']))

    avg = run_query("SELECT AVG(recompensatotalbando) AS media_bando FROM bando;")
    st.metric("Média de Recompensa Total", f"{avg.iloc[0]['media_bando']:,}")

    # Top bandos
    top = run_query("""
        SELECT nomebando, recompensatotalbando
        FROM bando
        ORDER BY recompensatotalbando DESC
        LIMIT 10;
    """)

    if not top.empty:
        fig = px.bar(
            top,
            y="nomebando",
            x="recompensatotalbando",
            orientation="h",
            text="recompensatotalbando"
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(top)

    # Relação capitão vs bando
    rel = run_query("""
        SELECT 
            b.nomebando,
            p.recompensa AS recompensacapitao,
            b.recompensatotalbando,
            CASE 
                WHEN p.recompensa > 0 THEN ROUND(b.recompensatotalbando::numeric / p.recompensa::numeric, 2)
                ELSE NULL
            END AS multiplicador
        FROM bando b
        JOIN pirata p ON p.nomepersonagem = b.piratacapitao
        ORDER BY multiplicador DESC NULLS LAST;
    """)

    if not rel.empty:
        st.subheader("Multiplicador: Capitão vs Bando")
        st.dataframe(rel)

def stats_aliancas():
    st.header("Alianças")

    total = run_query("SELECT COUNT(*) AS total_aliancas FROM alianca;")
    st.metric("Total de Alianças", int(total.iloc[0]['total_aliancas']))

    top = run_query("""
        SELECT nomealianca, recompensatotalalianca
        FROM alianca
        ORDER BY recompensatotalalianca DESC;
    """)

    if not top.empty:
        fig = px.bar(top, x="nomealianca", y="recompensatotalalianca", text="recompensatotalalianca")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(top)

    bandos = run_query("""
        SELECT nomealianca, COUNT(*) AS total_bandos
        FROM bando
        WHERE nomealianca IS NOT NULL
        GROUP BY nomealianca;
    """)

    if not bandos.empty:
        st.subheader("Bandos por Aliança")
        st.dataframe(bandos)

def stats_frutas():
    st.header("Akuma no Mi")

    cnt = run_query("SELECT COUNT(*) AS total_frutas FROM akumanomi;")
    st.metric("Total de Frutas", int(cnt.iloc[0]['total_frutas']))

    tipos = run_query("""
        SELECT tipofruta, COUNT(*) AS total
        FROM akumanomi
        GROUP BY tipofruta;
    """)

    if not tipos.empty:
        fig = px.pie(tipos, names="tipofruta", values="total")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(tipos)

    media = run_query("""
        SELECT 
            a.tipofruta,
            AVG(p.recompensa) AS mediarecompensa
        FROM pirata p
        JOIN posse_fruta pf ON p.nomepersonagem = pf.nomepersonagem
        JOIN akumanomi a ON pf.nomefruta = a.nomefruta
        GROUP BY a.tipofruta
        ORDER BY mediarecompensa DESC;
    """)

    if not media.empty:
        fig = px.bar(media, x="tipofruta", y="mediarecompensa", text="mediarecompensa")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(media)

def stats_especies():
    st.header("Espécies")

    qtd = run_query("SELECT COUNT(*) AS total_especies FROM especie;")
    st.metric("Total de Espécies", int(qtd.iloc[0]['total_especies']))

    personagens = run_query("""
        SELECT nomeespecie, COUNT(*) AS total_personagens
        FROM filiacao_especie
        GROUP BY nomeespecie
        ORDER BY total_personagens DESC;
    """)

    if not personagens.empty:
        st.subheader("Personagens por Espécie")
        st.dataframe(personagens)

    media = run_query("""
        SELECT fe.nomeespecie, AVG(p.recompensa) AS mediarecompensa
        FROM pirata p
        JOIN filiacao_especie fe ON p.nomepersonagem = fe.nomepersonagem
        GROUP BY fe.nomeespecie
        ORDER BY mediarecompensa DESC;
    """)

    if not media.empty:
        fig = px.bar(media, x="nomeespecie", y="mediarecompensa")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(media)

def stats_navios():
    st.header("Navios")

    total = run_query("SELECT COUNT(*) AS total_navios FROM navio;")
    st.metric("Total de Navios", int(total.iloc[0]['total_navios']))

    por_bando = run_query("""
        SELECT nomebando, COUNT(*) AS total_navios
        FROM navio
        GROUP BY nomebando;
    """)

    st.subheader("Navios por Bando")
    st.dataframe(por_bando)


def stats_ilhas_capitulos():
    st.header("Ilhas & Capítulos")

    ilhas = run_query("SELECT COUNT(*) AS total_ilhas FROM ilha;")
    st.metric("Total de Ilhas", int(ilhas.iloc[0]['total_ilhas']))

    cap = run_query("""
        SELECT nomeilha, COUNT(*) AS total_capitulos
        FROM localizacao_capitulo
        GROUP BY nomeilha;
    """)

    if not cap.empty:
        st.subheader("Capítulos por Ilha")
        st.dataframe(cap)

    aparicoes = run_query("""
        SELECT nomepersonagem, COUNT(*) AS aparicoes
        FROM aparicao_em_capitulo
        GROUP BY nomepersonagem
        ORDER BY aparicoes DESC
        LIMIT 10;
    """)

    if not aparicoes.empty:
        st.subheader("Personagens com mais aparições")
        st.dataframe(aparicoes)


def stats_habilidades():
    st.header("Habilidades")

    total = run_query("SELECT COUNT(*) AS total_habs FROM habilidade;")
    st.metric("Total de Habilidades", int(total.iloc[0]['total_habs']))

    ranking = run_query("""
        SELECT nomepersonagem, COUNT(*) AS qtd_habs
        FROM lista_habilidade
        GROUP BY nomepersonagem
        ORDER BY qtd_habs DESC
        LIMIT 10;
    """)

    if not ranking.empty:
        st.subheader("Personagens com mais habilidades")
        st.dataframe(ranking)

def stats_clusters_outliers():
    st.header("Clusters e Outliers")

    df = run_query("SELECT nomepersonagem AS nomepirata, recompensa AS recompensaindividual FROM pirata;")

    # cluster
    X = df[["recompensaindividual"]].dropna()

    if X.empty:
        st.info("Dados insuficientes.")
    else:
        k = st.slider("Número de clusters", 2, 8, 3)
        kmeans = KMeans(n_clusters=k, random_state=42)
        df["cluster"] = kmeans.fit_predict(X)

        fig = px.scatter(df, x=df.index, y="recompensaindividual", color="cluster",
                         hover_name="nomepirata")
        st.plotly_chart(fig, use_container_width=True)

    # outliers
    q1 = df["recompensaindividual"].quantile(0.25)
    q3 = df["recompensaindividual"].quantile(0.75)
    iqr = q3 - q1
    limite = q3 + 1.5 * iqr

    outliers = df[df["recompensaindividual"] > limite]

    st.subheader("Outliers")
    st.dataframe(outliers)


tabs_extra = st.tabs([
    "Piratas",
    "Bandos",
    "Alianças",
    "Akuma no Mi",
    "Espécies",
    "Navios",
    "Ilhas & Capítulos",
    "Habilidades",
    "Clusters & Outliers"
])

with tabs_extra[0]:
    stats_piratas()

with tabs_extra[1]:
    stats_bandos()

with tabs_extra[2]:
    stats_aliancas()

with tabs_extra[3]:
    stats_frutas()

with tabs_extra[4]:
    stats_especies()

with tabs_extra[5]:
    stats_navios()

with tabs_extra[6]:
    stats_ilhas_capitulos()

with tabs_extra[7]:
    stats_habilidades()

with tabs_extra[8]:
    stats_clusters_outliers()
