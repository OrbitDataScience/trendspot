import streamlit as st
import pandas as pd
import re
import aiohttp
import openpyxl
import time
import google.generativeai as genai
import json

genai.configure(api_key="AIzaSyBt-qioyS3ds_1fS2cYQABQNgWOUggXVwg")


def upload_to_gemini(path, mime_type=None):
    file = genai.upload_file(path, mime_type=mime_type)
    print(f"Uploaded file '{file.display_name}' as: {file.uri}")
    return file


def wait_for_files_active(files):
    for name in (file.name for file in files):
        file = genai.get_file(name)
        while file.state.name == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(10)
            file = genai.get_file(name)
        if file.state.name != "ACTIVE":
            raise Exception(f"File {file.name} failed to process")


def main():
    st.set_page_config(page_title="TrendSpot PDF", layout='wide')
    files = []
    dataframes = []

    # SIDEBAR
    with st.sidebar:
        st.header('TrendSpot PDF IA')
        arquivo_pdf = st.file_uploader(
            "Faça o upload do arquivo", type="pdf", accept_multiple_files=True)

    # MAIN
    if arquivo_pdf:
        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config=generation_config,
            system_instruction="""Analise o PDF e retorne em formato JSON com as seguintes dados: 'data', "tema", 'titulo' e 'descriçao' de cada noticia.

            Observações:
            - O PDF contém notícias sobre tendências em redes sociais.
            - A coluna tema pode receber um dos 3 temas definidos: Geral, Alimentação, Beleza. Analise o conteúdo do PDF para definir o tema de cada notícia.
            - Ao final do PDF, há uma seção 'Para aproveitar agora' com 4 tópicos. Analise eles tambem, com 'data', "tema", 'titulo' e 'descriçao'
            Output example:
            [            
                {
                    "data": "10/01/2025",
                    "tema" : "Geral",
                    "titulo": "Debí tirar más fotos",
                    "descriçao": "Lançado no dia 5, o novo álbum de Bad Bunny tem viralizado com a música \"Debí Tirar Más Fotos\", impulsionando uma trend que desta o carinho dos usuários por alguém. O cantor reagiu às criações e o álbum tem gerado comentários. Mais de 37 mil vídeos foram compartilhados no último dia.",
                },
            ]
            """,
        )

        for uploaded_file in arquivo_pdf:
            with open(uploaded_file.name, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Upload to Gemini
            file = upload_to_gemini(
                uploaded_file.name, mime_type="application/pdf")
            files.append(file)

        wait_for_files_active(files)

        # Iterar sobre os arquivos processados
        for file in files:
            chat_session = model.start_chat(
                history=[
                    {
                        "role": "user",
                        "parts": [
                            file,
                        ],
                    },
                    {
                        "role": "model",
                        "parts": [
                            """
                            [           
                                {
                                    "data": "10/01/2025",
                                    "tema" : "Geral",
                                    "titulo": "Debí tirar más fotos",
                                    "descriçao": "Lançado no dia 5, o novo álbum de Bad Bunny tem viralizado com a música \"Debí Tirar Más Fotos\", impulsionando uma trend que desta o carinho dos usuários por alguém. O cantor reagiu às criações e o álbum tem gerado comentários. Mais de 37 mil vídeos foram compartilhados no último dia.",
                                },
                            ]
                            """,
                        ],
                    },
                ]
            )

            response = chat_session.send_message("INSERT_INPUT_HERE")
            resposta = response.text

            # Salvar resposta em arquivo JSON temporário
            temp_filename = f"output_{file.display_name}.json"
            with open(temp_filename, 'w') as f:
                f.write(resposta)

            # Corrigir o arquivo JSON (remover a primeira e última linha)
            with open(temp_filename, 'r') as f:
                linhas = f.readlines()

            linhas = linhas[1:len(linhas)-1]

            with open(temp_filename, 'w') as f:
                f.writelines(linhas)

            # Carregar o JSON corrigido
            with open(temp_filename, 'r') as f:
                dados_json = json.load(f)

            # Converter para DataFrame
            df = pd.json_normalize(dados_json)
            # Adicionar o DataFrame à lista de DataFrames
            dataframes.append(df)

    if not dataframes:
        st.info("Faça o upload de um arquivo PDF para começar.")
    else:
        # Concatena
        final_df = pd.concat(dataframes, ignore_index=True)

        st.write(final_df)


if __name__ == '__main__':
    main()
