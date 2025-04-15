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
        
        if len(text.strip()) < 3:
            return text
        
        if target_lang is None:
            target_lang = TranslationManager.get_user_language(user_id)
        
        if not target_lang or target_lang not in SUPPORTED_LANGUAGES or target_lang == 'en':
            return text
                
        cache_key = f"txt_{text[:100]}_{target_lang}"
        if cache_key in TEXT_CACHE:
            return TEXT_CACHE[cache_key]
                
        try:
            html_placeholders = {}
            counter = 0
            
            patterns = [
                (r'<b>.*?</b>', 'bold_tag'),
                (r'<i>.*?</i>', 'italic_tag'),
                (r'<code>.*?</code>', 'code_tag'),
                (r'<pre.*?>.*?</pre>', 'pre_tag'),
                (r'<a href=.*?</a>', 'url_tag'),
                (r'<u>.*?</u>', 'underline_tag'),
                (r'<s>.*?</s>', 'strikethrough_tag'),
                (r'<blockquote>.*?</blockquote>', 'quote_tag'),
                (r'<spoiler>.*?</spoiler>', 'spoiler_tag'),
            ]
            
            protected_text = text
            
            for pattern, tag_type in patterns:
                def replace_tag(match):
                    nonlocal counter
                    placeholder = f"__PROTECTED_TAG_{counter}__"
                    html_placeholders[placeholder] = match.group(0)
                    counter += 1
                    return placeholder
                    
                protected_text = re.sub(pattern, replace_tag, protected_text, flags=re.DOTALL)
            
            def protect_standalone_tag(match):
                nonlocal counter
                placeholder = f"__PROTECTED_TAG_{counter}__"
                html_placeholders[placeholder] = match.group(0)
                counter += 1
                return placeholder
                
            protected_text = re.sub(r'<[^<>]+?>', protect_standalone_tag, protected_text)
            
            if not protected_text.strip() or all(x in html_placeholders for x in protected_text.split()):
                return text
            
            try:
                detected_lang = detect(protected_text.strip())
                if detected_lang == target_lang:
                    return text
            except:
                pass
                
            translator = GoogleTranslator(source='auto', target=target_lang)
            translated_text = translator.translate(protected_text)
            
            if not translated_text:
                return text
                
            for placeholder, original in sorted(html_placeholders.items(), key=lambda x: len(x[0]), reverse=True):
                translated_text = translated_text.replace(placeholder, original)
                
            TEXT_CACHE[cache_key] = translated_text
            
            return translated_text
        except Exception as e:
            LOGGER.error(f"Text translation error: {e}")
            return text
    
    @staticmethod
    def get_supported_languages():
        return SUPPORTED_LANGUAGES