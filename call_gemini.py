# pip install google-genai

import base64
import os
from google import genai
from google.genai import types

def call_gemini(pergunta: str) -> str:
    """ 
    Método para carregar carregar os arquivos no modelo Gemini, e 
    realizar a pergunta baseada em ambos os arquvos.
    """
    # Inicializa o cliente Gemini
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    # Caminhos dos arquivos CSV
    caminho_arquivo1 = "extracted_files/202401_NFs_Cabecalho.csv"
    caminho_arquivo2 = "extracted_files/202401_NFs_Itens.csv"

    # Lê e converte os arquivos para base64
    with open(caminho_arquivo1, "rb") as f1:
        base64_cabecalho = base64.b64encode(f1.read())

    with open(caminho_arquivo2, "rb") as f2:
        base64_itens = base64.b64encode(f2.read())

    # Define os conteúdos da conversa
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(
                    mime_type="text/csv",
                    data=base64.b64decode(base64_cabecalho),
                ),
                types.Part.from_bytes(
                    mime_type="text/csv",
                    data=base64.b64decode(base64_itens),
                ),
                types.Part.from_text(text=pergunta),
            ],
        ),
    ]

    prompt = """   - Forneça uma resposta clara e direta
                    - Use os dados fornecidos acima
                    - Seja específico e inclua números quando possível
                    - Use emojis para tornar a resposta mais amigável
                    - Não inclua explicações técnicas ou código
                    - Responda em português brasileiro"""
    
    # Configurações de geração
    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0),
        response_mime_type="text/plain",
        system_instruction=[
            types.Part.from_text(text=prompt),
        ],
    )

    # Faz a chamada e coleta a resposta
    resposta = ""
    for chunk in client.models.generate_content_stream(
        model="gemini-2.5-flash-preview-04-17",
        contents=contents,
        config=generate_content_config,
    ):
        resposta += chunk.text

    return resposta


