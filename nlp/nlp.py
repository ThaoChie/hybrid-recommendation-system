import re
import pandas as pd
from underthesea import pos_tag
# ===== LOAD DATA =====
df = pd.read_csv("data/tiki_thoi_trang_nu_cleaned_final.csv", dtype=str)

def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'\(.*?\)', ' ', text)
    text = re.sub(r'\[.*?\]', ' ', text)
    text = re.sub(r'\d+ml|\d+g|\d+l\d+', ' ', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def extract_product(text):
    text = clean_text(text)
    tagged = pos_tag(text)
    
    result = []
    skip = 0   # cho phép skip tối đa 1 từ
    
    for word, tag in tagged:
        if tag in ["N", "Np", "A", "V"]:   # thêm V (động từ nhẹ)
            result.append(word)
            skip = 0
        else:
            skip += 1
            if skip >= 2:   # chỉ break khi skip quá nhiều
                break
    
    return " ".join(result[:4])


df["product_type"] = df["name"].apply(extract_product)
df.to_csv("tiki_thoi_trang_nu_cleaned_final.csv", index=False, encoding="utf-8-sig")

print("DONE")
print(df[["name","product_type"]].head(10))