import os
import zipfile
import pandas as pd
import streamlit as st
from PIL import Image
from io import BytesIO
import base64
import requests
import json
import time

# ========== CONFIGURAÇÕES DA PÁGINA ==========
st.set_page_config(
    page_title="Grupo Alquimistas Digitais - Análise de NFs", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CONFIGURAÇÕES DA API ==========
API_BASE_URL = "http://localhost:5000/api"

# ========== FUNÇÃO PARA IMAGEM CIRCULAR ==========
def circular_image_base64(image_path, size=60):
    try:
        img = Image.open(image_path).convert("RGBA")
        img = img.resize((size, size))

        # Máscara circular
        mask = Image.new("L", img.size, 0)
        for x in range(size):
            for y in range(size):
                if (x - size / 2) ** 2 + (y - size / 2) ** 2 <= (size / 2) ** 2:
                    mask.putpixel((x, y), 255)
        img.putalpha(mask)

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()
    except FileNotFoundError:
        return None

# ========== FUNÇÕES DA API ==========
def check_api_health():
    """Verifica se a API está funcionando"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        return None

def get_data_summary():
    """Busca resumo dos dados da API"""
    try:
        response = requests.get(f"{API_BASE_URL}/summary", timeout=10)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Erro ao buscar resumo: {str(e)}")
        return None

def send_query(question):
    """Envia pergunta para a API"""
    try:
        payload = {"question": question}
        response = requests.post(
            f"{API_BASE_URL}/query", 
            json=payload, 
            timeout=30
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Erro ao enviar pergunta: {str(e)}")
        return None

# ========== CSS PERSONALIZADO ==========
st.markdown("""
    <style>
    .header-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 20px;
        margin-top: 20px;
        margin-bottom: 30px;
    }
    .header-title {
        font-size: 2.5em;
        font-weight: bold;
        color: #FFD700;
    }
    .subtitle {
        text-align: center;
        font-size: 1.2em;
        color: #CCCCCC;
        margin-bottom: 30px;
    }
    .stApp {
        background-color: #0D1B2A;
    }
    .status-indicator {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .status-ok {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    .status-error {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    .status-warning {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }
    .chat-container {
        max-height: 400px;
        overflow-y: auto;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .user-message {
        background-color: #007bff;
        color: white;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
        text-align: right;
    }
    .bot-message {
        background-color: #f8f9fa;
        color: #333;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
        text-align: left;
    }
    </style>
""", unsafe_allow_html=True)

# ========== TOPO COM LOGO + TÍTULO ==========
encoded_logo = circular_image_base64("alquimistas.png", size=60)
if encoded_logo:
    logo_html = f'<img src="data:image/png;base64,{encoded_logo}" width="60" height="60" style="border-radius: 50%;">'
else:
    logo_html = '<div style="width: 60px; height: 60px; background-color: #FFD700; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; color: #0D1B2A;">🤖</div>'

st.markdown(f"""
<div class="header-container">
    {logo_html}
    <div class="header-title">Grupo Alquimistas Digitais</div>
</div>
<div class="subtitle">Análise Inteligente de Notas Fiscais</div>
""", unsafe_allow_html=True)

# ========== SIDEBAR COM STATUS ==========
with st.sidebar:
    st.header("🔧 Status do Sistema")
    
    # Verificar status da API
    health_status = check_api_health()
    
    if health_status is None:
        st.markdown('<div class="status-indicator status-error">❌ API não está respondendo</div>', unsafe_allow_html=True)
        st.error("Certifique-se de que o backend está rodando em http://localhost:5000")
        st.stop()
    elif health_status.get("agent_ready", False):
        st.markdown('<div class="status-indicator status-ok">✅ Sistema operacional</div>', unsafe_allow_html=True)
        st.success("Agente IA carregado e pronto!")
    else:
        st.markdown('<div class="status-indicator status-warning">⏳ Carregando agente...</div>', unsafe_allow_html=True)
        st.warning("Aguarde o agente terminar de carregar os dados.")
    
    # Botão para atualizar status
    if st.button("🔄 Atualizar Status"):
        st.rerun()

# ========== RESUMO DOS DADOS ==========
if health_status and health_status.get("agent_ready", False):
    with st.expander("📊 Resumo dos Dados", expanded=False):
        with st.spinner("Carregando resumo dos dados..."):
            summary = get_data_summary()
            
            if summary and "error" not in summary:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total de Notas", f"{summary['total_notas']:,}")
                    st.metric("Total de Itens", f"{summary['total_itens']:,}")
                
                with col2:
                    st.metric("Valor Total", f"R$ {summary['estatisticas_financeiras']['valor_total']:,.2f}")
                    st.metric("Valor Médio", f"R$ {summary['estatisticas_financeiras']['valor_medio']:,.2f}")
                
                with col3:
                    st.metric("Maior Nota", f"R$ {summary['estatisticas_financeiras']['maior_nota']:,.2f}")
                
                # Período
                st.write(f"**Período:** {summary['periodo']['inicio']} até {summary['periodo']['fim']}")
                
                # Principais fornecedores
                st.write("**Principais Fornecedores:**")
                for fornecedor, count in list(summary['principais_fornecedores'].items())[:5]:
                    st.write(f"• {fornecedor}: {count} notas")
                
            else:
                st.error("Erro ao carregar resumo dos dados")

# ========== DADOS CSV LOCAIS (para visualização) ==========
with st.expander("🔍 Visualizar Dados Locais", expanded=False):
    try:
        zip_path = "data/202401_NFs.zip"
        extract_dir = "data/"
        
        # Extrair se necessário
        if not os.path.exists(os.path.join(extract_dir, "202401_NFs_Cabecalho.csv")):
            if os.path.exists(zip_path):
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(extract_dir)
            else:
                st.warning("Arquivo ZIP não encontrado em data/202401_NFs.zip")
        
        # Carregar e mostrar dados
        if os.path.exists(os.path.join(extract_dir, "202401_NFs_Cabecalho.csv")):
            cab = pd.read_csv(os.path.join(extract_dir, "202401_NFs_Cabecalho.csv"))
            itens = pd.read_csv(os.path.join(extract_dir, "202401_NFs_Itens.csv"))
            df = pd.merge(itens, cab, on="CHAVE DE ACESSO", how="left")
            
            st.write(f"**Dados combinados:** {df.shape[0]} registros, {df.shape[1]} colunas")
            st.dataframe(df.head(10), use_container_width=True)
        else:
            st.info("Dados locais não disponíveis para visualização")
    except Exception as e:
        st.error(f"Erro ao carregar dados locais: {str(e)}")

# ========== INTERFACE DE CHAT ==========
st.header("💬 Chat com o Agente IA")

# Inicializar histórico de chat
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Mostrar histórico de chat
if st.session_state.chat_history:
    for message in st.session_state.chat_history:
        if message["type"] == "user":
            st.markdown(f"""
            <div class="user-message">
                <strong>Você:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="bot-message">
                <strong>🤖 Agente:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)

# Input para nova pergunta
if health_status and health_status.get("agent_ready", False):
    pergunta = st.text_input(
        "Digite sua pergunta sobre as notas fiscais:",
        placeholder="Ex: Qual o fornecedor com maior valor total de notas?",
        key="question_input"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        enviar = st.button("📤 Enviar", type="primary")
    with col2:
        limpar = st.button("🗑️ Limpar Chat")
    
    if limpar:
        st.session_state.chat_history = []
        st.rerun()
    
    if enviar and pergunta.strip():
        # Adicionar pergunta ao histórico
        st.session_state.chat_history.append({
            "type": "user", 
            "content": pergunta.strip()
        })
        
        # Mostrar indicador de carregamento
        with st.spinner("🤔 Processando sua pergunta..."):
            # Enviar para API
            response_data = send_query(pergunta.strip())
            
            if response_data and response_data.get("status") == "success":
                # Adicionar resposta ao histórico
                st.session_state.chat_history.append({
                    "type": "bot",
                    "content": response_data["response"]
                })
            else:
                # Adicionar erro ao histórico
                error_msg = response_data.get("error", "Erro desconhecido") if response_data else "Erro de comunicação com o servidor"
                st.session_state.chat_history.append({
                    "type": "bot",
                    "content": f"❌ Erro: {error_msg}"
                })
        
        # Limpar input e recarregar
        st.rerun()
        
else:
    st.info("⏳ Aguarde o agente terminar de carregar para fazer perguntas.")

# ========== EXEMPLOS DE PERGUNTAS ==========
if health_status and health_status.get("agent_ready", False):
    with st.expander("💡 Exemplos de Perguntas", expanded=False):
        st.write("**Perguntas sugeridas:**")
        
        exemplos = [
            "Qual o fornecedor com maior valor total de notas?",
            "Quantas notas foram emitidas por estado?",
            "Qual o produto mais vendido?",
            "Mostre as 10 maiores notas fiscais",
            "Qual a média de valor por item?",
            "Quantas notas foram emitidas por mês?",
            "Quais são os principais produtos por categoria?",
            "Análise de fornecedores por região"
        ]
        
        for exemplo in exemplos:
            if st.button(f"📝 {exemplo}", key=f"ex_{hash(exemplo)}"):
                st.session_state.question_input = exemplo

# ========== FOOTER ==========
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>🔬 <strong>Grupo Alquimistas Digitais</strong> - Transformando dados em insights</p>
    <p>Powered by LangChain, Gemini AI & Streamlit</p>
</div>
""", unsafe_allow_html=True)