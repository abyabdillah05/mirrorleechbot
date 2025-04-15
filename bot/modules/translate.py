import asyncio
from bot import bot, DATABASE_URL, user_data, config_dict, LOGGER, bot_loop
import inspect

from bot.helper.telegram_helper.message_utils import (
    sendMessage,
    editMessage
)
from bot.helper.ext_utils.bot_utils import update_user_ldata
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.translator import TranslationManager
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.ext_utils.db_handler import DbManger
from pyrogram.filters import command, regex
from pyrogram.handlers import MessageHandler, CallbackQueryHandler

async def language_handler(client, message):
    args = message.text.split()
    user_id = message.from_user.id
    
    if len(args) > 1:
        lang_code = args[1].lower()
        if lang_code in TranslationManager.get_supported_languages():
            TranslationManager.set_user_language(user_id, lang_code)
            update_user_ldata(user_id, "language", lang_code)
            if DATABASE_URL:
                await DbManger().update_user_data(user_id)
            
            lang_name = TranslationManager.get_supported_languages()[lang_code]
            confirm_msg = f"Language has been set to {lang_name}"
            translated_msg = TranslationManager.translate_text(confirm_msg, target_lang=lang_code)
            await sendMessage(message, translated_msg)
        else:
            langs = "\n".join([f"{code}: {name}" for code, name in TranslationManager.get_supported_languages().items()])
            await sendMessage(message, f"Invalid language code. Available languages:\n\n{langs}")
    else:
        buttons = ButtonMaker(user_id) 
        supported_langs = TranslationManager.get_supported_languages()
        current_lang = user_data.get(user_id, {}).get("language", config_dict.get("DEFAULT_LANGUAGE", "en"))
        
        for lang_code, lang_name in supported_langs.items():
            check = "✅ " if current_lang == lang_code else ""
            buttons.ibutton(f"{check}{lang_name}", f"lang {lang_code}")
        
        buttons.ibutton("Cancel", "lang cancel")
        
        await sendMessage(
            message,
            "Select your preferred language / Pilih bahasa yang Anda inginkan:",
            buttons.build_menu(2)
        )

async def language_callback(client, callback_query):
    data = callback_query.data.split()
    user_id = callback_query.from_user.id
    message = callback_query.message
    
    if data[1] == "cancel":
        await editMessage(message, "Language selection canceled.")
        return
    
    lang_code = data[1]
    if lang_code in TranslationManager.get_supported_languages():
        TranslationManager.set_user_language(user_id, lang_code)
        update_user_ldata(user_id, "language", lang_code)
        if DATABASE_URL:
            await DbManger().update_user_data(user_id)
        
        lang_name = TranslationManager.get_supported_languages()[lang_code]
        confirm_msg = f"Language has been set to {lang_name}"
        translated_msg = TranslationManager.translate_text(confirm_msg, target_lang=lang_code)
        
        await editMessage(message, translated_msg)
    else:
        await editMessage(message, "Invalid language selection.")

bot.add_handler(
    MessageHandler(
        language_handler,
        filters=command(
            BotCommands.LanguageCommand
        ) & CustomFilters.authorized
    )
)

bot.add_handler(
    CallbackQueryHandler(
        language_callback,
        filters=regex(
            "^lang"
        )
    )
)