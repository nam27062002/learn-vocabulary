import requests
from googletrans import Translator
import logging
from .audio_service import EnhancedCambridgeAudioFetcher

# Set up logging
logger = logging.getLogger(__name__)

def get_cambridge_british_audio(word):
    """
    Fetch British English audio from Cambridge Dictionary.
    Prioritizes UK pronunciation over US pronunciation.

    Args:
        word (str): The word to fetch audio for

    Returns:
        str: Audio URL if found, empty string otherwise
    """
    if not word or not word.strip():
        return ""

    try:
        # Use the enhanced Cambridge audio fetcher
        enhanced_fetcher = EnhancedCambridgeAudioFetcher()
        audio_options = enhanced_fetcher.fetch_multiple_audio_sources(word.strip())

        if not audio_options:
            logger.info(f"No audio options found for word: {word}")
            return ""

        # Prioritize UK/British pronunciation
        uk_audio = None
        fallback_audio = None

        for option in audio_options:
            if not option.is_valid:
                continue

            # Check if this is UK/British pronunciation
            label_lower = option.label.lower()
            if 'uk' in label_lower or 'british' in label_lower:
                uk_audio = option.url
                break

            # Keep first valid audio as fallback
            if fallback_audio is None:
                fallback_audio = option.url

        # Return UK audio if found, otherwise fallback to any available audio
        selected_audio = uk_audio or fallback_audio or ""

        if selected_audio:
            logger.info(f"Selected audio for '{word}': {selected_audio}")
        else:
            logger.info(f"No valid audio found for word: {word}")

        return selected_audio

    except Exception as e:
        logger.error(f"Error fetching Cambridge audio for word '{word}': {e}")
        return ""

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

        # Get Cambridge Dictionary audio (prioritizing British English)
        cambridge_audio = get_cambridge_british_audio(word)

        if isinstance(api_phonetics, list):
            for p in api_phonetics:
                if isinstance(p, dict):
                    # Replace dictionaryapi.dev audio with Cambridge Dictionary audio
                    phonetics.append({
                        "text": p.get("text", ""),
                        "audio": cambridge_audio  # Use Cambridge audio instead of p.get("audio", "")
                    })

        # If no phonetics from dictionaryapi.dev but we have Cambridge audio, create a phonetic entry
        if not phonetics and cambridge_audio:
            phonetics.append({
                "text": "",  # No phonetic text available
                "audio": cambridge_audio
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