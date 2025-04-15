from bot import bot, DATABASE_URL, user_data, config_dict, LOGGER, bot_loop
import inspect

from bot.helper.telegram_helper.message_utils import (
    sendMessage,
    editMessage
)
from bot.helper.ext_utils.bot_utils import update_user_ldata
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.translator import TranslationManager, register_command_translations
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

async def list_commands_handler(client, message):
    user_id = message.from_user.id
    lang_code = TranslationManager.get_user_language(user_id)
    
    if lang_code == 'en':
        await sendMessage(message, "You're using the default English language.\nNo command translations available.")
        return
    
    msg = f"<b>Available command translations for {TranslationManager.get_supported_languages()[lang_code]}:</b>\n\n"
    
    for name, attr in inspect.getmembers(BotCommands):
        if not name.startswith('_') and isinstance(attr, (str, list)):
            commands = [attr] if isinstance(attr, str) else attr
            for cmd in commands:
                if config_dict.get("CMD_SUFFIX"):
                    base_cmd = cmd.split(config_dict["CMD_SUFFIX"])[0]
                else:
                    base_cmd = cmd
                
                translated = TranslationManager.translate_command(base_cmd, lang_code)
                if translated and translated != base_cmd:
                    suffix = config_dict.get("CMD_SUFFIX", "")
                    msg += f"/{base_cmd}{suffix} → /{translated}{suffix}\n"
    
    await sendMessage(message, msg)

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

bot.add_handler(
    MessageHandler(
        list_commands_handler,
        filters=command(
            "commands"
        ) & CustomFilters.authorized
    )
)

bot_loop.create_task(
    register_command_translations(
        bot
    )
)