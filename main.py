import os
import json
import warnings
import requests
import pandas as pd
from tqdm.auto import tqdm

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
        "CNDX": f"{base_url}&locale=en_GB&portfolioId=253741",  # Nasdaq 100
        "IVV": f"{base_url}&locale=en_US&portfolioId=239726",   # S&P 500
        "IJH": f"{base_url}&locale=en_US&portfolioId=239763",   # S&P 500 mid-cap
        "IJR": f"{base_url}&locale=en_US&portfolioId=239774",   # S&P 500 small-cap
        "IWB": f"{base_url}&locale=en_US&portfolioId=239707",   # Russell 1000
        "IWM": f"{base_url}&locale=en_US&portfolioId=239710",   # Russell 2000
        "IWV": f"{base_url}&locale=en_US&portfolioId=239714",   # Russell 3000
    }

    cur_date = pd.Timestamp.now().__str__().split(" ")[0]

    pbar = tqdm(url_mapper.items(), total=len(url_mapper.keys()))
    for product, url in pbar:
        pbar.set_description(f"[iShares] Downloading {product}")

        dest_dir = os.path.join(root_dir, "ishares", product)
        if not os.path.exists(dest_dir): os.makedirs(dest_dir)

        try:
            response = requests.get(url=url, headers=custom_headers)
            if response.status_code != 200: raise ValueError("Invalid status code")

            response, ticker_df = json.loads(response.content), []

            try: cur_date = response.get("componentsByNameMap").get("holdings").get("containersByNameMap").get("all").get("dataPointsByNameMap").get("asOfDate").get("value")
            except (AttributeError, Exception) as e: pass

            data_map = response.get("componentsByNameMap").get("holdings").get("containersByNameMap").get("all").get("dataPointsByNameMap")

            if product in ["CNDX"]:
                ticker_df = [{"ticker": t, "name": n, "sector": s, "asset_class": asset_class, "weight": w, "isin": isin, }
                             for t, n, s, asset_class, w, isin in zip(data_map.get("ticker").get("formattedValue"),
                                                                      data_map.get("issueName").get("formattedValue"),
                                                                      data_map.get("sectorName").get("formattedValue"),
                                                                      data_map.get("assetClass").get("formattedValue"),
                                                                      data_map.get("holdingPercent").get("formattedValue"),
                                                                      data_map.get("isin").get("formattedValue"),
                                                                      )]

            elif product in ["IVV", "IJH", "IJR", "IWB", "IWM", "IWV"]:
                w_key = "marketWeight" if product in ["IVV", "IJH", "IJR"] else "holdingPercent"
                
                ticker_df = [{"ticker": t, "name": n, "sector": s, "asset_class": asset_class, "weight": w, "isin": isin, "cusip": cusip, "sedol": sedol}
                             for t, n, s, asset_class, w, isin, cusip, sedol in zip(data_map.get("ticker").get("formattedValue"),
                                                                                    data_map.get("issueName").get("formattedValue"),
                                                                                    data_map.get("sectorName").get("formattedValue"),
                                                                                    data_map.get("assetClass").get("formattedValue"),
                                                                                    data_map.get(f"{w_key}").get("formattedValue"),
                                                                                    data_map.get("isin").get("formattedValue"),
                                                                                    data_map.get("cusip").get("formattedValue"),
                                                                                    data_map.get("sedol").get("formattedValue"),
                                                                                    )]

            if isinstance(cur_date, int): cur_date = str(pd.to_datetime(str(cur_date)).date())

            ticker_df = pd.DataFrame(ticker_df)
            if ticker_df.empty: raise ValueError(f"[{product}] No data")

            ticker_df = ticker_df.sort_values(by="ticker").reset_index(drop=True)

            ticker_df.to_csv(os.path.join(dest_dir, f"{product}_{cur_date}.csv"), index=False)

        except Exception as e: print(f"[{product}] Error: {e}")


if __name__ == "__main__":
    download_iShares()
