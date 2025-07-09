import requests
from googletrans import Translator

def get_word_details(word):
    """
    Lấy chi tiết đầy đủ của một từ một cách an toàn.
    Hàm này được thiết kế để xử lý các cấu trúc dữ liệu không nhất quán từ API.
    """
    api_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list) or not data:
            return {"error": f"Không tìm thấy dữ liệu cho từ '{word}'."}
        
        word_data = data[0]
        if not isinstance(word_data, dict):
            return {"error": "Định dạng dữ liệu từ API không hợp lệ."}

        # Trích xuất phát âm một cách an toàn
        phonetics = []
        api_phonetics = word_data.get('phonetics', [])
        if isinstance(api_phonetics, list):
            for p in api_phonetics:
                if isinstance(p, dict):
                    phonetics.append({
                        "text": p.get("text", ""),
                        "audio": p.get("audio", "")
                    })

        # Trích xuất nghĩa một cách an toàn
        meanings = []
        api_meanings = word_data.get('meanings', [])
        if isinstance(api_meanings, list):
            for m in api_meanings:
                if not isinstance(m, dict):
                    continue

                definitions = []
                api_definitions = m.get('definitions', [])
                if isinstance(api_definitions, list):
                    for d in api_definitions:
                        if isinstance(d, dict):
                            definitions.append({
                                "en": d.get("definition", ""),
                                "example": d.get("example", "")
                            })
                
                meanings.append({
                    "part_of_speech": m.get("partOfSpeech", ""),
                    "definitions": definitions
                })

        return {
            "word": word_data.get("word", word),
            "phonetics": phonetics,
            "meanings": meanings
        }

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {"error": f"Từ '{word}' không tồn tại trong từ điển."}
        return {"error": f"Lỗi HTTP khi gọi API từ điển: {e}"}
    except Exception as e:
        print(f"Lỗi không mong muốn trong get_word_details cho từ '{word}': {e}")
        return {"error": "Lỗi hệ thống khi đang xử lý yêu cầu từ điển."} 