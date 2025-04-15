from deep_translator import GoogleTranslator
from langdetect import detect
from bot import user_data, config_dict, LOGGER, bot_loop
from bot.helper.telegram_helper.bot_commands import BotCommands
import re
import inspect
from pyrogram.handlers import MessageHandler
from pyrogram.filters import command
import asyncio
from time import time

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

COMMAND_CACHE = {}
TEXT_CACHE = {}
REGISTERED_COMMANDS = set()

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
    def translate_command(command, target_lang=None, user_id=None):
        if not command:
            return command
            
        if target_lang is None:
            target_lang = TranslationManager.get_user_language(user_id)
            
        if target_lang == 'en' or target_lang not in SUPPORTED_LANGUAGES:
            return command
        
        cache_key = f"cmd_{command}_{target_lang}"
        if cache_key in COMMAND_CACHE:
            return COMMAND_CACHE[cache_key]
            
        try:
            translator = GoogleTranslator(source='en', target=target_lang)
            translated = translator.translate(command)
            
            if not translated:
                return command
                
            cleaned = ''.join(c for c in translated if c.isalnum() or c == '_').lower()
            
            if not cleaned:
                return command
                
            COMMAND_CACHE[cache_key] = cleaned
            return cleaned
        except Exception as e:
            LOGGER.error(f"Command translation error: {e}")
            return command
    
    @staticmethod
    def translate_button_text(text, target_lang=None, user_id=None):
        if not text or not isinstance(text, str) or len(text) < 3:
            return text
            
        if target_lang is None:
            target_lang = TranslationManager.get_user_language(user_id)
            
        if target_lang == 'en' or target_lang not in SUPPORTED_LANGUAGES:
            return text
        
        prefix_match = re.match(r'^([✓✅❌☑️⬇️➕🔄◽️▫️📁📂🗂️📊📈📉🔍🔎🔑🔒🔓♻️⚠️⛔️✴️❇️💠🔰⭕️✅❌➰➿〰️💲💱©®™🔴🟠🟡🟢🔵🟣⚫️⚪️🟤🔘🔸🔹🔶🔷🔺🔻💠🔆]\s*)', text)
        prefix = prefix_match.group(1) if prefix_match else ""
        
        if prefix:
            main_text = text[len(prefix):]
        else:
            main_text = text
            
        suffix_match = re.search(r'([:\-→⟶⇒⇨⇾➡️➤▶️★☆⭐️✨🌟✯✰\s]+)$', main_text)
        suffix = suffix_match.group(1) if suffix_match else ""
        
        if suffix:
            main_text = main_text[:-len(suffix)]
        
        if main_text.strip():
            try:
                cache_key = f"btn_{main_text}_{target_lang}"
                if cache_key in TEXT_CACHE:
                    translated_main = TEXT_CACHE[cache_key]
                else:
                    translator = GoogleTranslator(source='auto', target=target_lang)
                    translated_main = translator.translate(main_text.strip())
                    TEXT_CACHE[cache_key] = translated_main
                
                if translated_main:
                    return f"{prefix}{translated_main}{suffix}"
            except Exception as e:
                LOGGER.error(f"Button translation error: {e}")
                
        return text
    
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
            placeholder = f"<HTMLTAG{count}>"
            html_entities[placeholder] = match.group(0)
            count += 1
            return placeholder
            
        text_without_html = re.sub(r'<[^<>]*?>', replace_tag, text)
        
        if target_lang is None:
            target_lang = TranslationManager.get_user_language(user_id)
        
        if not target_lang or target_lang not in SUPPORTED_LANGUAGES:
            target_lang = DEFAULT_LANGUAGE
            if not DEFAULT_LANGUAGE or DEFAULT_LANGUAGE not in SUPPORTED_LANGUAGES:
                return text 
        
        if not text_without_html.strip():
            return text
        
        try:
            try:
                detected_lang = detect(text_without_html)
                if detected_lang == target_lang:
                    return text
            except Exception as e:
                LOGGER.error(f"Language detection error: {e}")
        
            try:
                translator = GoogleTranslator(source='auto', target=target_lang)
                translated_text = translator.translate(text_without_html)
                
                if not translated_text:
                    return text
                
                for placeholder, tag in html_entities.items():
                    if placeholder in translated_text:
                        translated_text = translated_text.replace(placeholder, tag)
                    else:
                        translated_text += tag
                        
                return translated_text
            except Exception as e:
                LOGGER.error(f"Translation error: {e} --> Invalid source or target language!")
                return text
        except Exception as e:
            LOGGER.error(f"General translation error: {e}")
            return text
    
    @staticmethod
    def get_supported_languages():
        return SUPPORTED_LANGUAGES