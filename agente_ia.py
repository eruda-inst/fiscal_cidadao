# agente_ia.py

import os
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
from io import StringIO

class AgenteDeDados:

    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Chave GOOGLE_API_KEY não encontrada no arquivo .env")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro-latest')

    def _criar_prompt(self, pergunta: str, df: pd.DataFrame) -> str:
        buffer = StringIO()
        df.info(buf=buffer)
        df_info = buffer.getvalue()

        prompt = f"""
        Você é um assistente de dados especialista em analisar gastos públicos de Jacobina, BA.
        Seu objetivo é responder perguntas com base em um DataFrame do Pandas chamado 'df'.

        INSTRUÇÕES:
        1.  Analise a pergunta do usuário.
        2.  **Passo 1: GERE O CÓDIGO.** Escreva o código Python/Pandas para encontrar a resposta. Use APENAS a variável 'df' e a biblioteca pandas. O código deve ser capaz de ser executado diretamente.
        3.  **Passo 2: GERE A RESPOSTA.** Com base no resultado que o código produziria, escreva uma resposta clara e objetiva em português para o usuário. Formate valores monetários de forma legível (ex: R$ 1.234,56).
        4.  Se a pergunta não puder ser respondida com os dados, informe o motivo de forma clara.

        **Informações sobre o DataFrame (df.info()):**
        {df_info}

        **Primeiras 5 linhas do DataFrame (df.head()):**
        {df.head().to_markdown()}

        **Pergunta do Usuário:**
        {pergunta}

        ---
        **CÓDIGO PYTHON GERADO:**
        ```python
        # Escreva seu código aqui
        ```

        **RESPOSTA PARA O USUÁRIO:**
        """
        return prompt

    def perguntar(self, pergunta: str, df: pd.DataFrame) -> str:

        prompt = self._criar_prompt(pergunta, df)
        
        try:
            resposta_ia = self.model.generate_content(prompt)
            
            if "RESPOSTA PARA O USUÁRIO:" in resposta_ia.text:
                return resposta_ia.text.split("RESPOSTA PARA O USUÁRIO:")[-1].strip()
            else:
                return resposta_ia.text.strip()

        except Exception as e:
            print(f"Erro na comunicação com a IA: {e}")
            return f"Ocorreu um erro ao processar sua pergunta: {e}"