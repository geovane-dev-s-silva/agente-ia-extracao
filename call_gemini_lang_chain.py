def call_gemini(pergunta: str) -> str:
  
    import os
    import base64
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.schema import HumanMessage
    from langchain_core.messages import HumanMessage
    from dotenv import load_dotenv
    load_dotenv()
    
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY não encontrada nas variáveis de ambiente")
    
    os.environ["GOOGLE_API_KEY"] = gemini_api_key
    
    # Inicializa o modelo Gemini
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-preview-04-17",
        temperature=0.3
    )
    
    # Caminhos dos arquivos CSV
    caminho_arquivo1 = "extracted_files/202401_NFs_Cabecalho.csv"
    caminho_arquivo2 = "extracted_files/202401_NFs_Itens.csv"
    
    # Lê e converte os arquivos para base64
    with open(caminho_arquivo1, "rb") as f1:
        dados_cabecalho = f1.read()
    
    with open(caminho_arquivo2, "rb") as f2:
        dados_itens = f2.read()
    
    # Converte para base64
    base64_cabecalho = base64.b64encode(dados_cabecalho).decode('utf-8')
    base64_itens = base64.b64encode(dados_itens).decode('utf-8')
    
    # Instrução do sistema
    system_prompt = """- Forneça uma resposta clara e direta
- Use os dados fornecidos acima
- Seja específico e inclua números quando possível
- Use emojis para tornar a resposta mais amigável
- Não inclua explicações técnicas ou código
- Responda em português brasileiro"""
    
    # Cria a mensagem com os arquivos anexados
    message_content = [
        {
            "type": "text",
            "text": f"Instruções: {system_prompt}\n\nArquivos CSV anexados: Cabeçalho das NFs e Itens das NFs\n\nPergunta: {pergunta}"
        },
        {
            "type": "media",
            "mime_type": "text/csv",
            "data": base64_cabecalho
        },
        {
            "type": "media", 
            "mime_type": "text/csv",
            "data": base64_itens
        }
    ]
    
    # Cria a mensagem
    message = HumanMessage(content=message_content)
    
    # Chama o modelo
    resposta = llm.invoke([message])
    
    return resposta.content

teste = call_gemini("Qual foi o valor total das notas fiscais?")
print(teste)