import fs from "fs";

// Đọc dữ liệu JSON gốc
const data = JSON.parse(fs.readFileSync("worldcities.json", "utf8"));

// Các tiền tố cần xóa (phân biệt chữ hoa/thường và có dấu)
const prefixes = [
  "Thành phố",
  "Thành Phố",
  "Thanh Pho",
  "Thanh phố",
  "City of",
  "Ciudad de",
  "Ville de",
  "Comune di",
  "Municipio de",
  "Prefecture of"
];

// Hàm xóa tiền tố trong chuỗi
function cleanName(name) {
  if (!name) return "";

  let cleaned = name.trim();

  for (const prefix of prefixes) {
    const regex = new RegExp("^" + prefix + "\\s+", "i");
    cleaned = cleaned.replace(regex, ""); // Xóa tiền tố
  }

  // Xóa khoảng trắng thừa
  cleaned = cleaned.trim();

  // Viết hoa chữ cái đầu (tuỳ chọn, giúp đồng nhất)
  cleaned = cleaned.charAt(0).toUpperCase() + cleaned.slice(1);

  return cleaned;
}

// Làm sạch từng dòng
const cleanedData = data.map((row) => ({
  city: cleanName(row.city),
  city_ascii: cleanName(row.city_ascii),
  lat: row.lat,
  lng: row.lng,
  admin_name: cleanName(row.admin_name)
}));

// Ghi ra file mới
fs.writeFileSync(
  "worldcities.json",
  JSON.stringify(cleanedData, null, 2),
  "utf8"
);

console.log(`✅ Đã làm sạch ${cleanedData.length} dòng và lưu vào worldcities_clean.json`);
