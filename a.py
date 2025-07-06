import requests
from googletrans import Translator

def get_word_details(word):
    # Gọi API để lấy dữ liệu
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    response = requests.get(url)
    
    if response.status_code != 200:
        return {"error": "Không tìm thấy từ hoặc lỗi API"}
    
    data = response.json()[0]
    
    # Trích xuất thông tin cơ bản
    result = {
        "word": data.get("word", ""),
        "license": data.get("license", {}).get("name", ""),
        "source_url": data.get("sourceUrls", [""])[0]
    }
    
    # Xử lý thông tin phát âm và audio
    phonetics = []
    for ph in data.get("phonetics", []):
        if ph.get("text") or ph.get("audio"):
            phonetic_info = {
                "text": ph.get("text", ""),
                "audio": ph.get("audio", ""),
                "source_url": ph.get("sourceUrl", "")
            }
            phonetics.append(phonetic_info)
    result["phonetics"] = phonetics
    
    # Xử lý nghĩa và định nghĩa
    meanings = []
    translator = Translator()
    
    for meaning in data.get("meanings", []):
        meaning_info = {
            "part_of_speech": meaning.get("partOfSpeech", ""),
            "synonyms": meaning.get("synonyms", []),
            "antonyms": meaning.get("antonyms", []),
            "definitions": []
        }
        
        for definition in meaning.get("definitions", []):
            en_def = definition.get("definition", "")
            vi_def = translator.translate(en_def, src='en', dest='vi').text if en_def else ""
            
            def_info = {
                "en": en_def,
                "vi": vi_def,
                "synonyms": definition.get("synonyms", []),
                "antonyms": definition.get("antonyms", [])
            }
            meaning_info["definitions"].append(def_info)
        
        meanings.append(meaning_info)
    
    result["meanings"] = meanings
    return result

# Sử dụng hàm
word_data = get_word_details("meticulous")

# In kết quả chi tiết
print(f"Từ: {word_data['word']}")
print(f"Giấy phép: {word_data['license']}")
print(f"Nguồn: {word_data['source_url']}\n")

print("Phát âm:")
for i, ph in enumerate(word_data['phonetics'], 1):
    print(f"  {i}. Phiên âm: {ph['text']}")
    print(f"     Audio: {ph['audio']}")
    print(f"     Nguồn audio: {ph['source_url']}")

print("\nNghĩa:")
for meaning in word_data['meanings']:
    print(f"\nTừ loại: {meaning['part_of_speech']}")
    print(f"Từ đồng nghĩa: {', '.join(meaning['synonyms'])}")
    print(f"Từ trái nghĩa: {', '.join(meaning['antonyms'])}")
    
    for j, definition in enumerate(meaning['definitions'], 1):
        print(f"\n  Định nghĩa {j}:")
        print(f"    Tiếng Anh: {definition['en']}")
        print(f"    Tiếng Việt: {definition['vi']}")
        print(f"    Từ đồng nghĩa: {', '.join(definition['synonyms'])}")
        print(f"    Từ trái nghĩa: {', '.join(definition['antonyms'])}")