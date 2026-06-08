import os
import warnings
import requests
import pandas as pd
from tqdm.auto import tqdm
from bs4 import BeautifulSoup
from pyfinviz import Screener

warnings.filterwarnings("ignore")

root_dir = os.path.join(os.getcwd(), "data")
if not os.path.exists(root_dir): os.makedirs(root_dir)

custom_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def download_ishares():
    base_url = "https://www.blackrock.com/varnish-api/blk-one01-product-data/product-data/api/v1/get-fund-document?appType=PRODUCT_PAGE&appSubType=ISHARES&targetSite=us-ishares&locale=en_US"

    url_mapper = {
        "CNDX": "https://www.ishares.com/ch/professionals/en/products/253741/ishares-nasdaq-100-ucits-etf/1495092304805.ajax?fileType=csv&fileName=CSNDX_holdings&dataType=fund",
        "IVV": f"{base_url}&portfolioId=239726&userType=individual&component=holdings",
        "IWB": f"{base_url}&portfolioId=239707&userType=individual&component=holdings",
        "IWM": f"{base_url}&portfolioId=239710&userType=individual&component=holdings",
        "IWV": f"{base_url}&portfolioId=239714&userType=individual&component=holdings"
    }

    for product, url in tqdm(url_mapper.items(), total=len(url_mapper.keys()), desc="Downloading iShares"):
        try:
            response = requests.get(url=url, headers=custom_headers)
            if response.status_code != 200: raise ValueError("Invalid status code")

            dest_dir = os.path.join(root_dir, "ishares", product)
            if not os.path.exists(dest_dir): os.makedirs(dest_dir)

            with open(os.path.join(dest_dir, f"{product}_{pd.Timestamp.now().__str__().split(' ')[0]}.csv"), "wb") as f:
                f.write(response.content)

        except Exception as e:
            print(f"[{product}] Error: {e}")

def download_finviz():
    finviz_dir = os.path.join(root_dir, "finviz")
    if not os.path.exists(finviz_dir): os.makedirs(finviz_dir)

    url = "https://finviz.com/screener"

    response = requests.get(url=url, headers=custom_headers)
    if response.status_code != 200: raise ValueError(f"Invalid status code, {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")
    num_page = soup.find_all("a", {"class": "screener-pages"})[-2].text

    if not num_page.isnumeric(): raise ValueError(f"Invalid page number, {num_page}")

    pages = [i for i in range(1, int(num_page) + 1)]

    finviz_data = {
        "overview": [],
        "valuation": [],
        "financial": [],
        "performance": [],
        "technical": [],
    }

    finviz_view = {
        "overview": Screener.ViewOption.OVERVIEW,
        "valuation": Screener.ViewOption.VALUATION,
        "financial": Screener.ViewOption.FINANCIAL,
        "performance": Screener.ViewOption.PERFORMANCE,
        "technical": Screener.ViewOption.TECHNICAL,
    }

    for k, v in finviz_data.items():
        for i in tqdm(pages, total=len(pages), desc=f"[Finviz] Downloading {k.title()}"):
            try:
                s = Screener(pages=[i], view_option=finviz_view[k])

                finviz_data[k].append(s.data_frames[i])

            except Exception as e:
                print(f"[{k.title()}] Error: {e}, page {i}")

        df = pd.concat(finviz_data[k], ignore_index=True, axis=0)
        if not df.empty:
            if "No" in df.columns.tolist(): df = df.drop(columns=["No"], axis=1)

            dest_dir = os.path.join(finviz_dir, k.upper())
            if not os.path.exists(dest_dir): os.makedirs(dest_dir)

            df.to_csv(os.path.join(dest_dir, f"{k.title()}_{pd.Timestamp.now().__str__().split(' ')[0]}.csv"), index=False)


if __name__ == "__main__":
    download_ishares()

    download_finviz()
