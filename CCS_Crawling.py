import requests
from bs4 import BeautifulSoup
import os
import PyPDF2
from io import BytesIO
import re
import time
import argparse

url = {'CCS22':'https://www.sigsac.org//ccs//CCS2022//proceedings//ccs-proceedings.html',}

def Crawling(conference = None, save_folder = 'paper/', keywords= None):
    if conference == None:
        print('Please choose conference!')
        return
    if conference not in url:
        print('Conference not support!')
        return

    if not os.path.exists(save_folder):
        os.mkdir(save_folder)

    c_url = url[conference]

    #crawling html elements
    response = requests.get(c_url, verify=False)
    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    # CCS22 paper tag
    papers = soup.find_all("a", class_="DLtitleLink")

    if keywords == None:
        print("No Keywords, Download All Papers")

    for paper in papers:
        pdf_link = paper.get("href")
        pdf_link = pdf_link.replace("doi/", "doi/pdf/")
        print(pdf_link)
        pdf_response = requests.get(pdf_link)
        pdf_data = pdf_response.content
        stream = BytesIO(pdf_data)
        pdf_reader = PyPDF2.PdfReader(stream)
        if len(pdf_reader.pages) <= 6:
            continue
        text = ""
        for i in range(3):
            page = pdf_reader.pages[i]
            text += page.extract_text()
        if keywords == None:
            match = True
        else:
            if isinstance(keywords, list):
                for keyword in keywords:
                    match = re.search(keyword, text, flags=re.IGNORECASE)
                    if match:
                        print(pdf_link, " contains keywords:" + keyword)
                        break
            else:
                match = re.search(keywords, text, flags=re.IGNORECASE)
                if match:
                    print(pdf_link, " contains keywords:" + keywords)
        if match:
            parts = pdf_link.split("/")
            filename = parts[-1]
            filename += ".pdf"
            save_folder = "paper"
            save_path = save_folder + "/" + filename
            with open(save_path, "wb") as f:
                f.write(pdf_data)
        time.sleep(10)



# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-C', '--conference', default='CCS22', help="conference for crawling")
    parser.add_argument('-F', '--save_folder', default="paper/", help="where paper saved")
    parser.add_argument('-K', '--keywords', default=None, nargs='+', help="Key words you want")

    args = parser.parse_args()

    print(args.keywords)
    Crawling(args.conference,args.save_folder,args.keywords)
