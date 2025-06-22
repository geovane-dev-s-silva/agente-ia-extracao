"""
 Nome do arquivo: agente.py
 Autor: Alquimistas Digitais
 Data: 10/06/2025
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import zipfile
import pandas as pd
from typing import List, Dict, Any
import google.generativeai as genai
import logging
import threading
import time
import base64
from dotenv import load_dotenv
load_dotenv()
from call_gemini_lang_chain import call_gemini
# Suprimir warnings
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

"""
 Alquimistas Digitais - Análise Inteligente de Notas Fiscais

 A escolha do Gemini como base para o agente, foi devido a generosa quota de tokens 
 oferecidas pela Google, permitindo a construção de projetos simples e protótipos como esse.

"""
class SimpleGemini:
   
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash-preview-04-17"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
    
    def generate(self, prompt: str) -> str:
        """Gera resposta diretamente"""
        try:
            response = self.model.generate_content(prompt)
            return response.text if response.text else "Resposta vazia do modelo"
        except Exception as e:
            logger.error(f"Erro ao chamar Gemini: {e}")
            return f"Erro: {str(e)}"

class NFAnalysisAgent:

    """Agente simplificado de IA para análise de Notas Fiscais"""
    
    def __init__(self, gemini_api_key: str):
        self.gemini_api_key = gemini_api_key
        self.gemini = SimpleGemini(api_key=gemini_api_key)
        self.df_cabecalho = None
        self.df_itens = None
        self.df_combined = None
        self.is_ready = False

    
    def extract_zip_files(self, zip_path: str, extract_to: str = "./data/"):
        """Extrai arquivos CSV do ZIP"""
        try:
            os.makedirs(extract_to, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
                extracted_files = zip_ref.namelist()
            
            logger.info(f"Arquivos extraídos: {extracted_files}")
            
            cabecalho_file = None
            itens_file = None
            
            for file in extracted_files:
                if "Cabecalho" in file or "cabecalho" in file:
                    cabecalho_file = os.path.join(extract_to, file)
                elif "Itens" in file or "itens" in file:
                    itens_file = os.path.join(extract_to, file)
            
            return cabecalho_file, itens_file
            
        except Exception as e:
            logger.error(f"Erro ao extrair ZIP: {e}")
            return None, None
    
    def load_csv_files(self, cabecalho_path: str, itens_path: str):
        
        try:
            self.df_cabecalho = pd.read_csv(cabecalho_path, encoding='utf-8')
            self.df_itens = pd.read_csv(itens_path, encoding='utf-8')
            
            # Limpar nomes das colunas
            self.df_cabecalho.columns = self.df_cabecalho.columns.str.strip()
            self.df_itens.columns = self.df_itens.columns.str.strip()
            
            logger.info(f"Cabeçalho carregado: {self.df_cabecalho.shape[0]} registros")
            logger.info(f"Itens carregados: {self.df_itens.shape[0]} registros")
            
            # Criar DataFrame combinado
            self.df_combined = pd.merge(
                self.df_cabecalho, 
                self.df_itens, 
                on='CHAVE DE ACESSO', 
                how='inner',
                suffixes=('_cab', '_item')
            )
            
            self.is_ready = True
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar CSVs: {e}")
            return False
    
    def get_data_summary(self) -> str:

        """Gera resumo dos dados para o contexto da LLM"""

        if not self.is_ready:
            return ""
        
        try:
            # Informações básicas
            total_notas = self.df_cabecalho.shape[0]
            total_itens = self.df_itens.shape[0]
            
            # Estatísticas financeiras
            valor_total = self.df_cabecalho['VALOR NOTA FISCAL'].sum()
            valor_medio = self.df_cabecalho['VALOR NOTA FISCAL'].mean()
            
            # Top fornecedores por montante
            top_fornecedores = self.df_cabecalho.groupby('RAZÃO SOCIAL EMITENTE')['VALOR NOTA FISCAL'].sum().sort_values(ascending=False).head(10)
            
            # Top produtos por quantidade
            top_produtos = self.df_itens.groupby('DESCRIÇÃO DO PRODUTO/SERVIÇO')['QUANTIDADE'].sum().sort_values(ascending=False).head(10)
            
            # Top estados
            top_estados = self.df_cabecalho['UF EMITENTE'].value_counts().head(5)
            
            summary = f"""
            DADOS DAS NOTAS FISCAIS:
            - Total de notas fiscais: {total_notas:,}
            - Total de itens: {total_itens:,}
            - Valor total das notas: R$ {valor_total:,.2f}
            - Valor médio por nota: R$ {valor_medio:,.2f}
            
            TOP 10 FORNECEDORES POR MONTANTE:
            {chr(10).join([f"- {fornecedor}: R$ {valor:,.2f}" for fornecedor, valor in top_fornecedores.items()])}
            
            TOP 10 PRODUTOS POR QUANTIDADE:
            {chr(10).join([f"- {produto}: {qtd:,.0f} unidades" for produto, qtd in top_produtos.items()])}
            
            TOP 5 ESTADOS EMITENTES:
            {chr(10).join([f"- {estado}: {count:,} notas" for estado, count in top_estados.items()])}
            """
            
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo: {e}")
            return ""
    
    def get_summary(self) -> dict:
        """Retorna resumo dos dados em formato JSON"""
        if not self.is_ready or self.df_cabecalho is None:
            return {"error": "Dados não carregados"}
        
        try:
            # Estatísticas financeiras
            valor_total = float(self.df_cabecalho['VALOR NOTA FISCAL'].sum())
            valor_medio = float(self.df_cabecalho['VALOR NOTA FISCAL'].mean())
            maior_nota = float(self.df_cabecalho['VALOR NOTA FISCAL'].max())
            
            # Período
            data_min = self.df_cabecalho['DATA EMISSÃO'].min()
            data_max = self.df_cabecalho['DATA EMISSÃO'].max()
            
            # Principais fornecedores
            principais_fornecedores = self.df_cabecalho['RAZÃO SOCIAL EMITENTE'].value_counts().head(5).to_dict()
            
            return {
                "total_notas": int(self.df_cabecalho.shape[0]),
                "total_itens": int(self.df_itens.shape[0]),
                "estatisticas_financeiras": {
                    "valor_total": valor_total,
                    "valor_medio": valor_medio,
                    "maior_nota": maior_nota
                },
                "periodo": {
                    "inicio": str(data_min),
                    "fim": str(data_max)
                },
                "principais_fornecedores": principais_fornecedores
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo: {e}")
            return {"error": str(e)}
    
    def execute_pandas_analysis(self, question: str) -> str:
        """Executa análise direta com pandas baseada na pergunta"""
        try:
            question_lower = question.lower()
            
            if "maior montante" in question_lower or ("fornecedor" in question_lower and "maior" in question_lower):
                fornecedor_montante = self.df_cabecalho.groupby('RAZÃO SOCIAL EMITENTE')['VALOR NOTA FISCAL'].sum().sort_values(ascending=False)
                maior_fornecedor = fornecedor_montante.index[0]
                maior_valor = fornecedor_montante.iloc[0]
                return f"🏆 O fornecedor com maior montante é: **{maior_fornecedor}** com R$ {maior_valor:,.2f}"
            
            elif "produto" in question_lower and "mais vendido" in question_lower:
                produto_vendido = self.df_itens.groupby('DESCRIÇÃO DO PRODUTO/SERVIÇO')['QUANTIDADE'].sum().sort_values(ascending=False)
                produto_top = produto_vendido.index[0]
                quantidade = produto_vendido.iloc[0]
                return f"📦 O produto mais vendido é: **{produto_top}** com {quantidade:.0f} unidades"
            
            elif "estado" in question_lower or "uf" in question_lower:
                estados_emitente = self.df_cabecalho['UF EMITENTE'].value_counts().head(5)
                result = "📍 Estados com mais emissões:\n"
                for estado, count in estados_emitente.items():
                    result += f"• {estado}: {count} notas\n"
                return result.strip()
            
            elif "maiores notas" in question_lower or "maiores valores" in question_lower:
                maiores_notas = self.df_cabecalho.nlargest(10, 'VALOR NOTA FISCAL')[['RAZÃO SOCIAL EMITENTE', 'VALOR NOTA FISCAL']]
                result = "💰 As 10 maiores notas fiscais:\n"
                for idx, row in maiores_notas.iterrows():
                    result += f"• {row['RAZÃO SOCIAL EMITENTE']}: R$ {row['VALOR NOTA FISCAL']:,.2f}\n"
                return result.strip()
            
            else:
                return None  # Deixa para a LLM processar
                
        except Exception as e:
            logger.error(f"Erro na análise pandas: {e}")
            return None
    
    def query(self, question: str) -> str:

        """
        Processa uma pergunta usando abordagem híbrida, pois perguntas
        mais simples podem ser resolvidas diretamente com pandas economizando tokens
        de modelos, que mesmo gratuítos são limitados.
        """

        if not self.is_ready:
            return "Agente não está pronto ainda. Aguarde o carregamento dos dados."
        
        try:
            # Primeiro tenta análise direta com pandas
            pandas_result = self.execute_pandas_analysis(question)
            if pandas_result:
                return pandas_result
            
            # Se não conseguiu com pandas, usa a API do Gemini
            resposta = call_gemini(question)
            
            return f"{resposta.strip()}"
            
        except Exception as e:
            logger.error(f"Erro ao processar query: {e}")
            return f"❌ Erro ao processar pergunta: {str(e)}"

# Instância global do agente
nf_agent = None
agent_loading = False

def initialize_agent():
    """Inicializa o agente em background"""
    global nf_agent, agent_loading
    
    if agent_loading:
        return
    
    agent_loading = True
    logger.info("Iniciando carregamento do agente...")
    
    try:
        # Verificar API key
        api_key = os.getenv("GOOGLE_API_KEY") 
        if not api_key:
            logger.error("GOOGLE_API_KEY não configurada!")
            return
        
        # Verificar arquivo ZIP
        zip_paths = ["202401_NFs.zip", "data/202401_NFs.zip", "./202401_NFs.zip"]
        zip_path = None
        
        for path in zip_paths:
            if os.path.exists(path):
                zip_path = path
                break
        
        if not zip_path:
            logger.error("Arquivo ZIP das NFs não encontrado!")
            return
        
        # Inicializar agente
        nf_agent = NFAnalysisAgent(api_key)
        
        # Extrair e carregar dados
        cabecalho_path, itens_path = nf_agent.extract_zip_files(zip_path)
        if not cabecalho_path or not itens_path:
            logger.error("Erro ao extrair arquivos do ZIP")
            return
        
        if not nf_agent.load_csv_files(cabecalho_path, itens_path):
            logger.error("Erro ao carregar arquivos CSV")
            return
        
        logger.info("Agente carregado com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro ao inicializar agente: {e}")
    finally:
        agent_loading = False

# Inicializar agente ao startar o servidor
threading.Thread(target=initialize_agent, daemon=True).start()

# ========== ROTAS DA API ==========

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verifica status da API e do agente"""
    return jsonify({
        "status": "ok",
        "agent_ready": nf_agent is not None and nf_agent.is_ready,
        "agent_loading": agent_loading,
        "timestamp": time.time()
    })

@app.route('/api/summary', methods=['GET'])
def get_summary():
    """Retorna resumo dos dados"""
    if not nf_agent or not nf_agent.is_ready:
        return jsonify({"error": "Agente não está pronto"}), 503
    
    summary = nf_agent.get_summary()
    if "error" in summary:
        return jsonify(summary), 500
    
    return jsonify(summary)

@app.route('/api/query', methods=['POST'])
def process_query():
    """Processa pergunta do usuário"""
    if not nf_agent or not nf_agent.is_ready:
        return jsonify({
            "status": "error",
            "error": "Agente não está pronto. Aguarde o carregamento dos dados."
        }), 503
    
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({
            "status": "error",
            "error": "Pergunta não fornecida"
        }), 400
    
    question = data['question'].strip()
    if not question:
        return jsonify({
            "status": "error",
            "error": "Pergunta vazia"
        }), 400
    
    try:
        logger.info(f"Processando pergunta: {question}")
        response = nf_agent.query(question)
        
        return jsonify({
            "status": "success",
            "response": response,
            "question": question
        })
        
    except Exception as e:
        logger.error(f"Erro ao processar pergunta: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/reload', methods=['POST'])
def reload_agent():
    """Recarrega o agente"""
    threading.Thread(target=initialize_agent, daemon=True).start()
    return jsonify({"status": "reloading"})

if __name__ == '__main__':
    print("🚀 Iniciando servidor backend...")
    print("📡 API disponível em: http://localhost:5000")
    print("🔧 Health check: http://localhost:5000/api/health")
    print("📊 Resumo: http://localhost:5000/api/summary")
    print("💬 Query: POST http://localhost:5000/api/query")
    
    #app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)
    # O uso de `use_reloader=False` evita que o servidor reinicie duas vezes no modo debug