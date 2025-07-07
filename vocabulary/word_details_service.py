import requests
from googletrans import Translator

def get_word_details(word):
    # Gọi API để lấy dữ liệu
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        response = requests.get(url)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        if not data: # API might return empty list for no word found
            return {"error": "Không tìm thấy từ"}
        
        data = data[0] # Get the first entry if multiple are returned
        
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
                "synonyms": meaning.get("synonyms", []), # General synonyms for this part of speech
                "antonyms": meaning.get("antonyms", []), # General antonyms for this part of speech
                "definitions": []
            }
            
            for definition in meaning.get("definitions", []):
                en_def = definition.get("definition", "")
                # Dịch sang tiếng Việt. Có thể có độ trễ do gọi Google Translate API
                vi_def = translator.translate(en_def, src='en', dest='vi').text if en_def else ""
                
                def_info = {
                    "en": en_def,
                    "vi": vi_def,
                    "synonyms": definition.get("synonyms", []), # Synonyms specific to this definition
                    "antonyms": definition.get("antonyms", []) # Antonyms specific to this definition
                }
                meaning_info["definitions"].append(def_info)
            
            meanings.append(meaning_info)
        
        result["meanings"] = meanings
        return result
    
    except requests.exceptions.RequestException as e:
        return {"error": f"Lỗi kết nối hoặc API: {e}"}
    except (ValueError, IndexError) as e:
        return {"error": f"Lỗi xử lý dữ liệu từ API: {e}"}
    except Exception as e:
        return {"error": f"Đã xảy ra lỗi không xác định: {e}"} 