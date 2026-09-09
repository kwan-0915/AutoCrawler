import os
import argparse
import pandas as pd
from tqdm.auto import tqdm

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", help="iShares product name [CNDX | IVV | etc]", default="", type=str)
    parser.add_argument("--start_date", help="Start download date, e.g. 2026-01-01", default="", type=str)
    parser.add_argument("--end_date", help="End download date, e.g. 2026-01-31", default="", type=str)
    args = vars(parser.parse_args())

    if not args.get("product"): raise ValueError("Please specify a valid product name")
    elif not args.get("start_date"): raise ValueError("Please specify a start date")
    elif not args.get("end_date"): raise ValueError("Please specify a end date")

    product, start_date, end_date = args.get("product", ""), args.get("start_date"), args.get("end_date")
    print(f"Compressing data: {product} from {start_date} to {end_date}")

    data_dir = os.path.join(os.getcwd(), "data")

    root_dir = os.path.join(data_dir, "ishares", product)
    root_file = [f for f in os.listdir(root_dir) if start_date <= f.split("_")[1].replace(".csv", "") <= end_date]

    if not len(root_file): raise ValueError(f"[{product}]: No data found between {start_date} - {end_date}")

    df = pd.concat([pd.read_csv(os.path.join(root_dir, f)) for f in sorted(root_file)], axis=0)
    df = df.drop_duplicates(subset=["ticker", "isin"], keep="last").sort_values(by="ticker").reset_index(drop=True)

    if df.empty: raise ValueError(f"[{product}]: Failed to compress data, total files: {len(root_file)}")
    else:
        out_dir = os.path.join(data_dir, "lookup", product)
        if not os.path.exists(out_dir): os.makedirs(out_dir)

        df.to_csv(os.path.join(out_dir, f"{product}_{end_date}.csv"), index=False)

        for f in tqdm(root_file, total=len(root_file), desc="Removing duplicates files"):
            os.remove(os.path.join(root_dir, f))

