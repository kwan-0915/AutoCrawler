import os
import json
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

def download_iShares():
    base_url = "https://www.ishares.com/varnish-api/blk-one01-product-data/product-data/api/v2/get-product-data?appSubType=ISHARES&appType=PRODUCT_PAGE&component=holdings.all&targetSite=us-ishares&userType=individual&excludeContent=true&includeConfig=true"

    url_mapper = {
        "CNDX": f"{base_url}&locale=en_GB&portfolioId=253741&asOfDate={asOfDate}",
        "IVV": f"{base_url}&locale=en_US&portfolioId=239726&asOfDate={asOfDate}",
        "IWB": f"{base_url}&locale=en_US&portfolioId=239707&asOfDate={asOfDate}",  # russel 1000
        "IWM": f"{base_url}&locale=en_US&portfolioId=239710&asOfDate={asOfDate}",  # russel 2000
        "IWV": f"{base_url}&locale=en_US&portfolioId=239714&asOfDate={asOfDate}",  # russel 3000
    }

    pbar = tqdm(url_mapper.items(), total=len(url_mapper.keys()))
    for product, url in pbar:
        pbar.set_description(f"[iShares] Downloading {product}")

        dest_dir = os.path.join(root_dir, "ishares", product)
        if not os.path.exists(dest_dir): os.makedirs(dest_dir)

        try:
            response = requests.get(url=url, headers=custom_headers)
            if response.status_code != 200: raise ValueError("Invalid status code")

            response, ticker_df = json.loads(response.content), []
            data_map = response.get("componentsByNameMap").get("holdings").get("containersByNameMap").get("all").get("dataPointsByNameMap")

            if product in ["CNDX"]:
                ticker_df = [{"ticker": t, "name": n, "sector": s, "weight": w, "ISIN": isin}
                     for t, n, s, w, isin, asset_class in zip(data_map.get("ticker").get("formattedValue"),
                                                              data_map.get("issueName").get("formattedValue"),
                                                              data_map.get("sectorName").get("formattedValue"),
                                                              data_map.get("holdingPercent").get("formattedValue"),
                                                              data_map.get("isin").get("formattedValue"),
                                                              data_map.get("assetClass").get("formattedValue")) if asset_class == "Equity" and t != "-"]

            elif product in ["IVV", "IWB", "IWM", "IWV"]:
                ticker_df = [{"ticker": t, "name": n, "sector": s, "asset_class": asset_class, "weight": w, "isin": isin, "cusip": cusip, "sedol": sedol}
                             for t, n, s, asset_class, w, isin, cusip, sedol in zip(data_map.get("ticker").get("formattedValue"),
                                                                                    data_map.get("issueName").get("formattedValue"),
                                                                                    data_map.get("sectorName").get("formattedValue"),
                                                                                    data_map.get("assetClass").get("formattedValue"),
                                                                                    data_map.get("holdingPercent").get("formattedValue"),
                                                                                    data_map.get("isin").get("formattedValue"),
                                                                                    data_map.get("cusip").get("formattedValue"),
                                                                                    data_map.get("sedol").get("formattedValue"),)]

            ticker_df = pd.DataFrame(ticker_df)
            if ticker_df.empty: raise ValueError(f"[{product}] No data")

            ticker_df = ticker_df.sort_values(by="ticker").reset_index(drop=True)

            ticker_df.to_csv(os.path.join(dest_dir, f"{product}_{pd.Timestamp.now().__str__().split(' ')[0]}.csv"), index=False)

        except Exception as e: print(f"[{product}] Error: {e}")

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
    download_iShares()

    download_finviz()
