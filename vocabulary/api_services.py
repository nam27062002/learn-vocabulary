import requests

def get_word_suggestions_from_datamuse(query):
    """Fetches word suggestions from Datamuse API.

    Args:
        query (str): The search query.

    Returns:
        list: A list of suggested words, or an empty list if an error occurs.
    """
    suggestions = []
    if not query:
        return suggestions

    datamuse_url = f"https://api.datamuse.com/sug?s={query}"
    try:
        response = requests.get(datamuse_url)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        suggestions = [item['word'] for item in data]
    except requests.exceptions.RequestException as e:
        # In a real application, you might want to log this error more formally
        print(f"[ERROR] Error calling Datamuse API for query '{query}': {e}")
    except ValueError as e: # Handles JSON decoding errors
        print(f"[ERROR] JSON decoding error from Datamuse API: {e}")
    return suggestions

def check_word_spelling_with_languagetool(word):
    """Checks the spelling of a word using LanguageTool API.

    Args:
        word (str): The word to check.

    Returns:
        bool: True if the word is correct, False otherwise.
    """
    if not word:
        return False

    languagetool_url = "https://api.languagetool.org/v2/check"
    payload = {
        'text': word,
        'language': 'en-US' # Adjust language as needed
    }
    try:
        response = requests.post(languagetool_url, data=payload)
        response.raise_for_status()
        data = response.json()
        is_correct = len(data.get('matches', [])) == 0
        return is_correct
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error calling LanguageTool API for word '{word}': {e}")
    except ValueError as e: # Handles JSON decoding errors
        print(f"[ERROR] JSON decoding error from LanguageTool API: {e}")
    return False 