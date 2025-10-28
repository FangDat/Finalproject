import pandas as pd
import json

# Đọc file CSV với delimiter là dấu ';'
df = pd.read_csv("worldcities.csv", delimiter=";")

# Nếu lat/lng có dấu phẩy (ví dụ "10,123") → đổi sang dấu chấm
if df["lat"].dtype == object:
    df["lat"] = df["lat"].astype(str).str.replace(",", ".").astype(float)
if df["lng"].dtype == object:
    df["lng"] = df["lng"].astype(str).str.replace(",", ".").astype(float)

# Giữ lại đúng 5 cột cần thiết
df = df[["city", "city_ascii", "lat", "lng", "admin_name"]]

# Nếu admin_name bị NaN → thay bằng city
df["admin_name"] = df.apply(
    lambda row: row["city"] if pd.isna(row["admin_name"]) else row["admin_name"],
    axis=1
)

# Thay các NaN còn lại bằng None để JSON hợp lệ
df = df.where(pd.notnull(df), None)

# Chuyển DataFrame → list các dict
records = df.to_dict(orient="records")

# Ghi ra file JSON
with open("worldcities.json", "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"✅ Đã chuyển {len(records)} dòng sang worldcities.json (đã thay admin_name bị NaN bằng city)!")
