import time
import google.generativeai as genai

genai.configure(api_key="AIzaSyBt-qioyS3ds_1fS2cYQABQNgWOUggXVwg")


def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini.

    See https://ai.google.dev/gemini-api/docs/prompting_with_media
    """
    file = genai.upload_file(path, mime_type=mime_type)
    print(f"Uploaded file '{file.display_name}' as: {file.uri}")
    return file


def wait_for_files_active(files):
    """Waits for the given files to be active.

    Some files uploaded to the Gemini API need to be processed before they can be
    used as prompt inputs. The status can be seen by querying the file's "state"
    field.

    This implementation uses a simple blocking polling loop. Production code
    should probably employ a more sophisticated approach.
    """
    print("Waiting for file processing...")
    for name in (file.name for file in files):
        file = genai.get_file(name)
        while file.state.name == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(10)
            file = genai.get_file(name)
        if file.state.name != "ACTIVE":
            raise Exception(f"File {file.name} failed to process")
    print("...all files ready")
    print()


def resposta():
    # Create the model
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
        system_instruction="Analise o PDF e retorne uma tabela com as seguintes colunas: 'data', 'titulo', 'descriçao', 'rede social', e 'assunto' de cada noticia.",
    )

    # TODO Make these files available on the local file system
    # You may need to update the file paths
    files = [
        upload_to_gemini("arquivo.pdf", mime_type="application/pdf"),
    ]

    # Some files have a processing delay. Wait for them to be ready.
    wait_for_files_active(files)

    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    files[0],
                ],
            },
            {
                "role": "model",
                "parts": [
                    "```\n| data       | titulo                         | descriçao                                                                                                                                                                                                              | rede social | assunto              |\n|------------|---------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------|----------------------|\n| 10/01/2025 | Debí tirar más fotos            | Lançado no dia 5, o novo álbum de Bad Bunny tem viralizado com a música \"Debí Tirar Más Fotos\", impulsionando uma trend que desta o carinho dos usuários por alguém. O cantor reagiu às criações e o álbum tem gerado comentários. Mais de 37 mil vídeos foram compartilhados no último dia. | TikTok      | Trend                |\n| 10/01/2025 | Nonchalant Challenge            | A trend envolve demonstrar uma atitude descontraída em situações cotidianas. Embora a maioria dos vídeos sejam gringos, a ideia está sendo adaptada para cenários como escadas e academias, gerando muitos conteúdos criativos. | TikTok      | Trend                |\n| 10/01/2025 | Bebês seguram tudo              | Nessa trend, pessoas dão para bebês e crianças muito mais coisas do que eles conseguem segurar. As conversas e conteúdos deste tipo crescem cada vez mais.                                                             | TikTok      | Trend - Maternidade |\n| 10/01/2025 | Uma vez me falaram que...      | Em formato carrossel, usuários compartilham coisas que ouviram outras pessoas falarem, mas que não se identificaram com a situação, seja por gostar ou não gostar. O áudio usado teve 6,7 mil usos em apenas 1 dia.       | TikTok      | Trend                |\n| 10/01/2025 | Meme Gabizinha                   | A foto de uma criança, conhecida como Gabizinha, tem sido usada de forma engraçada para representar a mudança de personalidade dos usuários em diferentes situações.                                                      | TikTok      | Meme                 |\n| 10/01/2025 | Fazendo meu próprio meme        | Creators e influencers, estão criando posts em formato de meme, usando suas próprias fotos e associando-as a situações que geram identificação. Esse tipo de conteúdo tem ganhado força nas últimas semanas.              | Instagram   | Creator & Influencer  |\n| 10/01/2025 | Marrom Bombom                    | Desde a semana do Natal, a trend com a música de \"Os Morenos\" segue em alta. Além de valorizar o tom de pele, os usuários aproveitam o momento para exibir o bronzeado, especialmente com o aumento das viagens.         | TikTok      | Trend                |\n| 10/01/2025 | Que nunca nos falte o supérfluo | Os usuários compartilham seus itens de desejo utilizando essa abordagem, que tem potencial para ser adaptada a diversos segmentos.                                                                                       | TikTok      | Trend                |\n| 10/01/2025 | Ninja, pirata ou cowboy?        | Pessoas perguntam para seus parceiros ou outros homens se eles prefeririam ser um ninja, um pirata ou um cowboy e sempre se surpreendem com a resposta. A trend não é nova, mas está gerando uma nova onda de conteúdos recentemente.     | TikTok      | Assunto             |\n| 10/01/2025 | É claro que vou resolver, mas... | Usuários contam que são super capazes de resolver seus problemas, eles só precisam fazer algo antes, como chorar ou reclamar.                                                                                               | TikTok      | Trend                |\n```",
                ],
            },
        ]
    )

    response = chat_session.send_message("INPUT")
    print(response.text)
    return response.text
