from pyrogram.filters import create

from bot import user_data, OWNER_ID


class CustomFilters:

    async def owner_filter(self, _, update):
        user = update.from_user or update.sender_chat
        user_id = user.id
        return user_id == OWNER_ID

    owner = create(owner_filter)

    async def sudo_user(self, _, update):
        user = (
            update.from_user
            or update.sender_chat
        )
        user_id = user.id
        
        return bool(
            user_id == OWNER_ID
            or user_id in user_data
            and user_data[user_id].get("is_sudo")
        )

    sudo = create(sudo_user)

    async def authorized_user(self, _, update):
        user = (
            update.from_user
            or update.sender_chat
        )
        try:
            user_id = user.id
        except AttributeError:
            return False
        chat_id = update.chat.id
        thread_id = update.message_thread_id
        return bool(
            user_id == OWNER_ID
            or (
                user_id in user_data
                and (
                    user_data[user_id].get("is_auth", False)
                    or user_data[user_id].get("is_sudo", False)
                )
            )
            or (
                    (
                        chat_id in user_data
                        and user_data[chat_id].get("is_auth", False)
                    ) and thread_id == user_data[chat_id].get("thread_id")
                if update.chat.is_forum
                else (
                    chat_id in user_data
                    and user_data[chat_id].get("is_auth", False)
                )
            )
        )
    
    authorized = create(authorized_user)