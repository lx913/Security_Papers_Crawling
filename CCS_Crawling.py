import requests
from bs4 import BeautifulSoup
import os
import PyPDF2
from io import BytesIO
import re
import time
import argparse

conference_support = ["ccs"]
url = {'dblp':'https://dblp.org/db/conf/',}

def Crawling(conference = None, year = None, save_folder = 'paper/', keywords= None):
    if conference == None:
        print('Please choose conference!')
        return
    if conference not in conference_support:
        print('Conference not support!')
        return
    if year == None:
        print('Please choose year!')
        return
    if not os.path.exists(save_folder):
        os.mkdir(save_folder)

    dblp = url["dblp"]
    c_url = dblp + conference + '/' + conference+year +'.html'
    # https://dblp.org/db/conf/ccs/ccs2022.html

    #crawling html elements
    response = requests.get(c_url, verify=False)
    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    # all href
    papers = soup.find_all("a",href=lambda x: x and re.search(r"doi\.org/10\.1145/\d{7}\.\d{7}", x))

    # all doi, including keynote
    pdf_links = []
    pattern = r"doi\.org/(.+)"

    for paper in papers:
        pdf_link = paper.get("href")
        match_res = 'https://dl.acm.org/doi/pdf/' + re.search(pattern, pdf_link).group(1)
        if match_res not in pdf_links:
            pdf_links.append(match_res)

    if keywords == None:
        print("No Keywords, Download All Papers")

    for pdf_link in pdf_links:
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
    parser.add_argument('-C', '--conference', default='ccs', help="conference for crawling")
    parser.add_argument('-Y', '--year', default='2022', help="year for crawling")
    parser.add_argument('-F', '--save_folder', default="paper/", help="where paper saved")
    parser.add_argument('-K', '--keywords', default=None, nargs='+', help="Key words you want")

    args = parser.parse_args()

    Crawling(args.conference,args.year,args.save_folder,args.keywords)
