import random
import requests
import os
import tempfile
import time
import aiohttp
from io import BytesIO
from datetime import datetime
from PIL import Image

###############################
## Import Libraries Pyrogram ##
###############################

from pyrogram.enums import ChatType
from pyrogram.filters import (command,
                              regex)
from pyrogram.handlers import MessageHandler
from pyrogram.handlers import CallbackQueryHandler

##################################
## Import Variable From Project ##
##################################

from bot import (bot,
                 LOGGER,
                 DOWNLOAD_DIR)
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import (sendMessage,
                                                      editMessage)
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.safelinku_utils import SafeLinkU
from bot.helper.ext_utils.bot_utils import new_thread

#########################
## Api Anime Image URL ##
#########################

## Modified by Tg @WzdDizzyFlasherr ##
## You can add/remove/edit all APIs here ##

# 10 Different Anime Image APIs
ANIME_APIS = [
    # 1. WAIFU.PICS - Good reliable API with SFW and NSFW
    {
        "name": "Waifu.pics",
        "sfw_url": "https://api.waifu.pics/sfw/{tag}",
        "nsfw_url": "https://api.waifu.pics/nsfw/{tag}",
        "sfw_tags": ["waifu", "neko", "shinobu", "megumin", "bully", "cuddle", "cry", "hug", "awoo", "kiss", "lick", "pat", "smug", "bonk", "yeet", "blush", "smile", "wave", "highfive", "handhold", "nom", "bite", "glomp", "slap", "kill", "kick", "happy", "wink", "poke", "dance", "cringe"],
        "nsfw_tags": ["waifu", "neko", "trap", "blowjob"],
        "parse": lambda r: r.json()["url"] if r.status_code == 200 and "url" in r.json() else None
    },
    
    # 2. NEKOS.LIFE - Another good API for anime images
    {
        "name": "Nekos.life",
        "sfw_url": "https://nekos.life/api/v2/img/{tag}",
        "nsfw_url": "https://nekos.life/api/v2/img/{tag}",
        "sfw_tags": ["neko", "ngif", "smile", "waifu", "cuddle", "feed", "fox_girl", "lizard", "pat", "poke", "slap", "tickle"],
        "nsfw_tags": ["lewd", "ero", "blowjob", "tits", "boobs", "trap", "pussy", "cum", "hentai"],
        "parse": lambda r: r.json()["url"] if r.status_code == 200 and "url" in r.json() else None
    },
    
    # 3. WAIFU.IM - Great for higher quality anime images
    {
        "name": "Waifu.im",
        "sfw_url": "https://api.waifu.im/search?included_tags={tag}",
        "nsfw_url": "https://api.waifu.im/search?included_tags={tag}",
        "sfw_tags": ["maid", "waifu", "marin-kitagawa", "mori-calliope", "raiden-shogun", "oppai", "selfies", "uniform", "kamisato-ayaka"],
        "nsfw_tags": ["ass", "hentai", "milf", "oral", "paizuri", "ecchi", "ero"],
        "parse": lambda r: r.json()["images"][0]["url"] if r.status_code == 200 and "images" in r.json() and r.json()["images"] else None
    },
    
    # 4. NEKOBOT API - Popular anime image API with lots of NSFW
    {
        "name": "Nekobot",
        "sfw_url": "https://nekobot.xyz/api/image?type={tag}",
        "nsfw_url": "https://nekobot.xyz/api/image?type={tag}",
        "sfw_tags": ["neko", "kitsune", "waifu", "coffee"],
        "nsfw_tags": ["hentai", "ass", "boobs", "paizuri", "thigh", "hthigh", "anal", "hanal", "gonewild", "pgif", "4k", "lewdneko", "pussy", "holo", "lewdkitsune", "kemonomimi", "feet", "hfeet", "blowjob", "hmidriff", "hboobs", "tentacle"],
        "parse": lambda r: r.json()["message"] if r.status_code == 200 and "message" in r.json() else None
    },
    
    # 5. HMTAI API - Hentai/anime image API with tons of NSFW
    {
        "name": "HMTAI",
        "sfw_url": "https://hmtai.hatsunia.cfd/v2/sfw/{tag}",
        "nsfw_url": "https://hmtai.hatsunia.cfd/v2/nsfw/{tag}",
        "sfw_tags": ["wallpaper", "mobileWallpaper", "neko", "jahy", "slap", "lick", "depression"],
        "nsfw_tags": ["ass", "bdsm", "cum", "creampie", "manga", "femdom", "hentai", "incest", "masturbation", "public", "ero", "orgy", "elves", "yuri", "pantsu", "glasses", "cuckold", "blowjob", "boobjob", "foot", "thighs", "vagina", "ahegao", "uniform", "gangbang", "tentacles", "gif", "neko", "nsfwMobileWallpaper", "zettaiRyouiki"],
        "parse": lambda r: r.json() if r.status_code == 200 else None
    },
    
    # 6. WAIFU API
    {
        "name": "Waifu API",
        "sfw_url": "https://api.waifu.lu/v1/sfw/{tag}",
        "nsfw_url": "https://api.waifu.lu/v1/nsfw/{tag}",
        "sfw_tags": ["waifu", "neko", "uniform"],
        "nsfw_tags": ["waifu", "neko", "trap", "maid"],
        "parse": lambda r: r.json()["url"] if r.status_code == 200 and "url" in r.json() else None
    },
    
    # 7. ANIME-IMAGES-API - Another anime API
    {
        "name": "Anime Images",
        "sfw_url": "https://anime-api.hisoka17.repl.co/img/sfw/{tag}",
        "nsfw_url": "https://anime-api.hisoka17.repl.co/img/nsfw/{tag}",
        "sfw_tags": ["hug", "kiss", "slap", "wink", "pat", "kill", "cuddle", "punch", "waifu"],
        "nsfw_tags": ["hentai", "boobs", "lesbian"],
        "parse": lambda r: r.json()["url"] if r.status_code == 200 and "url" in r.json() else None
    },
    
    # 8. PICREW API - Better anime image API
    {
        "name": "Picrew API",
        "sfw_url": "https://api.waifu.pics/sfw/{tag}",
        "nsfw_url": "https://api.waifu.pics/nsfw/{tag}",
        "sfw_tags": ["waifu", "neko", "shinobu", "megumin", "bully", "cuddle", "cry", "hug", "awoo", "kiss", "lick", "pat", "smug", "bonk", "yeet", "blush", "smile", "wave", "highfive", "handhold", "nom", "bite", "glomp", "slap", "kill", "kick", "happy", "wink", "poke", "dance", "cringe"],
        "nsfw_tags": ["waifu", "neko", "trap", "blowjob"],
        "parse": lambda r: r.json()["url"] if r.status_code == 200 and "url" in r.json() else None
    },
    
    # 9. NEKOS.FUN - Anime API
    {
        "name": "Nekos Fun",
        "sfw_url": "https://api.nekos.fun/api/{tag}",
        "nsfw_url": "https://api.nekos.fun/api/{tag}",
        "sfw_tags": ["kiss", "lick", "hug", "baka", "cry", "poke", "smug", "slap", "tickle", "pat", "laugh", "feed", "cuddle"],
        "nsfw_tags": ["lesbian", "anal", "bj", "classic", "cum", "spank"],
        "parse": lambda r: r.json()["image"] if r.status_code == 200 and "image" in r.json() else None
    },
    
    # 10. ANIME-NEKO-API
    {
        "name": "Anime Neko",
        "sfw_url": "https://img-api.lioncube.fr/{tag}",
        "nsfw_url": "https://img-api.lioncube.fr/{tag}",
        "sfw_tags": ["neko", "kitsune", "waifu"],
        "nsfw_tags": ["hentai", "trap"],
        "parse": lambda r: r.json()["url"] if r.status_code == 200 and "url" in r.json() else None
    }
]

##########################################
## Another Tags By Tg @WzdDizzyFlasherr ##
##########################################

## You can add/remove/edit all tags here ##

# SFW Tags organized by categories
SFW_TAGS = {
    # Generic Character Types
    "waifu": "Anime Wife Character",
    "neko": "Cat Girl Character",
    "kitsune": "Fox Girl Character",
    "fox_girl": "Fox Girl Character",
    "cat-girl": "Cat Girls",
    "husbando": "Male Anime Character",
    "maid": "Maid Character",
    "jahy": "Jahy Character",
    
    # Popular Anime Characters
    "megumin": "Konosuba Character",
    "shinobu": "Demon Slayer Character",
    "rem": "Rem (Re:Zero)",
    "zero-two": "Zero Two (Darling in the Franxx)",
    "hatsune-miku": "Hatsune Miku (Vocaloid)",
    "asuna": "Asuna Yuuki (SAO)",
    "mikasa": "Mikasa Ackerman (AoT)",
    "esdeath": "Esdeath (Akame ga Kill)",
    "albedo": "Albedo (Overlord)",
    "mai-sakurajima": "Mai Sakurajima (Bunny Girl Senpai)",
    "power": "Power (Chainsaw Man)",
    "makima": "Makima (Chainsaw Man)",
    "yor": "Yor Forger (Spy x Family)",
    "hinata": "Hinata Hyuga (Naruto)",
    "nezuko": "Nezuko Kamado (Demon Slayer)",
    "aqua": "Aqua (Konosuba)",
    "darkness": "Darkness (Konosuba)",
    "emilia": "Emilia (Re:Zero)",
    "ai-hoshino": "Ai Hoshino (Oshi no Ko)",
    "rias": "Rias Gremory (High School DxD)",
    "chizuru": "Chizuru Mizuhara (Rent-a-Girlfriend)",
    "alice": "Alice Zuberg (SAO Alicization)",
    "misaka": "Misaka Mikoto (Railgun)",
    "miku": "Miku Nakano (Quintessential Quintuplets)",
    "nino": "Nino Nakano (Quintessential Quintuplets)",
    "ichika": "Ichika Nakano (Quintessential Quintuplets)",
    "yotsuba": "Yotsuba Nakano (Quintessential Quintuplets)",
    "itsuki": "Itsuki Nakano (Quintessential Quintuplets)",
    "nagatoro": "Nagatoro (Don't Toy With Me)",
    "komi": "Komi-san (Komi Can't Communicate)",
    "chika": "Chika Fujiwara (Kaguya-sama)",
    "kaguya": "Kaguya Shinomiya (Kaguya-sama)",
    "violet": "Violet Evergarden",
    "toga": "Himiko Toga (My Hero Academia)",
    "hori": "Kyoko Hori (Horimiya)",
    "tsunade": "Tsunade (Naruto)",
    "sakura": "Sakura Haruno (Naruto)",
    "marin-kitagawa": "Marin Kitagawa (My Dress-Up Darling)",
    "urushi": "Urushi Yaotome (Soredemo Ayumu)",
    "roxy": "Roxy Migurdia (Mushoku Tensei)",
    "eris": "Eris Boreas Greyrat (Mushoku Tensei)",
    "sylphiette": "Sylphiette (Mushoku Tensei)",
    
    # Male Anime Characters
    "eren": "Eren Yeager (AoT)",
    "levi": "Levi Ackerman (AoT)",
    "kirito": "Kirito (SAO)",
    "yuji": "Yuji Itadori (Jujutsu Kaisen)",
    "gojo": "Satoru Gojo (Jujutsu Kaisen)",
    "tanjiro": "Tanjiro Kamado (Demon Slayer)",
    "zenitsu": "Zenitsu Agatsuma (Demon Slayer)",
    "inosuke": "Inosuke Hashibira (Demon Slayer)",
    "todoroki": "Shoto Todoroki (My Hero Academia)",
    "bakugo": "Katsuki Bakugo (My Hero Academia)",
    "deku": "Izuku Midoriya (My Hero Academia)",
    "kakashi": "Kakashi Hatake (Naruto)",
    "naruto": "Naruto Uzumaki",
    "sasuke": "Sasuke Uchiha (Naruto)",
    "itachi": "Itachi Uchiha (Naruto)",
    "miyamura": "Izumi Miyamura (Horimiya)",
    "denji": "Denji (Chainsaw Man)",
    "aki": "Aki Hayakawa (Chainsaw Man)",
    "loid": "Loid Forger (Spy x Family)",
    "light": "Light Yagami (Death Note)",
    "L": "L Lawliet (Death Note)",
    "luffy": "Monkey D. Luffy (One Piece)",
    "zoro": "Roronoa Zoro (One Piece)",
    "sanji": "Sanji (One Piece)",
    "goku": "Son Goku (Dragon Ball)",
    "vegeta": "Vegeta (Dragon Ball)",
    
    # Genshin Impact Characters
    "raiden-shogun": "Raiden Shogun (Genshin)",
    "kamisato-ayaka": "Ayaka (Genshin)",
    "genshin-impact": "Genshin Impact",
    "hutao": "Hu Tao (Genshin)",
    "ganyu": "Ganyu (Genshin)",
    "keqing": "Keqing (Genshin)",
    "mona": "Mona (Genshin)",
    "eula": "Eula (Genshin)",
    "fischl": "Fischl (Genshin)",
    "jean": "Jean (Genshin)",
    "barbara": "Barbara (Genshin)",
    "yae-miko": "Yae Miko (Genshin)",
    "shenhe": "Shenhe (Genshin)",
    "nahida": "Nahida (Genshin)",
    "nilou": "Nilou (Genshin)",
    "yelan": "Yelan (Genshin)",
    "furina": "Furina (Genshin)",
    "ningguang": "Ningguang (Genshin)",
    "beidou": "Beidou (Genshin)",
    "venti": "Venti (Genshin)",
    "zhongli": "Zhongli (Genshin)",
    "childe": "Tartaglia/Childe (Genshin)",
    "xiao": "Xiao (Genshin)",
    "kazuha": "Kaedehara Kazuha (Genshin)",
    "alhaitham": "Alhaitham (Genshin)",
    "diluc": "Diluc (Genshin)",
    
    # Honkai Characters
    "raiden-mei": "Raiden Mei (Honkai)",
    "kiana": "Kiana Kaslana (Honkai)",
    "bronya": "Bronya Zaychik (Honkai)",
    "seele": "Seele Vollerei (Honkai)",
    "durandal": "Durandal (Honkai)",
    "fu-hua": "Fu Hua (Honkai)",
    "elysia": "Elysia (Honkai)",
    "mobius": "Mobius (Honkai)",
    "aponia": "Aponia (Honkai)",
    "eden": "Eden (Honkai)",
    "griseo": "Griseo (Honkai)",
    "pardofelis": "Pardofelis (Honkai)",
    "vill-v": "Vill-V (Honkai)",
    
    # Honkai Star Rail Characters
    "kafka": "Kafka (Star Rail)",
    "silver-wolf": "Silver Wolf (Star Rail)",
    "seele-sr": "Seele (Star Rail)",
    "bronya-sr": "Bronya (Star Rail)",
    "himeko": "Himeko (Star Rail)",
    "clara": "Clara (Star Rail)",
    "luocha": "Luocha (Star Rail)",
    "jing-yuan": "Jing Yuan (Star Rail)",
    "sushang": "Sushang (Star Rail)",
    "dan-heng": "Dan Heng (Star Rail)",
    "blade": "Blade (Star Rail)",
    "gepard": "Gepard (Star Rail)",
    "yanqing": "Yanqing (Star Rail)",
    "pela": "Pela (Star Rail)",
    "topaz": "Topaz (Star Rail)",
    
    # VTubers
    "mori-calliope": "Mori Calliope (Hololive)",
    "hololive": "Hololive VTubers",
    "vtuber": "Virtual YouTubers",
    "gura": "Gawr Gura (Hololive)",
    "amelia": "Amelia Watson (Hololive)",
    "ina": "Ninomae Ina'nis (Hololive)",
    "kiara": "Takanashi Kiara (Hololive)",
    "korone": "Inugami Korone (Hololive)",
    "fubuki": "Shirakami Fubuki (Hololive)",
    "pekora": "Usada Pekora (Hololive)",
    "marine": "Houshou Marine (Hololive)",
    "suisei": "Hoshimachi Suisei (Hololive)",
    "kronii": "Ouro Kronii (Hololive)",
    "mumei": "Nanashi Mumei (Hololive)",
    "bae": "Hakos Baelz (Hololive)",
    "sana": "Tsukumo Sana (Hololive)",
    "fauna": "Ceres Fauna (Hololive)",
    "irys": "IRyS (Hololive)",
    "ollie": "Kureiji Ollie (Hololive)",
    "moona": "Moona Hoshinova (Hololive)",
    "iofi": "Airani Iofifteen (Hololive)",
    "anya": "Anya Melfissa (Hololive)",
    "reine": "Pavolia Reine (Hololive)",
    "koyori": "Hakui Koyori (Hololive)",
    "lui": "Takane Lui (Hololive)",
    "laplus": "La+ Darknesss (Hololive)",
    "chloe": "Sakamata Chloe (Hololive)",
    "iroha": "Kazama Iroha (Hololive)",
    "kizuna-ai": "Kizuna AI",
    "ironmouse": "Ironmouse (VShojo)",
    "veibae": "Veibae (VShojo)",
    "zentreya": "Zentreya (VShojo)",
    "silvervale": "Silvervale (VShojo)",
    "nyanners": "Nyanners (VShojo)",
    
    # Expressions & Emotions
    "smile": "Smiling Anime",
    "happy": "Happy Anime",
    "laugh": "Laughing Anime",
    "cry": "Crying Anime",
    "blush": "Blushing Anime",
    "pout": "Pouting Anime",
    "smug": "Smug Anime",
    "bored": "Bored Anime",
    "depression": "Sad/Depressing",
    "facepalm": "Facepalm",
    "baka": "Baka/Idiot",
    "cringe": "Cringing",
    "think": "Thinking",
    "thumbsup": "Thumbs Up",
    
    # Actions
    "dance": "Dancing Anime",
    "wink": "Winking Anime",
    "sleep": "Sleeping Anime",
    "yawn": "Yawning Anime",
    "nom": "Eating Food",
    "awoo": "Wolf Girl Howling",
    
    # Interactions
    "hug": "Hugging Anime",
    "kiss": "Kissing Anime",
    "cuddle": "Cuddling Anime",
    "pat": "Headpat Anime",
    "slap": "Slapping Anime",
    "poke": "Poking Anime",
    "handhold": "Handholding Anime",
    "kick": "Kicking Anime",
    "wave": "Waving Anime",
    "highfive": "High Five Anime",
    "bite": "Biting Anime",
    "feed": "Feeding Anime",
    "tickle": "Tickling Anime",
    "lick": "Licking Anime",
    "punch": "Punching Anime",
    "bonk": "Bonking Anime",
    "kill": "Killing Anime",
    "shoot": "Shooting Anime",
    "stare": "Staring Anime",
    "yeet": "Yeeting Anime",
    "glomp": "Pouncing Hug",
    
    # Clothing & Features
    "uniform": "School Uniform",
    "oppai": "Well-endowed Characters",
    "selfies": "Character Taking Photo",
    "glasses": "Girls with Glasses",
    "bikini": "Bikini",
    "kimono": "Kimono",
    "lingerie": "Lingerie",
    "schoolgirl": "School Girl",
    "casual": "Casual Outfit",
    "miko": "Shrine Maiden Outfit",
    "suit": "Business Suit",
    "hoodie": "Hoodie",
    "sweater": "Sweater",
    "dress": "Dress",
    "sundress": "Sundress",
    "ponytail": "Ponytail",
    "stockings": "Stockings",
    "thighhighs": "Thigh High Socks",
    "pantyhose": "Pantyhose",
    "leggings": "Leggings",
    "heels": "High Heels",
    "boots": "Boots",
    
    # Animal Traits
    "kemonomimi": "Animal Ears Girls",
    "usagimimi": "Bunny Girl",
    "bunny-girl": "Bunny Girls",
    "kemono": "Kemono Style",
    "wolfgirl": "Wolf Girl",
    "inumimi": "Dog Girl",
    "okayu": "Cat Boy",
    "nekomata": "Cat Spirit",
    "kitsune": "Fox Spirit",
    "dragon-girl": "Dragon Girl",
    "dragon-boy": "Dragon Boy",
    "tanuki": "Tanuki Girl",
    "bakeneko": "Monster Cat",
    "snake-girl": "Snake Girl",
    "tiger-girl": "Tiger Girl",
    "shark-girl": "Shark Girl",
    "deer-girl": "Deer Girl",
    "horse-girl": "Horse Girl",
    "spider-girl": "Spider Girl",
    "bat-girl": "Bat Girl",
    "tengu": "Tengu",
    "oni": "Oni/Demon",
    
    # Settings & Themes
    "wallpaper": "Desktop Wallpaper",
    "mobileWallpaper": "Mobile Wallpaper",
    "coffee": "Coffee Image",
    "fantasy": "Fantasy Setting",
    "office-lady": "Office Lady",
    "beach": "Beach Scene",
    "wedding": "Wedding Scene", 
    "christmas": "Christmas Theme",
    "halloween": "Halloween Theme",
    "festival": "Festival Theme",
    "cyberpunk": "Cyberpunk Theme",
    "nature": "Nature Background",
    "city": "City Background",
    "school": "School Setting",
    "cafe": "Cafe Setting",
    "onsen": "Hot Spring",
    "classroom": "Classroom Setting",
    "bedroom": "Bedroom Setting",
    "restaurant": "Restaurant Setting",
    "kitchen": "Kitchen Setting",
    "library": "Library Setting",
    "gym": "Gym Setting",
    "rooftop": "Rooftop Scene",
    "hospital": "Hospital Setting",
    "shrine": "Shrine Setting",
    "garden": "Garden Setting",
    "forest": "Forest Setting",
    "mountain": "Mountain Setting",
    "sunset": "Sunset Background",
    "night": "Night Scene",
    "winter": "Winter Scene",
    "autumn": "Autumn Scene",
    "spring": "Spring Scene",
    "summer": "Summer Scene",
    "rain": "Rainy Scene",
    "snow": "Snowy Scene",
    "stars": "Starry Sky",
    "moon": "Moon Scene",
    
    # Misc Categories
    "yuri": "Girls Love",
    "elf": "Elf Characters",
    "cosplay": "Anime Cosplay",
    "anime": "General Anime",
    "girl": "Anime Girls",
    "witch": "Witch Character",
    "ninja": "Ninja Character",
    "samurai": "Samurai Character",
    "knight": "Knight Character",
    "wizard": "Wizard Character",
    "princess": "Princess Character",
    "angel": "Angel Character",
    "demon": "Demon Character",
    "vampire": "Vampire Character",
    "ghost": "Ghost Character",
    "superhero": "Superhero Character",
    "fantasy": "Fantasy Character",
    "robot": "Robot Character",
    "android": "Android Character",
    "fairy": "Fairy Character",
    "mermaid": "Mermaid Character",
    "deity": "God/Goddess Character",
    "monster-girl": "Monster Girl",
    "zombie": "Zombie Character",
    "succubus": "Succubus Character",
    "centaur": "Centaur Character",
    "magical-girl": "Magical Girl",
    "chibi": "Chibi Style",
    "jk": "High School Girl",
    "idol": "Idol Character",
    "loli": "Child Character",
    "shota": "Young Boy Character",
    "megane": "Glasses Character",
    "heterochromia": "Different Colored Eyes",
    "shrine-maiden": "Shrine Maiden"
}

# NSFW Tags organized by categories
NSFW_TAGS = {
    # Generic NSFW Character Types
    "waifu": "NSFW Anime Girls",
    "neko": "NSFW Cat Girls",
    "trap": "NSFW Trap Characters",
    "hentai": "General Hentai",
    "catgirl-nsfw": "NSFW Cat Girl",
    "foxgirl-nsfw": "NSFW Fox Girl",
    "wolfgirl-nsfw": "NSFW Wolf Girl",
    "bunnygirl-nsfw": "NSFW Bunny Girl",
    "elves-nsfw": "NSFW Elves",
    "succubus-nsfw": "NSFW Succubus",
    "demon-nsfw": "NSFW Demon",
    "angel-nsfw": "NSFW Angel",
    "witch-nsfw": "NSFW Witch",
    "vampire-nsfw": "NSFW Vampire",
    "monster-nsfw": "NSFW Monster",
    
    # Popular Anime Character NSFW
    "rem-nsfw": "Rem NSFW (Re:Zero)",
    "asuna-nsfw": "Asuna NSFW (SAO)",
    "mikasa-nsfw": "Mikasa NSFW (AoT)",
    "albedo-nsfw": "Albedo NSFW (Overlord)",
    "zero-two-nsfw": "Zero Two NSFW",
    "mai-nsfw": "Mai Sakurajima NSFW",
    "rias-nsfw": "Rias Gremory NSFW",
    "hinata-nsfw": "Hinata NSFW (Naruto)",
    "tsunade-nsfw": "Tsunade NSFW (Naruto)",
    "sakura-nsfw": "Sakura NSFW (Naruto)",
    "chizuru-nsfw": "Chizuru NSFW (Rent-a-Girlfriend)",
    "miku-nsfw": "Miku NSFW (Quintessential)",
    "nagatoro-nsfw": "Nagatoro NSFW",
    "nezuko-nsfw": "Nezuko NSFW (Demon Slayer)",
    "power-nsfw": "Power NSFW (Chainsaw Man)",
    "makima-nsfw": "Makima NSFW (Chainsaw Man)",
    "yor-nsfw": "Yor NSFW (Spy x Family)",
    "marin-nsfw": "Marin NSFW (Dress-Up Darling)",
    "roxy-nsfw": "Roxy NSFW (Mushoku Tensei)",
    "eris-nsfw": "Eris NSFW (Mushoku Tensei)",
    "sylphie-nsfw": "Sylphie NSFW (Mushoku Tensei)",
    
    # Genshin Impact NSFW
    "genshin-nsfw": "Genshin Impact NSFW",
    "raiden-nsfw": "Raiden Shogun NSFW (Genshin)",
    "ayaka-nsfw": "Ayaka NSFW (Genshin)",
    "ganyu-nsfw": "Ganyu NSFW (Genshin)",
    "hutao-nsfw": "Hu Tao NSFW (Genshin)",
    "mona-nsfw": "Mona NSFW (Genshin)",
    "keqing-nsfw": "Keqing NSFW (Genshin)",
    "eula-nsfw": "Eula NSFW (Genshin)",
    "yae-nsfw": "Yae Miko NSFW (Genshin)",
    "shenhe-nsfw": "Shenhe NSFW (Genshin)",
    "yelan-nsfw": "Yelan NSFW (Genshin)",
    "nilou-nsfw": "Nilou NSFW (Genshin)",
    "furina-nsfw": "Furina NSFW (Genshin)",
    "ningguang-nsfw": "Ningguang NSFW (Genshin)",
    "beidou-nsfw": "Beidou NSFW (Genshin)",
    
    # Honkai NSFW
    "mei-nsfw": "Raiden Mei NSFW (Honkai)",
    "kiana-nsfw": "Kiana NSFW (Honkai)",
    "bronya-nsfw": "Bronya NSFW (Honkai)",
    "seele-nsfw": "Seele NSFW (Honkai)",
    "durandal-nsfw": "Durandal NSFW (Honkai)",
    "fu-hua-nsfw": "Fu Hua NSFW (Honkai)",
    "elysia-nsfw": "Elysia NSFW (Honkai)",
    
    # Star Rail NSFW
    "kafka-nsfw": "Kafka NSFW (Star Rail)",
    "silver-wolf-nsfw": "Silver Wolf NSFW (Star Rail)",
    "seele-sr-nsfw": "Seele NSFW (Star Rail)",
    "himeko-nsfw": "Himeko NSFW (Star Rail)",
    "clara-nsfw": "Clara NSFW (Star Rail)",
    
    # Hololive NSFW
    "hololive-nsfw": "Hololive NSFW",
    "calliope-nsfw": "Mori Calliope NSFW",
    "gura-nsfw": "Gawr Gura NSFW",
    "marine-nsfw": "Marine NSFW",
    "fubuki-nsfw": "Fubuki NSFW",
    "pekora-nsfw": "Pekora NSFW",
    
    # Body Parts
    "ass": "NSFW Posterior",
    "boobs": "NSFW Chest",
    "tits": "NSFW Chest Alt",
    "pussy": "NSFW Female Parts",
    "vagina": "Female Anatomy",
    "thighs": "NSFW Thighs",
    "thigh": "Thigh Alt",
    "hthigh": "Hentai Thighs",
    "zettaiRyouiki": "Thigh High Territory",
    "feet": "NSFW Feet",
    "hfeet": "Hentai Feet",
    "midriff": "NSFW Midriff",
    "hmidriff": "Hentai Midriff",
    "hboobs": "Hentai Chest",
    "oppai-nsfw": "Oppai NSFW",
    "nipples": "Nipples NSFW",
    "pantyhose-nsfw": "Pantyhose NSFW",
    "stockings-nsfw": "Stockings NSFW",
    "thighhighs-nsfw": "Thigh Highs NSFW",
    "armpits": "Armpits NSFW",
    "navel": "Navel NSFW",
    "ass-spread": "Spread NSFW",
    "buttjob": "Butt Job NSFW",
    "cleavage": "Cleavage NSFW",
    
    # Sexual Actions
    "blowjob": "NSFW Oral",
    "bj": "BJ Alt",
    "boobjob": "NSFW Chest Job",
    "paizuri": "Paizuri",
    "cum": "NSFW Climax",
    "creampie": "NSFW Internal",
    "spank": "NSFW Spanking",
    "foot": "NSFW Foot Actions",
    "handjob": "Hand Service",
    "footjob": "Foot Service",
    "oral": "NSFW Oral Actions",
    "masturbation": "Self-Pleasure",
    "bukkake": "Multiple Finish",
    "deepthroat": "Deep Throat NSFW",
    "cunnilingus": "Female Oral NSFW",
    "titfuck": "Chest Job NSFW",
    "fingering": "Fingering NSFW",
    "groping": "Groping NSFW",
    "69": "69 Position NSFW",
    "threesome": "Threesome NSFW",
    "intercrural": "Thigh Sex NSFW",
    "armpit-job": "Armpit Job NSFW",
    "face-sitting": "Face Sitting NSFW",
    "rimjob": "Rim Job NSFW",
    "prostate": "Prostate NSFW",
    "grinding": "Grinding NSFW",
    
    # Sex Positions
    "missionary": "Missionary Position",
    "doggy": "Doggy Style",
    "cowgirl": "Cowgirl Position",
    "reverse-cowgirl": "Reverse Cowgirl",
    "standing": "Standing Position",
    "on-side": "Side Position",
    "amazon": "Amazon Position",
    "full-nelson": "Full Nelson",
    "mating-press": "Mating Press",
    "pile-driver": "Pile Driver",
    "lotus": "Lotus Position",
    "spoon": "Spooning Position",
    "chair": "Chair Position",
    "table": "Table Position",
    "wall": "Wall Position",
    
    # Types of Content
    "anal": "NSFW Rear Entry",
    "hanal": "Hentai Anal",
    "classic": "Classic NSFW",
    "ero": "Erotic Content",
    "ecchi": "Suggestive Content",
    "lesbian": "Girl-Girl NSFW",
    "lewd": "Lewd Content",
    "lewdneko": "Lewd Cat Girls",
    "lewdkitsune": "Lewd Fox Girls",
    "yuri-nsfw": "Yuri NSFW",
    "manga": "Manga Panels",
    "ahegao": "Pleasure Face",
    "futa": "Futanari",
    "pregnant": "Pregnancy NSFW",
    "lactation": "Milk NSFW",
    "uncensored": "Uncensored NSFW",
    "toys": "Sex Toys",
    "tentacle-sex": "Tentacle Sex",
    "monster-sex": "Monster Sex",
    "rape": "Non-con",
    "mind-break": "Mind Break",
    "defloration": "First Time",
    "voyeur": "Voyeurism",
    "exhibitionism": "Exhibitionism",
    "netorare": "NTR",
    "netori": "Stealing Someone's Partner",
    "yaoi": "Male-Male NSFW",
    "bara": "Muscular Male NSFW",
    "pegging": "Female-Male Strap-on",
    
    # Groups & Categories
    "gangbang": "Group Activity",
    "orgy": "NSFW Group",
    "tentacles": "NSFW Tentacles",
    "cuckold": "Cuckold",
    "incest": "Taboo Relations",
    "milf": "NSFW Mature Women",
    "public": "Public Exposure",
    "gonewild": "Amateur NSFW",
    "group": "Group NSFW",
    "ffm": "FFM Threesome",
    "mmf": "MMF Threesome",
    "harem": "Harem NSFW",
    "glory-hole": "Glory Hole",
    "swinging": "Swinging",
    "office-sex": "Office Sex",
    "beach-sex": "Beach Sex",
    "school-sex": "School Sex",
    "bathroom-sex": "Bathroom Sex",
    "outdoor-sex": "Outdoor Sex",
    "car-sex": "Car Sex",
    
    # BDSM & Power Play
    "bdsm": "NSFW Bondage",
    "femdom": "Female Domination",
    "domination": "Dominance NSFW",
    "submission": "Submission NSFW",
    "bondage": "Restraints",
    "spanking": "Punishment",
    "leather": "Leather NSFW",
    "latex": "Latex NSFW",
    "collar": "Collar NSFW",
    "leash": "Leash NSFW",
    "chains": "Chains NSFW",
    "handcuffs": "Handcuffs NSFW",
    "rope": "Rope Bondage",
    "shibari": "Japanese Rope Bondage",
    "suspension": "Suspension Bondage",
    "blindfold": "Blindfolded NSFW",
    "gag": "Gagged NSFW",
    "whip": "Whipped NSFW",
    "paddle": "Paddled NSFW",
    "petplay": "Pet Play NSFW",
    "master": "Master/Slave NSFW",
    "chastity": "Chastity NSFW",
    "maledom": "Male Domination",
    
    # Clothing & Settings
    "uniform": "NSFW Uniforms",
    "maid": "NSFW Maid",
    "school": "School Setting NSFW",
    "teacher": "Teacher NSFW",
    "student": "Student NSFW",
    "office-nsfw": "Office NSFW",
    "nurse-nsfw": "Nurse NSFW",
    "police-nsfw": "Police NSFW",
    "swimsuit-nsfw": "Swimsuit NSFW",
    "lingerie-nsfw": "Lingerie NSFW",
    "glasses-nsfw": "Glasses NSFW",
    "beach-nsfw": "Beach NSFW",
    "festival-nsfw": "Festival NSFW",
    "selfie-nsfw": "Selfie NSFW",
    "microskirt": "Micro Skirt NSFW",
    "bikini-nsfw": "Bikini NSFW",
    "apron": "Apron NSFW",
    "bunnysuit": "Bunny Suit NSFW",
    "cheerleader": "Cheerleader NSFW",
    "gym-uniform": "Gym Uniform NSFW",
    "naked-apron": "Naked Apron",
    "bodysuit": "Bodysuit NSFW",
    "virgin-killer": "Virgin Killer Sweater",
    "see-through": "See-through Clothes",
    "wedding-nsfw": "Wedding NSFW",
    "kimono-nsfw": "Kimono NSFW",
    "bloomers": "Bloomers NSFW",
    "business-suit": "Business Suit NSFW",
    "catsuit": "Catsuit NSFW",
    "lace": "Lace NSFW",
    
    # Format & Quality
    "gif": "NSFW Animations",
    "pgif": "NSFW Photo GIFs",
    "4k": "4K NSFW Images",
    "nsfwMobileWallpaper": "NSFW Phone Wallpaper",
    "hd": "HD NSFW",
    "illustration": "Illustrated NSFW",
    "censored": "Censored NSFW",
    "sketch": "Sketch Style NSFW",
    "artistic": "Artistic NSFW",
    "pixel": "Pixel Art NSFW"
}

# Keyword mapping for user input
TAG_MAPPING = {
    # Character mappings
    "wife": "waifu",
    "marin": "marin-kitagawa",
    "mori": "mori-calliope",
    "raiden": "raiden-shogun",
    "ayaka": "kamisato-ayaka",
    "genshin": "genshin-impact",
    "random": "waifu",
    "mei": "raiden-mei",
    "zerotwo": "zero-two",
    "shogun": "raiden-shogun",
    "calliope": "mori-calliope",
    "kitagawa": "marin-kitagawa",
    "ganyu": "ganyu",
    "hu-tao": "hutao",
    "kafka": "kafka",
    "makinami": "mai-sakurajima",
    "sakurajima": "mai-sakurajima",
    "bunny-senpai": "mai-sakurajima",
    "quintuplets": "miku",
    "quintessential": "miku",
    "dress-up": "marin-kitagawa",
    "darling": "zero-two",
    "ditf": "zero-two",
    "rezero": "rem",
    "re-zero": "rem",
    "konosuba": "megumin",
    "chainsaw": "power",
    "spy": "yor",
    "spy-family": "yor",
    "demon-slayer": "nezuko",
    "kimetsu": "nezuko",
    "mha": "toga",
    "hero-academia": "deku",
    "bnha": "toga",
    "naruto": "hinata",
    "sao": "asuna",
    "aot": "mikasa",
    "attack-titan": "eren",
    "railgun": "misaka",
    "index": "misaka",
    
    # General mappings
    "wallpaper": "wallpaper",
    "oppai": "oppai",
    "selfie": "selfies",
    "uniform": "uniform",
    "fox": "fox_girl",
    "foxgirl": "fox_girl",
    "nekomimi": "neko",
    "usagi": "usagimimi",
    "bunny": "bunny-girl",
    "kiss": "kiss",
    "hug": "hug",
    "baka": "baka",
    
    # NSFW mappings
    "hentai": "hentai",
    "boob": "boobs",
    "chest": "boobs",
    "butt": "ass", 
    "rear": "ass",
    "oral": "blowjob",
    "lewd": "ero",
    "ecchi": "ero",
    "tentacle": "tentacles",
    "foot": "feet",
    "tits": "tits",
    "genshin-hentai": "genshin-nsfw",
    "rem-hentai": "rem-nsfw",
    "mai-hentai": "mai-nsfw",
    "hololive-hentai": "hololive-nsfw",
    "bondage": "bdsm",
    "threesome": "threesome",
    "yuri-hentai": "yuri-nsfw"
}

ANIME_IMAGES_DIR = "/root/kazumaxcl/anime"

try:
    os.makedirs(ANIME_IMAGES_DIR, exist_ok=True)
    LOGGER.info(f"Anime images directory created at: {ANIME_IMAGES_DIR}")
except Exception as e:
    LOGGER.error(f"Error creating anime images directory: {str(e)}")

########################################
## Waifu Feature | Credit @aenulrofik ##
########################################

## For another features enhanced by Tg @WzdDizzyFlasherr ##

async def animek(client, message):
    if len(message.command) > 1:
        keyword = ' '.join(message.command[1:])
    else:
        keyword = ""
    
    loading_messages = [
        "<b>🌸 Mencari waifu terbaik untuk Anda...</b>",
        "<b>✨ Menyiapkan gambar anime...</b>",
        "<b>🔍 Menjelajahi dunia anime untuk Anda...</b>",
        "<b>🎭 Menghubungi server anime...</b>",
        "<b>📸 Mempersiapkan gambar terbaik...</b>",
        "<b>🎬 Mengakses database anime...</b>",
        "<b>🌟 Mencari karakter favorit Anda...</b>",
        "<b>🎨 Menyiapkan artwork premium...</b>"
    ]
    
    mess = await sendMessage(message, random.choice(loading_messages))
    
    if message.command[0] == "start" and len(message.command) > 1:
        if message.command[1].startswith("anhdl_"):
            file_id = message.command[1].replace("anhdl_", "")
            await download_anime_hd(client, message, mess, file_id)
            return
    
    if keyword.lower() == "list":
        button = ButtonMaker()
        button.ubutton("💖 Donasi & Dukung Kami", "https://telegra.ph/Donate-and-Support-Us-03-21")
        
        sfw_keys = list(SFW_TAGS.keys())
        random.shuffle(sfw_keys)
        sfw_sample = sfw_keys[:25]
        sfw_display = [f"• <code>{tag}</code> - {SFW_TAGS[tag]}" for tag in sfw_sample]
        sfw_text = '\n'.join(sfw_display)
        
        nsfw_keys = list(NSFW_TAGS.keys())
        random.shuffle(nsfw_keys)
        nsfw_sample = nsfw_keys[:15]
        nsfw_display = [f"• <code>{tag}</code> - {NSFW_TAGS[tag]}" for tag in nsfw_sample]
        nsfw_text = '\n'.join(nsfw_display)
        
        text = f"<b>💮 Daftar Perintah Gambar Anime</b>\n\n" \
               f"<b>❓ Cara Penggunaan:</b>\n" \
               f"• <code>/{BotCommands.AnimekCommand[0]} [tag]</code>\n" \
               f"• <code>/{BotCommands.AnimekCommand[0]} random</code> - Gambar acak\n\n" \
               f"<b>🌸 Tag SFW (Sampel):</b>\n{sfw_text}\n\n" \
               f"<b>🔞 Tag NSFW (Sampel):</b>\n{nsfw_text}\n\n" \
               f"<b>ℹ️ Catatan:</b> Gunakan <code>random</code> untuk gambar acak. Beberapa tag mungkin tidak bekerja dengan semua API."
        
        await editMessage(mess, text, button.build_menu(1))
        return
    
    private = bool(message.chat.type == ChatType.PRIVATE)
    
    if keyword == "":
        tag = random.choice(list(SFW_TAGS.keys()))
        nsfw = False
        
    elif keyword.lower() in SFW_TAGS:
        tag = keyword.lower()
        nsfw = False
        
    elif keyword.lower() in TAG_MAPPING and TAG_MAPPING[keyword.lower()] in SFW_TAGS:
        tag = TAG_MAPPING[keyword.lower()]
        nsfw = False
        
    elif keyword.lower() in NSFW_TAGS:
        tag = keyword.lower()
        nsfw = True
        
    elif keyword.lower() in TAG_MAPPING and TAG_MAPPING[keyword.lower()] in NSFW_TAGS:
        tag = TAG_MAPPING[keyword.lower()]
        nsfw = True
        
    else:
        await editMessage(mess, f"<b>⚠️ Tag tidak ditemukan: </b><code>{keyword}</code>\n\nMenggunakan kata kunci sebagai pencarian...")
        tag = random.choice(list(SFW_TAGS.keys()))
        nsfw = False
    
    image_url, api_name = await get_anime_image(tag, nsfw)
    
    if not image_url:
        fallback_tags = ["waifu", "neko", "depression"] if not nsfw else ["hentai", "boobs", "classic"]
        fallback_tag = random.choice(fallback_tags)
        LOGGER.info(f"Mencoba alternatif: {api_name} dengan tag '{fallback_tag}'")
        
        try:
            image_url, api_name = await get_anime_image(fallback_tag, nsfw)
            if not image_url:
                await editMessage(mess, f"<b>❌ Gagal mengambil gambar anime</b>\n\nSemua API gagal. Silakan coba lagi nanti atau coba tag yang berbeda.")
                return
        except Exception as e:
            LOGGER.error(f"Error dengan API alternatif: {str(e)}")
            await editMessage(mess, f"<b>❌ Gagal mengambil gambar anime</b>\n\nSemua API gagal. Silakan coba lagi nanti.")
            return
    
    try:
        tag_info = SFW_TAGS.get(tag, NSFW_TAGS.get(tag, "Anime Image"))
        nsfw_indicator = "🔞 NSFW" if nsfw else "✅ SFW"
        
        file_id = await save_anime_hd(image_url, tag)
        if not file_id:
            LOGGER.error("Gagal menyimpan gambar HD")
            file_id = f"dummy_{int(time.time())}"
        
        bot_info = await bot.get_me()
        bot_nickname = bot_info.first_name
        
        bot_username = bot_info.username
        direct_link = f"https://t.me/{bot_username}?start=anhdl_{file_id}"

        LOGGER.info(f"Creating shortlink for: {direct_link}")
        try:
            short_url = await SafeLinkU.create_short_link(direct_link)
            LOGGER.info(f"SafelinkU short link response: {short_url}")
            
            if not short_url:
                LOGGER.warning("SafelinkU returned empty URL, using direct link")
                short_url = direct_link
        except Exception as e:
            LOGGER.error(f"Error creating SafelinkU short link: {str(e)}")
            short_url = direct_link
        
        button = ButtonMaker()
        button.ubutton("⬇️ Download HD", short_url)
        button.ubutton("💖 Donasi", "https://telegra.ph/Donate-and-Support-Us-03-21", "footer")
        
        caption = f"<b>🎭 {tag_info}</b>\n<b>🏷️ Tag:</b> <code>{tag}</code>\n<b>🌐 Sumber:</b> {api_name}\n<b>📊 Jenis:</b> {nsfw_indicator}\n\n<i>Powered By {bot_nickname}</i>"
        
        if nsfw and not private:
            await editMessage(mess, f"<b>⚠️ Konten NSFW hanya dapat dilihat di chat pribadi</b>\n\n{caption}", button.build_menu(1))
        else:
            temp_file = await download_image(image_url)
            if temp_file:
                await message.reply_photo(
                    photo=temp_file, 
                    caption=caption,
                    reply_markup=button.build_menu(1)
                )
                await mess.delete()
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            else:
                await editMessage(mess, f"<b>⚠️ Gagal mengunduh gambar</b>\n\n{caption}", button.build_menu(1))
    except Exception as e:
        LOGGER.error(f"Error mengirim gambar: {str(e)}")
        await editMessage(mess, f"<b>❌ Error mengirim gambar: {str(e)}</b>")

#######################################################
## Save Image HD In Server | By Tg @WzdDizzyFlasherr ##
#######################################################

async def download_anime_hd(client, message, mess=None, file_id=None):
    try:
        if mess is None:
            hd_download_messages = [
                "<b>📥 Mengakses database gambar HD...</b>",
                "<b>⚙️ Memproses gambar resolusi tinggi...</b>",
                "<b>🔍 Mencari file HD dari server...</b>",
                "<b>📊 Menyiapkan data gambar berkualitas tinggi...</b>",
                "<b>🖼️ Mengoptimalkan gambar untuk kualitas terbaik...</b>",
                "<b>📤 Menyiapkan pengiriman gambar HD...</b>",
                "<b>🔄 Memuat file HD untuk diunduh...</b>",
                "<b>💾 Mengekstrak file gambar dari penyimpanan...</b>"
            ]
            mess = await sendMessage(message, random.choice(hd_download_messages))
        else:
            await editMessage(mess, random.choice(hd_download_messages))
        
        if file_id is None and len(message.command) > 1:
            file_id = message.command[1].replace("anhdl_", "")
        
        if not file_id:
            await editMessage(mess, "<b>❌ ID file tidak valid.</b>\n\nGunakan link download yang diberikan oleh bot.")
            return
        
        file_path = os.path.join(ANIME_IMAGES_DIR, f"{file_id}.jpg")
        info_path = os.path.join(ANIME_IMAGES_DIR, f"{file_id}.info")
        
        if not os.path.exists(file_path):
            await editMessage(mess, "<b>❌ Gambar tidak ditemukan atau telah kedaluwarsa.</b>\n\nGambar HD hanya tersimpan selama 12 jam.")
            return
        
        info_data = {}
        if os.path.exists(info_path):
            with open(info_path, 'r') as f:
                for line in f:
                    if ':' in line:
                        key, value = line.strip().split(':', 1)
                        info_data[key.strip()] = value.strip()
        
        tag_info = info_data.get('tag_info', 'Anime Image')
        
        bot_info = await bot.get_me()
        bot_nickname = bot_info.first_name
        
        await message.reply_document(
            document=file_path,
            caption=f"<b>🎭 {tag_info} HD Image</b>\n<b>🖼️ Resolusi:</b> {info_data.get('width', 'Unknown')}x{info_data.get('height', 'Unknown')}\n<b>📤 Diunduh pada:</b> {info_data.get('timestamp', 'Unknown')}\n\n<i>Powered By {bot_nickname}</i>",
            file_name=f"{tag_info.replace(' ', '_')}_HD.jpg"
        )
        
        await mess.delete()
    except Exception as e:
        LOGGER.error(f"Error downloading HD image: {str(e)}")
        error_message = f"<b>❌ Error mengirim gambar HD:</b> {str(e)}"
        if mess:
            await editMessage(mess, error_message)
        else:
            await sendMessage(message, error_message)

async def get_anime_image(tag, is_nsfw=False):
    apis = ANIME_APIS.copy()
    random.shuffle(apis)
    
    for api in apis:
        if is_nsfw and api["nsfw_url"] and tag in api["nsfw_tags"]:
            url = api["nsfw_url"].format(tag=tag)
            api_type = "NSFW"
        elif not is_nsfw and api["sfw_url"] and tag in api["sfw_tags"]:
            url = api["sfw_url"].format(tag=tag)
            api_type = "SFW"
        else:
            continue
        
        LOGGER.info(f"Trying {api['name']} API for tag '{tag}' with URL: {url}")
        
        try:
            response = requests.get(url, timeout=5)
            image_url = api["parse"](response)
            
            if image_url:
                return image_url, api["name"]
        except requests.exceptions.Timeout:
            LOGGER.error(f"Timeout with {api['name']} API")
        except Exception as e:
            LOGGER.error(f"Error with {api['name']} API: {str(e)}")
    
    return None, "No API found"

async def download_image(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp:
                temp.write(response.content)
                temp_name = temp.name
            return temp_name
        return None
    except Exception as e:
        LOGGER.error(f"Error downloading image: {str(e)}")
        return None

async def save_anime_hd(url, tag):
    try:
        try:
            cleanup_old_anime_images()
        except Exception as e:
            LOGGER.error(f"Error in cleanup: {str(e)}")
        
        file_id = f"{int(time.time())}_{random.randint(1000, 9999)}"
        file_path = os.path.join(ANIME_IMAGES_DIR, f"{file_id}.jpg")
        info_path = os.path.join(ANIME_IMAGES_DIR, f"{file_id}.info")
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            
            img = Image.open(BytesIO(response.content))
            width, height = img.size
            
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            tag_info = SFW_TAGS.get(tag, NSFW_TAGS.get(tag, "Anime Image"))
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(info_path, 'w') as f:
                f.write(f"tag: {tag}\n")
                f.write(f"tag_info: {tag_info}\n")
                f.write(f"width: {width}\n")
                f.write(f"height: {height}\n")
                f.write(f"timestamp: {timestamp}\n")
                f.write(f"original_url: {url}\n")
            
            LOGGER.info(f"Saved anime HD image: {file_path}")
            return file_id
        
        LOGGER.error(f"Failed to download image from URL: {url}")
        return None
    except Exception as e:
        LOGGER.error(f"Error saving anime HD: {str(e)}")
        return None

@new_thread
def cleanup_old_anime_images():
    try:
        twelve_hours_ago = time.time() - (12 * 60 * 60)
        
        if not os.path.exists(ANIME_IMAGES_DIR):
            LOGGER.warning(f"Anime images directory does not exist: {ANIME_IMAGES_DIR}")
            return
            
        for filename in os.listdir(ANIME_IMAGES_DIR):
            file_path = os.path.join(ANIME_IMAGES_DIR, filename)
            if os.path.getmtime(file_path) < twelve_hours_ago:
                os.remove(file_path)
                LOGGER.info(f"Deleted old anime image: {filename}")
    except Exception as e:
        LOGGER.error(f"Error cleaning up old anime images: {str(e)}")

############################
## Waifu Command Handler  ##
############################

bot.add_handler(
    MessageHandler(
        animek, 
        filters=command(
            BotCommands.AnimekCommand
        )
    )
)