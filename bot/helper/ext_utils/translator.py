from deep_translator import GoogleTranslator
from langdetect import detect
from bot import user_data, config_dict, LOGGER
import re

SUPPORTED_LANGUAGES = {
    'en': 'English',
    'id': 'Indonesia',
    'tl': 'Filipino/Tagalog',
    'es': 'Español',
    'fr': 'Français',
    'de': 'Deutsch',
    'it': 'Italiano',
    'ja': '日本語',
    'ko': '한국어',
    'pt': 'Português',
    'ru': 'Русский',
    'zh-cn': '简体中文',
    'ar': 'العربية',
    'hi': 'हिन्दी',
    'tr': 'Türkçe',
    'vi': 'Tiếng Việt',
    'th': 'ไทย',
    'ms': 'Melayu',
}

DEFAULT_LANGUAGE = config_dict.get('DEFAULT_LANGUAGE', 'en')

class TranslationManager:
    @staticmethod
    def get_user_language(user_id=None):
        if user_id and user_id in user_data:
            return user_data[user_id].get('language', DEFAULT_LANGUAGE)
        return DEFAULT_LANGUAGE
    
    @staticmethod
    def set_user_language(user_id, language):
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['language'] = language
        
    @staticmethod
    def translate_text(text, target_lang=None, user_id=None):
        if not text or not isinstance(text, str):
            return text
        
        if len(text) <= 2 and not text.isalpha():
            return text
            
        html_entities = {}
        count = 0
        
        def replace_tag(match):
            nonlocal count
            placeholder = f"__HTML_TAG_{count}__"
            html_entities[placeholder] = match.group(0)
            count += 1
            return placeholder
            
        text_without_html = re.sub(r'<.*?>', replace_tag, text)
        
        if target_lang is None:
            target_lang = TranslationManager.get_user_language(user_id)
            
        try:
            detected_lang = detect(text_without_html)
            if detected_lang == target_lang:
                return text
        except:
            pass
            
        try:
            translator = GoogleTranslator(source='auto', target=target_lang)
            translated_text = translator.translate(text_without_html)
            
            for placeholder, tag in html_entities.items():
                translated_text = translated_text.replace(placeholder, tag)
                
            return translated_text
        except Exception as e:
            LOGGER.error(f"Translation error: {e}")
            return text
            
    @staticmethod
    def get_supported_languages():
        return SUPPORTED_LANGUAGES