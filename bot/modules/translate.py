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

COMMAND_TRANSLATIONS_CACHE = {}

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
        await sendMessage(message, "You're using the default language (English).\nNo command translations available.")
        return
    
    msg = f"<b>Available command translations for {TranslationManager.get_supported_languages()[lang_code]}:</b>\n\n"
    
    if lang_code in COMMAND_TRANSLATIONS_CACHE:
        await sendMessage(message, COMMAND_TRANSLATIONS_CACHE[lang_code])
        return
    
    for name, attr in inspect.getmembers(BotCommands):
        if not name.startswith('_') and isinstance(attr, (str, list)):
            commands = [attr] if isinstance(attr, str) else attr
            for cmd in commands:
                base_cmd = cmd
                if config_dict.get("CMD_SUFFIX") and cmd.endswith(config_dict["CMD_SUFFIX"]):
                    base_cmd = cmd[:-len(config_dict["CMD_SUFFIX"])]
                
                translated = TranslationManager.translate_command(base_cmd, lang_code)
                if translated and translated != base_cmd:
                    suffix = config_dict.get("CMD_SUFFIX", "")
                    msg += f"/{base_cmd}{suffix} → /{translated}{suffix}\n"
    
    COMMAND_TRANSLATIONS_CACHE[lang_code] = msg
    await sendMessage(message, msg)

async def batch_translate_commands(commands, lang_code):
    translations = {}
    for cmd in commands:
        translated = TranslationManager.translate_command(cmd, lang_code)
        translations[cmd] = translated
    return translations

async def register_command_translations(client):
    LOGGER.info("Starting to register translated commands for all languages...")
    
    command_handlers = {}
    all_commands = []
    
    for name, attr in inspect.getmembers(BotCommands):
        if not name.startswith('_') and isinstance(attr, (str, list)):
            commands = [attr] if isinstance(attr, str) else attr
            for cmd in commands:
                base_cmd = cmd
                if config_dict.get("CMD_SUFFIX") and cmd.endswith(config_dict["CMD_SUFFIX"]):
                    base_cmd = cmd[:-len(config_dict["CMD_SUFFIX"])]
                all_commands.append(base_cmd)
    
    try:
        for group_id in client.dispatcher.groups:
            for handler in client.dispatcher.groups[group_id]:
                if isinstance(handler, MessageHandler) and hasattr(handler, 'filters'):
                    if hasattr(handler.filters, 'commands') and handler.filters.commands:
                        for cmd in handler.filters.commands:
                            base_cmd = cmd
                            if config_dict.get("CMD_SUFFIX") and cmd.endswith(config_dict["CMD_SUFFIX"]):
                                base_cmd = cmd[:-len(config_dict["CMD_SUFFIX"])]
                            command_handlers[base_cmd] = handler.callback
    except Exception as e:
        LOGGER.error(f"Error accessing handlers: {e}")
    
    registered_commands = set()
    
    tasks = []
    for lang_code in TranslationManager.get_supported_languages():
        if lang_code == 'en': 
            continue
        
        LOGGER.info(f"Registering command translations for language: {lang_code}")
        
        translations = await batch_translate_commands(all_commands, lang_code)
        
        for base_cmd, translated in translations.items():
            if translated != base_cmd:
                if config_dict.get("CMD_SUFFIX"):
                    translated_cmd = f"{translated}{config_dict['CMD_SUFFIX']}"
                else:
                    translated_cmd = translated
                
                if translated_cmd in registered_commands:
                    continue
                
                if base_cmd in command_handlers:
                    try:
                        handler_func = command_handlers[base_cmd]
                        client.add_handler(
                            MessageHandler(
                                handler_func,
                                filters=command(
                                    translated_cmd
                                ) & CustomFilters.authorized
                            )
                        )
                        registered_commands.add(translated_cmd)
                        LOGGER.info(f"Registered translated command: /{translated_cmd} → /{base_cmd}")
                    except Exception as e:
                        LOGGER.error(f"Error registering translated command {translated_cmd}: {e}")

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

# Ubah cara run task untuk registrasi command agar tidak memblokir
def start_registration():
    asyncio.create_task(register_command_translations(bot))

# Gunakan method yang lebih efisien untuk menjalankan task
bot_loop.call_soon_threadsafe(start_registration)