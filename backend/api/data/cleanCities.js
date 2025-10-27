const fs = require('fs');

// đọc file JSON
let data = JSON.parse(fs.readFileSync('cities_cleaned.json', 'utf8'));

// danh sách từ cần xóa
const wordsToRemove = ["province of", "province", "city", "tỉnh", "huyện", "Thành phố"];

// hàm xóa từ cố định
function cleanText(str) {
    let result = str;
    wordsToRemove.forEach(word => {
        const regex = new RegExp(word, 'gi');
        result = result.replace(regex, '').trim();
    });
    return result;
}

// hàm chuyển tiếng Việt có dấu sang không dấu
function removeAccents(str) {
    return str.normalize("NFD")               // tách ký tự + dấu
              .replace(/[\u0300-\u036f]/g, '') // bỏ dấu
              .replace(/đ/g, 'd')             // chuyển đ → d
              .replace(/Đ/g, 'D');            // chuyển Đ → D
}

// xử lý toàn bộ array
const processedData = data.map(item => {
    let cleanedName = cleanText(item.name);
    let nonAccentName = removeAccents(cleanedName);
    // optional: capitalize mỗi từ
    nonAccentName = nonAccentName.split(' ')
                                 .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                                 .join(' ');

    return {
        ...item,
        name: nonAccentName
    };
});

// ghi ra file mới
fs.writeFileSync('cities_cleaned.json', JSON.stringify(processedData, null, 2), 'utf8');

console.log("Đã xóa từ cố định và chuyển tên thành phố sang không dấu!");
