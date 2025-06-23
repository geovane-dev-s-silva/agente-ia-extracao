# Agente IA Extração

Projeto Python para responder perguntas baseadas em arquivos CSV, usando a API da OpenAI.

---

## 📋 Requisitos

- Python 3.8 ou superior
- Conta na OpenAI com uma API Key

---

## 🛠️ Instalação

```bash
1. Clone o repositório:

git clone agente-ia-extracao
cd agente-ia-extracao

2. Crie um ambiente virtual:

python -m venv venv

3. Ative o ambiente virtual:

Windows (PowerShell):
.\venv\Scripts\activate

Linux / Mac:
source venv/bin/activate

4. Instale as dependências:

bash
pip install -r requirements.txt

5. Editar o arquivo chamado .env na raiz do projeto com o seguinte conteúdo:

OPENAI_API_KEY="sua-chave-da-openai-aqui"

6. Rodar o script principal e Front:

bash
streamlit run agente.py
streamlit run front.py
```

O programa irá solicitar:
Uma pergunta a ser respondida com base nos dados do CSV.

✅ Exemplo de execução:

Digite sua pergunta: Quantos clientes são de São Paulo?

👤👤👤 Autor: Grupo de Estudos Alquimistas Digitais
👤 Integrador do codigo: Libio, Izaqui.
👤 README e Revisoes de: Silva, Geovane. (https://github.com/geovane-dev-s-silva/)