import streamlit as st
import pandas as pd
import re
import aiohttp
import openpyxl
import time
import json
import requests

df = pd.DataFrame(columns=['Link', 'Thumb'])


def main():
    st.set_page_config(page_title="TrendSpot Links", layout='wide')

    # MAIN
    st.title("TrendSpot Links IA")
    st.info("Insira os links que deseja extrair informações.")
    links = st.text_area("", height=300)
    button = st.button("Extrair", use_container_width=True)

    if button:
        if links:
            links = re.findall(r'(https?://[^\s]+)', links)
            for link in links:
                df.loc[len(df)] = [link, '']
                if 'tiktok' in link:
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

                elif 'instagram' in link:
                    url = "https://instagram40.p.rapidapi.com/account-info"

                    querystring = {"username": "instagram"}

                    headers = {
                        'x-rapidapi-key': "88b5804da0mshaec086ad3147560p16ac64jsn608ec3c7f56c",
                        'x-rapidapi-host': "instagram40.p.rapidapi.com"
                    }

                    response = requests.request(
                        "GET", url, headers=headers, params=querystring)

                    thumb_url = response.json(
                    )["graphql"]["user"]["profile_pic_url_hd"]

                    df.loc[df['Link'] == link, 'Thumb'] = thumb_url

                else:
                    df.loc[df['Link'] == link, 'Thumb'] = 'Sem Link'

        else:
            st.info("Insira um link para continuar.")

        st.dataframe(df)


if __name__ == '__main__':
    main()
