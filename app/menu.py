import streamlit as st
from streamlit_option_menu import option_menu
import re
import aiohttp
import openpyxl
import time
import google.generativeai as genai
import json
import pandas as pd
import requests

st.set_page_config(page_title="TrendSpot", layout='wide')
genai.configure(api_key="")


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


with st.sidebar:
    selected = option_menu(
        "Menu",
        [
            "TrendSpot PDF",
            "TrendSpot Links",
            "Hot News"
        ],
        icons=[
            'link',
            'link',
            'link',
        ], menu_icon="list", default_index=0
    )


if selected == "TrendSpot PDF":

    files = []
    dataframes = []

    # SIDEBAR
    with st.sidebar:
        arquivo_pdf = st.file_uploader(
            "Faça o upload do arquivo", type="pdf", accept_multiple_files=True)

    # MAIN
    st.header('TrendSpot PDF IA')

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


elif selected == "TrendSpot Links":
    df = pd.DataFrame(columns=['Link', 'Thumb'])
    # MAIN
    st.header("TrendSpot Links IA")
    st.info("Insira os links que deseja extrair informações.")
    links = st.text_area("", height=300)
    button = st.button("Extrair", use_container_width=True)

    if button:
        if links:
            links = re.findall(r'(https?://[^\s]+)', links)
            for link in links:
                df.loc[len(df)] = [link, '']
                if 'tiktok.com' in link:
                    url = "https://tiktok-video-no-watermark10.p.rapidapi.com/index/Tiktok/getVideoInfo"

                    querystring = {"url": link}

                    headers = {
                        "x-rapidapi-key": "88b5804da0mshaec086ad3147560p16ac64jsn608ec3c7f56c",
                        "x-rapidapi-host": "tiktok-video-no-watermark10.p.rapidapi.com"
                    }

                    response = requests.get(
                        url, headers=headers, params=querystring)

                    thumb_url = response.json()["data"]["origin_cover"]

                    df.loc[df['Link'] == link, 'Thumb'] = thumb_url

                # elif 'instagram' in link:
                #     url = "https://instagram40.p.rapidapi.com/account-info"

                #     querystring = {"username": "instagram"}

                #     headers = {
                #         'x-rapidapi-key': "88b5804da0mshaec086ad3147560p16ac64jsn608ec3c7f56c",
                #         'x-rapidapi-host': "instagram40.p.rapidapi.com"
                #     }

                #     response = requests.request(
                #         "GET", url, headers=headers, params=querystring)

                #     thumb_url = response.json(
                #     )["graphql"]["user"]["profile_pic_url_hd"]

                #     df.loc[df['Link'] == link, 'Thumb'] = thumb_url

                else:
                    df.loc[df['Link'] == link, 'Thumb'] = 'Sem Link'

        else:
            st.info("Insira um link para continuar.")

        st.dataframe(df)


elif selected == "Hot News":
    dataframes = []
    df = pd.DataFrame(columns=['Titulo', 'Descrição'])
    st.header("Hot News IA")
    st.info("Insira o link que deseja analisar.")
    links = st.text_area("", height=300)
    button = st.button("Analisar", use_container_width=True)

    if button:
        if links:
            links = re.findall(r'(https?://[^\s]+)', links)
            for link in links:
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
                    system_instruction="""Vou enviar um link e quero que vc analise a noticia, e me retorne um  json com Titulo e uma descriçao da notica.
                    
                    Obs:
                    título: até 37 caracteres, incluindo espaços e pontuação
                    descrição: 242 caracteres, incluindo espaços e pontuação
                    
                    Output:
                    [  
                        {
                            "Titulo" :  "Noticia", 
                            "Descrição" : ""descriçao da noticia"  
                        }
                    ]
                    """,
                )

                chat_session = model.start_chat(
                    history=[
                        {
                            "role": "user",
                            "parts": [
                                link,
                            ],
                        },
                        {
                            "role": "model",
                            "parts": [
                                """
                                [  
                                    {
                                        "Titulo" :  "Noticia", 
                                        "Descrição" : ""descriçao da noticia"  
                                    }
                                ]
                                """,
                            ],
                        },
                    ]
                )

                response = chat_session.send_message("INSERT_INPUT_HERE")

                resposta = response.text

                temp_filename = f"output_.json"
                with open(temp_filename, 'w') as f:
                    f.write(resposta)

                 # Corrigir o arquivo JSON (remover a primeira e última linha)
                with open(temp_filename, 'r') as f:
                    linhas = f.readlines()

                linhas = linhas[1:len(linhas)-1]

                with open(temp_filename, 'w') as f:
                    f.writelines(linhas)

                with open(temp_filename, 'r') as f:
                    dados_json = json.load(f)

                df = pd.json_normalize(dados_json)
                dataframes.append(df)

    if dataframes:
        # Concatena
        final_df = pd.concat(dataframes, ignore_index=True)

        st.write(final_df)
