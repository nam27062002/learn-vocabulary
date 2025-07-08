from django.utils import translation

def manual_translations(request):
    """Manual translation context processor as fallback"""
    current_lang = translation.get_language()
    
    translations = {
        'en': {
            'learn_english': 'Learn English',
            'home': 'Home',
            'flashcards': 'Flashcards',
            'add_word': 'Add Word',
            'study': 'Study',
            'statistics': 'Statistics',
            'dashboard': 'Dashboard',
            'welcome_message': 'Welcome to LearnEnglish',
            'platform_description': 'Your personal vocabulary learning platform',
            'total_cards': 'Total Cards',
            'recent_cards': 'Recent Cards',
            'progress': 'Progress',
            'add_new_words': 'Add New Words',
            'study_cards': 'Study Cards',
            'add_flashcard': 'Add Flashcard',
            'add_new_flashcard': 'Add New Flashcard',
            'add_vocabulary_description': 'Add new vocabulary to your collection',
            'my_flashcards': 'My Flashcards',
            'vocabulary_collection': 'Your vocabulary collection',
        },
        'vi': {
            'learn_english': 'Học Tiếng Anh',
            'home': 'Trang chủ',
            'flashcards': 'Thẻ từ vựng',
            'add_word': 'Thêm từ',
            'study': 'Học tập',
            'statistics': 'Thống kê',
            'dashboard': 'Bảng điều khiển',
            'welcome_message': 'Chào mừng đến với LearnEnglish',
            'platform_description': 'Nền tảng học từ vựng cá nhân của bạn',
            'total_cards': 'Tổng số thẻ',
            'recent_cards': 'Thẻ gần đây',
            'progress': 'Tiến độ',
            'add_new_words': 'Thêm từ mới',
            'study_cards': 'Học thẻ từ',
            'add_flashcard': 'Thêm Flashcard',
            'add_new_flashcard': 'Thêm Flashcard Mới',
            'add_vocabulary_description': 'Thêm từ vựng mới vào bộ sưu tập của bạn',
            'my_flashcards': 'Thẻ từ vựng của tôi',
            'vocabulary_collection': 'Bộ sưu tập từ vựng của bạn',
        }
    }
    
    return {
        'manual_texts': translations.get(current_lang, translations['en']),
        'current_language_code': current_lang
    } 