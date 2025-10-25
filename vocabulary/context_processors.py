from django.utils import translation
from django.conf import settings
import json

# Only import gettext if i18n is enabled
if getattr(settings, 'USE_I18N', False):
    from django.utils.translation import gettext as _
else:
    # Fallback function when i18n is disabled
    def _(message):
        return str(message)

def i18n_compatible_translations(request):
    """
    Hybrid translation context processor that provides both Django i18n
    and legacy manual_texts for backward compatibility during migration.
    """
    # Get language from session first (for legacy system), then fall back to Django's i18n
    current_lang = request.session.get('django_language', translation.get_language())

    # If Django i18n is disabled, default to 'en'
    if not current_lang:
        current_lang = 'en'

    # Legacy translations for backward compatibility
    # These will be gradually removed as templates are migrated to use {% trans %}
    legacy_translations = {
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
            # Authentication texts
            'login_title': 'Login',
            'signup_title': 'Sign Up',
            'welcome_back': 'Welcome back!',
            'login_subtitle': 'Sign in to your account',
            'create_account': 'Create Account',
            'signup_subtitle': 'Start your vocabulary learning journey',
            'login_with_google': 'Sign in with Google',
            'signup_with_google': 'Sign up with Google',
            'or': 'or',
            'email_address': 'Email address',
            'password': 'Password',
            'confirm_password': 'Confirm password',
            'remember_me': 'Remember me',
            'forgot_password': 'Forgot password?',
            'sign_in': 'Sign in',
            'sign_up': 'Sign up',
            'dont_have_account': "Don't have an account?",
            'already_have_account': 'Already have an account?',
            'email_verification_notice': 'We will send you a verification email to activate your account.',
            'logout': 'Logout',
            'profile': 'Profile',
            # Decks
            'my_decks': 'My Decks',
            'back_to_all_decks': 'Back to all decks',
            # Statistics
            'statistics_title': 'Statistics',
            'total_decks': 'Total Decks',
            'average_cards_per_deck': 'Average Cards per Deck',
            'cards_per_deck': 'Cards per Deck',
            'no_decks_message': 'You have no decks yet.',
            # Study labels
            'start_study': 'Start Study',
            'select_decks': 'Select decks to study',
            'no_cards_due': 'No cards due for review today.',
            'grade_again': 'Again',
            'grade_hard': 'Hard',
            'grade_good': 'Good',
            'grade_easy': 'Easy',
            'show_answer': 'Show Answer',
            'mode_multiple_choice': 'Multiple Choice',
            'mode_type_answer': 'Type Answer',
            'select_mode': 'Select study mode',
            'check': 'Check',
            'correct': 'Correct!',
            'incorrect': 'Incorrect',
            'answer_placeholder': 'Type your answer...',
            'progress': 'Progress',
            'study_complete_title': 'Great job!',
            'study_complete_text': 'You have reviewed all due cards.',
            'next_card': 'Next Card →',
            'vietnamese_meaning': 'Vietnamese meaning',
            'dictation_placeholder': 'Listen and type the English word...',
            'select_at_least_one_deck': 'Please select at least one deck',
            # Add flashcard form
            'select_deck': 'Select deck:',
            'please_select_deck': '-- Please select a deck --',
            'create_new_deck': '-- Create new deck --',
            'term_label': 'TERM',
            'phonetic_label': 'PHONETIC',
            'english_definition_label': 'DEFINITION (ENGLISH)',
            'vietnamese_definition_label': 'DEFINITION (VIETNAMESE)',
            'term_placeholder': 'e.g., \'serendipity\'',
            'phonetic_placeholder': '/ˌser.ənˈdɪp.ə.t̬i/',
            'definition_placeholder': 'A concise and clear definition...',
            'vietnamese_placeholder': 'Vietnamese translation...',
            'upload_image': 'Upload image',
            'add_new_card': '➕ Add new card',
            'save_all_flashcards': '💾 Save all Flashcards',
            'drag_to_move': 'Drag to move card',
            'delete_card': 'Delete card',
            'confirm_delete_card': 'Delete Card',
            'delete_card_warning': 'Are you sure you want to delete this card? This action cannot be undone.',
            'cancel': 'Cancel',
            'delete': 'Delete',
            'part_of_speech': 'part of speech',
            'listen': 'Listen',

            # Quick Add Words section
            'quick_add_multiple_words': 'Quick Add Multiple Words',
            'quick_add_placeholder': 'Enter multiple words separated by | (pipe character). Example: assistant|cry|usual|file|ban|ice|column|currently|prepare|acceptable',
            'quick_add_info': 'Separate words with | (pipe) character. Each word will be automatically processed for spelling, definitions, and duplicates.',
            'generate_cards': 'Generate Cards',
            'processing_words': 'Processing words...',
            'processing_word_individual': 'Processing "{word}" ({current}/{total})...',

            # Study deck selection
            'search_decks': 'Search decks...',
            'select_all': 'Select All',
            'deselect_all': 'Deselect All',
            'decks_selected': 'decks selected',

            # SweetAlert messages
            'create_new_deck_title': 'Create New Deck',
            'deck_name_label': 'Deck Name',
            'deck_name_placeholder': 'Example: Day 1, IELTS Topic: Work...',
            'deck_name_required': 'You need to enter a name for the deck!',
            'cancel': 'Cancel',
            'confirm': 'Confirm',
            'created': 'Created!',
            'deck_created_success': 'Deck "{deck_name}" has been created successfully.',
            'cannot_create_deck': 'Cannot create deck',
            'unknown_error': 'Unknown error',

            # Duplicate warnings
            'duplicate_word_detected': 'Duplicate Word Detected',
            'word_already_exists': 'The word "{word}" already exists in your vocabulary.',
            'use_different_word': 'Please use a different word or modify the existing one.',

            # Processing and validation messages
            'no_words_found': 'No Words Found',
            'enter_words_pipe': 'Please enter some words separated by | (pipe) character.',
            'no_deck_selected': 'No Deck Selected',
            'select_deck_before_adding': 'Please select a deck before adding words.',
            'cannot_delete_only_card': 'Cannot delete the only card!',
            'translating': 'Translating...',
            'translation_not_available': 'Translation not available.',
            'translation_error': 'Translation error.',

            # Quick Add results
            'quick_add_results': 'Quick Add Results',
            'words_added_successfully': 'Successfully added {count} words: {words}',
            'duplicate_words_skipped': 'Skipped {count} duplicate words: {words}',
            'words_with_errors': 'Failed to process {count} words: {words}',
            'no_words_processed': 'No words were processed. Please check your input.',

            # Flashcard save success messages
            'saved_successfully': 'Saved successfully!',
            'words_added_to_collection': 'Words have been added to the collection: {words}',

            'correct_answer': 'Correct answer',
            # Console messages
            'console_welcome': '🎓 LearnEnglish App',
            'console_subtitle': 'Welcome to the developer console!',
            'console_built_with': 'Built with Django + Tailwind CSS + JavaScript ❤️',
            # Deck list
            'cards_text': 'cards',
            'no_decks_yet': 'You don\'t have any decks yet.',
            'get_started_by': 'Get started by',
            'adding_flashcards': 'adding some new flashcards',
            # Study
            'search_cambridge': 'Search on Cambridge Dictionary',
            'continue_button': 'Continue',
            'no_decks_selected': 'No decks selected',
            'back_to_login': 'Back to Login',
            'no_decks_available': 'No decks available',
            # Edit functionality
            'edit_card': 'Edit Card',
            'save_changes': 'Save Changes',
            'cancel_edit': 'Cancel',
            'edit_mode': 'Edit Mode',
            'card_updated_successfully': 'Card updated successfully!',
            'error_updating_card': 'Error updating card',
            'confirm_cancel_edit': 'Are you sure you want to cancel? Unsaved changes will be lost.',
            'this_deck_empty': 'This deck is empty.',
            'add_some_cards': 'Add some cards!',
            # Audio status indicators
            'has_audio': 'Has Audio',
            'no_audio': 'No Audio',
            'audio_available': 'Audio Available',
            'audio_missing': 'Audio Missing',
            'add_audio_url': 'Add audio URL to enable pronunciation',
            'filter_by_audio': 'Filter by Audio Status',
            'show_all_cards': 'Show All Cards',
            'show_cards_with_audio': 'Cards with Audio',
            'show_cards_without_audio': 'Cards without Audio',
            # Deck editing
            'edit_deck_name': 'Edit Deck Name',
            'deck_name': 'Deck Name',
            'save_deck_name': 'Save Name',
            'cancel_deck_edit': 'Cancel',
            'deck_name_updated': 'Deck name updated successfully!',
            'error_updating_deck': 'Error updating deck name',
            'deck_name_required': 'Deck name is required',
            # Audio fetching
            'fetch_missing_audio': 'Fetch Missing Audio',
            'fetching_audio': 'Fetching audio...',
            'audio_fetched_successfully': 'Audio fetched successfully!',
            'no_audio_found': 'No audio found for some words',
            'audio_fetch_error': 'Error fetching audio',
            'audio_fetch_complete': 'Audio fetch complete',
            'cards_updated': 'cards updated',
            'auto_fetch_audio': 'Auto-fetch audio for new cards',

            # Enhanced Audio Fetching
            'enhanced_audio_selection': 'Enhanced Audio Selection',
            'select_audio_pronunciation': 'Select Audio Pronunciation for:',
            'available_audio_options': 'Available Audio Options',
            'current_audio': 'Current Audio',
            'no_current_audio': 'No current audio',
            'preview': 'Preview',
            'us_pronunciation': 'US pronunciation',
            'uk_pronunciation': 'UK pronunciation',
            'primary_pronunciation': 'Primary pronunciation',
            'alternative_pronunciation': 'Alternative pronunciation',
            'ready': 'Ready',
            'playing': 'Playing',
            'keep_current': 'Keep Current',
            'confirm_selection': 'Confirm Selection',
            'no_audio_options_found': 'No audio options found',
            'try_checking_spelling': 'Try checking the word spelling or search manually on Cambridge Dictionary',
            'fetching_audio_options': 'Fetching audio options...',
            'audio_selection_updated': 'Audio pronunciation updated successfully!',
            'error_updating_audio': 'Error updating audio selection',
            'please_select_audio': 'Please select an audio option',
            'enhanced_audio_fetch': 'Enhanced Audio Fetch',
            'get_multiple_pronunciations': 'Get Multiple Pronunciations',

            # Study Mode Selection
            'study_mode': 'Study Mode',
            'normal_study_by_decks': 'Normal Study (by Decks)',
            'study_random_words': 'Study Random Words',
            'number_of_words': 'Number of Words',
            'available_words': 'Available Words',
            'select_decks': 'Select Decks',
            'no_decks_selected': 'No decks selected',
            'no_decks_available': 'No decks available',
            'start_study': 'Start Study',
            'correct': 'Correct',
            'incorrect': 'Incorrect',
            'check': 'Check',
            'answer_placeholder': 'Enter your answer...',
            'grade_again': 'Again',
            'grade_hard': 'Hard',
            'grade_good': 'Good',
            'grade_easy': 'Easy',
            'view_in_cambridge': 'View in Cambridge Dictionary',
            'no_cards_due': 'No cards due',
            'back_to_selection': 'Back to Selection',
            # Audio and study interface
            'play_audio': 'Play Audio',
            'listen_and_type': 'Listen and type what you hear',
            'type_what_you_hear': 'Type what you hear...',
            'correct_answer': 'Correct!',
            'incorrect_answer': 'Incorrect',
            'replay_audio': 'Replay',
            'english_label': 'English:',
            'vietnamese_label': 'Vietnamese:',

            # Deck detail interface
            'word_required': 'Word is required',
            'definition_required': 'At least one definition is required',
            'saving': 'Saving...',
            'previous_deck': 'Previous deck',
            'next_deck': 'Next deck',
            'card_updated_successfully': 'Card updated successfully!',
            'error_updating_card': 'Error updating card',
            'confirm_cancel_edit': 'Are you sure you want to cancel? Unsaved changes will be lost.',
            'deck_name_required': 'Deck name is required',
            'deck_name_updated': 'Deck name updated successfully!',
            'error_updating_deck': 'Error updating deck name',
            'save_deck_name': 'Save Name',
            'fetching_audio': 'Fetching audio...',
            'audio_fetched_successfully': 'Audio fetched successfully!',
            'cards_updated': 'cards updated',
            'no_audio_found': 'No audio found for some words',
            'audio_fetch_error': 'Error fetching audio',
            'audio_fetch_complete': 'Audio fetch complete',
            'found_label': 'Found:',
            'method_not_allowed': 'Method not allowed. Please refresh the page and try again.',
            'permission_denied': 'Permission denied. Please refresh the page and try again.',
            'card_not_found': 'Card not found. Please refresh the page and try again.',
            'server_response_error': 'Server response error. Please try again.',
            'no_definitions_available': 'No definitions available',
            'audio_url_label': 'Audio URL',
            'audio_url_placeholder': 'https://example.com/audio.mp3',
            'definitions_label': 'Definitions',
            'signed_in_as': 'Signed in as',
            'select_deck_alert': 'Please select at least one deck to study.',
            'no_decks_selected': 'No decks selected',
            'words_unit': 'words',
            'deck_study_description': 'Study specific flashcard decks',
            'random_study_description': 'Study random words from all decks',
            'sound_feedback': 'Sound Feedback',
            'review_incorrect_words': 'Review Incorrect Words',
            'review_study_description': 'Study words you previously answered incorrectly',
            'incorrect_words_count': 'incorrect words to review',
            'review_mode_description': 'Practice words you answered incorrectly in their original question format until you master them.',
            'start_review': 'Start Review',
            'multiple_choice': 'Multiple Choice',
            'input_mode': 'Input Mode',
            'dictation_mode': 'Dictation Mode',
            'review_completed_title': 'Congratulations!',
            'review_completed_message': 'You have successfully reviewed all incorrect words!',
            'continue_studying': 'Continue Studying',
            
            # Additional messages for add flashcard page
            'processing_error': 'Processing Error',
            'processing_error_message': 'An error occurred while processing the words. Please try again.',
            'duplicate_words_detected': 'Duplicate Words Detected',
            'duplicate_words_message_html': 'The following words already exist in your vocabulary:<br>{words}<br><br>Please remove or modify these words before saving.',
            'empty_input': 'Empty Input',
            'replace_existing_cards': 'Replace Existing Cards?',
            'replace_cards_confirmation_html': 'This will <strong>clear all current cards</strong> and replace them with {count} new cards.<br><br>Are you sure you want to continue?',
            'select_deck_before_saving': 'Please select or create a deck before saving.',
            'no_data_title': 'No Data',
            'enter_at_least_one_word': 'Please enter at least one vocabulary word.',
            'error_title': 'Error!',
            'error_occurred_message': 'An error occurred: {error}',
            'connection_error_title': 'Connection Error',
            'connection_error_message': 'Could not send request to server: {error}',
            'yes_replace_all': 'Yes, Replace All',

            # Blacklist Management
            'blacklist_management': 'Quản lý danh sách đen',
            'manage_words_excluded': 'Quản lý các từ bị loại khỏi phiên học của bạn',
            'total_blacklisted': 'Tổng số từ bị cấm',
            'filtered_results': 'Kết quả lọc',
            'selected': 'Đã chọn',
            'page': 'Trang',
            'search_words_decks': 'Tìm kiếm từ, bộ thẻ hoặc định nghĩa...',
            'select_all': 'Chọn tất cả',
            'clear': 'Xóa',
            'remove_selected': 'Xóa đã chọn',
            'select_page': 'Chọn trang',
            'word': 'Từ',
            'deck': 'Bộ thẻ',
            'blacklisted_at': 'Thời gian cấm',
            'actions': 'Hành động',
            'no_blacklisted_words_found': 'Không tìm thấy từ bị cấm',
            'no_blacklisted_words_message': 'Bạn chưa cấm từ nào, hoặc không có từ nào khớp với tìm kiếm hiện tại.',
            'start_studying': 'Bắt đầu học',
            'browse_decks': 'Duyệt bộ thẻ',
            'showing_words': 'Hiển thị {start}-{end} trong {total} từ',
            'items_per_page': 'Số mục mỗi trang:',
            'first_page': 'Trang đầu',
            'previous_page': 'Trang trước',
            'next_page': 'Trang sau',
            'last_page': 'Trang cuối',
            'go_to_page': 'Đi đến trang:',
            'go': 'Đi',
            'grid_view': 'Xem lưới',
            'table_view': 'Xem bảng',
            'confirm_removal': 'Xác nhận xóa',
            'cancel': 'Hủy',
            'remove_from_blacklist': 'Xóa khỏi danh sách đen',
            'loading_blacklisted_words': 'Đang tải từ bị cấm...',
            'searching_for': 'Tìm kiếm "{query}" - tìm thấy {count} kết quả',
            'words_selected': 'Đã chọn {count} từ',
            'all_words_selected': 'Đã chọn tất cả {count} từ',
            'successfully_removed_words': 'Đã xóa thành công {count} từ khỏi danh sách đen',
            'word_removed_from_blacklist': 'Đã xóa từ khỏi danh sách đen',
            'error_removing_word': 'Lỗi khi xóa từ: {error}',
            'error_removing_items': 'Lỗi khi xóa mục: {error}',
            'error_selecting_all_items': 'Lỗi khi chọn tất cả mục',
            'error_loading_blacklisted_words': 'Lỗi khi tải từ bị cấm. Vui lòng thử lại.',
            'removing': 'Đang xóa...',
        }
    }
    
    # Create a hybrid system that provides both legacy and Django i18n
    legacy_texts = legacy_translations.get(current_lang, legacy_translations['en'])

    # JavaScript translations using Django's gettext (fallback to English if translation fails)
    js_translations = {}
    try:
        js_translations = {
            'console_welcome': str(_("🎓 LearnEnglish App")),
            'console_subtitle': str(_("Welcome to the developer console!")),
            'console_built_with': str(_("Built with Django + Tailwind CSS + JavaScript ❤️")),
            'home': str(_("Home")),
            'flashcards': str(_("Flashcards")),
            'add_word': str(_("Add Word")),
            'study': str(_("Study")),
            'statistics': str(_("Statistics")),
            'profile': str(_("Profile")),
            'logout': str(_("Logout")),
            'correct': str(_("Correct")),
            'incorrect': str(_("Incorrect")),
            'check': str(_("Check")),
            'saving': str(_("Saving...")),
            'loading': str(_("Loading...")),
            'error': str(_("Error")),
            'success': str(_("Success")),
        }
    except Exception:
        # Fallback to legacy translations if Django i18n fails
        js_translations = {
            'console_welcome': legacy_texts.get('console_welcome', '🎓 LearnEnglish App'),
            'console_subtitle': legacy_texts.get('console_subtitle', 'Welcome to the developer console!'),
            'console_built_with': legacy_texts.get('console_built_with', 'Built with Django + Tailwind CSS + JavaScript ❤️'),
            'home': legacy_texts.get('home', 'Home'),
            'flashcards': legacy_texts.get('flashcards', 'Flashcards'),
            'add_word': legacy_texts.get('add_word', 'Add Word'),
            'study': legacy_texts.get('study', 'Study'),
            'statistics': legacy_texts.get('statistics', 'Statistics'),
            'profile': legacy_texts.get('profile', 'Profile'),
            'logout': legacy_texts.get('logout', 'Logout'),
            'correct': legacy_texts.get('correct', 'Correct'),
            'incorrect': legacy_texts.get('incorrect', 'Incorrect'),
            'check': legacy_texts.get('check', 'Check'),
            'saving': legacy_texts.get('saving', 'Saving...'),
            'loading': legacy_texts.get('loading', 'Loading...'),
            'error': legacy_texts.get('error', 'Error'),
            'success': legacy_texts.get('success', 'Success'),
        }

    # For templates that haven't been migrated yet, provide manual_texts
    # For new templates, they should use {% trans %} tags directly
    return {
        'manual_texts': legacy_texts,  # Legacy support
        'current_language_code': current_lang,
        'js_translations_json': json.dumps(js_translations),  # JSON string for JavaScript
    }

def manual_translations(request):
    """
    DEPRECATED: Use i18n_compatible_translations instead.
    This function is kept for backward compatibility only.
    """
    return i18n_compatible_translations(request)