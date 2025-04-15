from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.helper.ext_utils.translator import TranslationManager

class ButtonMaker:
    def __init__(self, user_id=None):
        self._button = []
        self._header_button = []
        self._footer_button = []
        self.user_id = user_id

    def _translate_text(self, text):
        if self.user_id is None:
            return text
        
        try:
            translated = TranslationManager.translate_button_text(text, user_id=self.user_id)
            return translated if translated else text
        except Exception:
            return text

    def ubutton(self, key, link, position=None):
        translated_key = self._translate_text(key)
        if not position:
            self._button.append(InlineKeyboardButton(text=translated_key, url=link))
        elif position == "header":
            self._header_button.append(InlineKeyboardButton(text=translated_key, url=link))
        elif position == "footer":
            self._footer_button.append(InlineKeyboardButton(text=translated_key, url=link))

    def ibutton(self, key, data, position=None):
        translated_key = self._translate_text(key)
        if not position:
            self._button.append(InlineKeyboardButton(text=translated_key, callback_data=data))
        elif position == "header":
            self._header_button.append(
                InlineKeyboardButton(text=translated_key, callback_data=data)
            )
        elif position == "footer":
            self._footer_button.append(
                InlineKeyboardButton(text=translated_key, callback_data=data)
            )

    def build_menu(self, b_cols=1, h_cols=8, f_cols=8):
        menu = [
            self._button[i : i + b_cols] for i in range(0, len(self._button), b_cols)
        ]
        if self._header_button:
            h_cnt = len(self._header_button)
            if h_cnt > h_cols:
                header_buttons = [
                    self._header_button[i : i + h_cols]
                    for i in range(0, len(self._header_button), h_cols)
                ]
                menu = header_buttons + menu
            else:
                menu.insert(0, self._header_button)
        if self._footer_button:
            if len(self._footer_button) > f_cols:
                [
                    menu.append(self._footer_button[i : i + f_cols])
                    for i in range(0, len(self._footer_button), f_cols)
                ]
            else:
                menu.append(self._footer_button)
        return InlineKeyboardMarkup(menu)

    def reset(self):
        self._button = []
        self._header_button = []
        self._footer_button = []