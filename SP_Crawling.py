import requests
from bs4 import BeautifulSoup
import os
import PyPDF2
from io import BytesIO
import re
import time
import argparse

conference_support = ["sp"]
url = {'dblp':'https://dblp.org/db/conf/',}
headers = {
            'Accept': 'application/json,text/plain,*/*',
            'Accept-Encoding': 'gzip,deflate,br',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Content-Length': '122',
            'Content-Type': 'application/json',
            'Referer': 'https://ieeexplore.ieee.org/search/searchresult.jsp?newsearch=true&queryText=mechanical',
            'User-Agent': 'Mozilla/5.0 '}

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
    papers = soup.find_all("a",href=lambda x: x and re.compile(r'doi\.org/10\.1109/.*(\d{7})').search(x))

    # all doi, including keynote
    pdf_links = []
    pattern = r'doi\.org/10\.1109/.*(\d{7})'

    for paper in papers:
        pdf_link = paper.get("href")
        match_res = 'https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=' + re.search(pattern, pdf_link).group(1)
        if match_res not in pdf_links:
            pdf_links.append(match_res)

    if keywords == None:
        print("No Keywords, Download All Papers")

    for pdf_link in pdf_links:
        print('Latent Link: ',pdf_link)
        pdf_response = requests.get(pdf_link)
        pdf_newurl = pdf_response.content
        pdf_loc = BeautifulSoup(pdf_newurl, "html.parser")
        pdf_url = pdf_loc.find_all(src=True)
        pdf_true_link = pdf_url[-1]['src']
        print('True Link: ', pdf_true_link)
        pdf_data = requests.get(pdf_true_link).content
        stream = BytesIO(pdf_data)
        pdf_reader = PyPDF2.PdfReader(stream)
        if len(pdf_reader.pages) <= 6:
            continue
        text = ""
        for i in range(3):
            page = pdf_reader.pages[i]
            text += page.extract_text()
        title = text.split("\n")[0]
        title = re.sub('[\/:*?"<>|]', '_', title)
        if keywords == None:
            match = True
        else:
            if isinstance(keywords, list):
                for keyword in keywords:
                    match = re.search(keyword, text, flags=re.IGNORECASE)
                    if match:
                        print('Paper:', title, ". contains " + keyword)
                        break
            else:
                match = re.search(keywords, text, flags=re.IGNORECASE)
                if match:
                    print('Paper:', title, ". contains " + keywords)
        if match:
            filename = title + ".pdf"
            save_folder = conference+year
            if not os.path.exists(save_folder):
                os.makedirs(save_folder)
            save_path = save_folder + "/" + filename
            with open(save_path, "wb") as f:
                f.write(pdf_data)
        time.sleep(10)



# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-C', '--conference', default='sp', help="conference for crawling")
    parser.add_argument('-Y', '--year', default='2022', help="year for crawling")
    parser.add_argument('-F', '--save_folder', default="paper/", help="where paper saved")
    parser.add_argument('-K', '--keywords', default=None, nargs='+', help="Key words you want")

    args = parser.parse_args()

    Crawling(args.conference,args.year,args.save_folder,args.keywords)
