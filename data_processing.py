import pandas as pd
import re
import numpy as np

def clean_data(input_file, output_file=None):
    """
    Làm sạch dữ liệu Tiki (strict version + xóa trùng tên):
    - Xóa hàng chứa #VALUE!
    - Buộc 5 cột số thỏa mãn:
      - price, original_price, discount: là số
      - rating: ≤ 5.0
      - review_count: số nguyên ≥ 0
    - XÓA HÀNG NẾU CỘT 'name' TRÙNG NHAU (giữ lại dòng đầu tiên)
    """
    
    required_numeric_cols = ['price', 'original_price', 'discount', 'rating', 'review_count']

    # ── 1. Đọc file ──────────────────────────────────────────────
    try:
        if input_file.lower().endswith('.csv'):
            df = pd.read_csv(input_file, dtype=str, low_memory=False)
        else:
            df = pd.read_excel(input_file, dtype=str)
    except Exception as e:
        print(f"Lỗi đọc file: {e}")
        return None

    print(f"Số hàng ban đầu: {len(df):,}")
    original_len = len(df)

    # ── 2. Xóa hàng chứa #VALUE! ────────────────────────────────
    has_error = df.apply(
        lambda row: row.astype(str).str.contains(r'#VALUE!', case=False, na=False).any(),
        axis=1
    )
    if has_error.any():
        print(f" → Xóa {has_error.sum():,} hàng chứa #VALUE!")
        df = df[~has_error]

    # ── 3. Hàm chuyển đổi số ─────────────────────────────────────
    def to_clean_float(x):
        if pd.isna(x) or str(x).strip() == '':
            return np.nan
        cleaned = re.sub(r'[^\d\.\-,]', '', str(x).strip())
        if ',' in cleaned and '.' not in cleaned.split(',')[-1]:
            cleaned = cleaned.replace(',', '.')
        cleaned = cleaned.replace(',', '')
        try:
            return float(cleaned)
        except:
            return np.nan

    def to_clean_int_nonneg(x):
        val = to_clean_float(x)
        if pd.isna(val):
            return np.nan
        if val.is_integer() and val >= 0:
            return int(val)
        return np.nan

    # ── 4. Clean & validate các cột số ───────────────────────────
    bad_rows_mask = pd.Series(False, index=df.index)
    missing_cols = [col for col in required_numeric_cols if col not in df.columns]

    if missing_cols:
        print(f"CẢNH BÁO: Thiếu cột: {', '.join(missing_cols)} → coi như lỗi")

    print("\nKiểm tra và làm sạch các cột số bắt buộc:")

    for col in required_numeric_cols:
        if col not in df.columns:
            bad_rows_mask = pd.Series(True, index=df.index)
            continue

        if col == 'review_count':
            cleaned = df[col].apply(to_clean_int_nonneg)
            invalid = cleaned.isna() & df[col].notna() & (df[col].astype(str).str.strip() != '')
            reason = "không phải số nguyên ≥ 0"
        elif col == 'rating':
            cleaned = df[col].apply(to_clean_float)
            invalid = (
                cleaned.isna() |
                (cleaned > 5.0) |
                (cleaned < 0)
            ) & df[col].notna() & (df[col].astype(str).str.strip() != '')
            reason = "không hợp lệ hoặc > 5.0"
        else:
            cleaned = df[col].apply(to_clean_float)
            invalid = cleaned.isna() & df[col].notna() & (df[col].astype(str).str.strip() != '')
            reason = "không phải số hợp lệ"

        if invalid.any():
            print(f"  Cột '{col}': {invalid.sum():,} giá trị vi phạm ({reason})")
        
        df[col] = cleaned
        bad_rows_mask = bad_rows_mask | invalid

    # Xóa dòng vi phạm điều kiện số
    if bad_rows_mask.any():
        print(f" → Xóa {bad_rows_mask.sum():,} dòng do vi phạm điều kiện số")
        df = df[~bad_rows_mask]

    # ── 5. Xóa trùng lặp theo cột 'name' (giữ dòng đầu tiên) ─────
    if 'name' in df.columns:
        before_dedup = len(df)
        df = df.drop_duplicates(subset=['name'], keep='first')
        dup_removed = before_dedup - len(df)
        if dup_removed > 0:
            print(f" → Xóa {dup_removed:,} dòng trùng tên (giữ lại bản đầu tiên)")
    else:
        print("CẢNH BÁO: Không tìm thấy cột 'name' → không thực hiện xóa trùng lặp")

    # ── 6. Báo cáo kết quả ───────────────────────────────────────
    removed_total = original_len - len(df)
    print(f"\nKết quả cuối cùng:")
    print(f"   Số hàng còn lại: {len(df):,}")
    print(f"   Tổng đã xóa: {removed_total:,} dòng ({removed_total/original_len:.1%} nếu original_len > 0)" if original_len > 0 else "0%")
    
    if len(df) == 0:
        print("CẢNH BÁO: KHÔNG CÒN DÒNG NÀO SAU KHI LÀM SẠCH!")

    # ── 7. Lưu file ──────────────────────────────────────────────
    if output_file is None:
        base, ext = input_file.rsplit('.', 1)
        output_file = f"{base}_cleaned_final.{ext}"

    try:
        if output_file.lower().endswith('.csv'):
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
        else:
            df.to_excel(output_file, index=False)
        print(f"Đã lưu file: {output_file}")
    except Exception as e:
        print(f"Lỗi lưu file: {e}")

    return df


# ── Chạy ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    df_cleaned = clean_data(
        input_file="",   # thay bằng file của bạn
    )