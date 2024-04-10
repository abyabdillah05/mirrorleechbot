#!/usr/bin/env python3
from bot.helper.telegram_helper.bot_commands import BotCommands

# TODO : More Translate to Indonesian & Change to efisien help message, No much variable in help_message.py

MIRROR_HELP = f"""
<b>Mirror digunakan untuk mengupload file dari telegram atau link yang anda berikan ke Google Drive</b>

• Untuk mirror link atau file dari telegram, gunakan perintah /mirror
<i>contoh:</i>
<pre languange="bash">/mirror https://contoh.com</pre>

• Untuk mengextract hasil mirror, tambahkan argumen -e setelah link
<i>contoh:</i>
<pre languange="bash">/mirror https://contoh.com -e</pre>

• Untuk mengarsip hasil mirror ke ZIP file, tambahkan argumen -z setelah link
<i>contoh:</i>
<pre languange="bash">/mirror https://contoh.com -z</pre>

• Jika file yang mau diextract terenkripsi password, atau mau menambahkan password pada zip yang mau dibuat, tambahkan passwordnya setelah argumen
<i>contoh:</i>
<pre languange="bash">/mirror https://contoh.com -e password</pre>

<b>Berikut beberapa argumen lain yang bisa digunakan</b>
<b>-i Jumlah_link atau File</b> = <i>Digunakan untuk mirror banyak file atau link sekaligus (balas ke link atau file pertama)</i>
<b>-n Nama_Baru</b> = <i>Untuk mirror dan mengganti nama file</i>
<b>-m Nama_folder</b> = <i>Membuat folder baru dan mirror file kedalamnya</i>
<b>-b</b> = <i>mendownload banyak link sekaligus di dalam file txt atau dalam satu pesan</i>
<b>-j</b> = <i>Untuk menggabungkan file yang displit oleh bot dalam banyak part</i>
<b>-s</b> = <i>Untuk memilih file pada torrent sebelum dimirror</i>
<b>-up rcl</b> = <i>Untuk upload ke rclone config</i>

<i>Argumen bisa digabung sekaligus, misal mau mirror 5 file sekaligus dan membuatnya menjadi satu folder dengan nama Folder_Baru:</i>

<pre languange="bash">/mirror -i 5 -n Nama_Baru -m Folder_Baru</pre>
"""

LEECH_HELP = f"""
<b>Leech digunakan untuk mendownload video atau file anda dan menguploadnya ke Telegram</b>

• Untuk leech link, gunakan perintah /leech
<i>contoh:</i>
<pre languange="bash">/leech https://contoh.com</pre>

• Untuk mendownload dan mengextract file sebelum dileech ke telegram, tambahkan argumen -e setelah link
<i>contoh:</i>
<pre languange="bash">/leech https://contoh.com -e</pre>

• Untuk mendownload dan mengarsip file menjadi ZIP sebelum dileech ke telegram, tambahkan argumen -z setelah link
<i>contoh:</i>
<pre languange="bash">/leech https://contoh.com -z</pre>

• Jika file yang mau diextract terenkripsi password, atau mau menambahkan password pada zip yang mau dibuat, tambahkan passwordnya setelah argumen
<i>contoh:</i>
<pre languange="bash">/leech https://contoh.com -e password</pre>

<b>Argumen di bantuan mirror juga berlaku di perintah leech.</b>
"""

TORRENT_HELP = f"""
<b>Untuk mirror atau leech torrent dan magnet link, gunakan QbTorrent untuk mendapat speed lebih baik</b>

• Untuk mirror torrent atau magnet link, gunakan perintah /qbmirror
<i>contoh:</i>
<pre languange="bash">/qbmirror magnet:?xt=xxxx</pre>

• Untuk leech torrent atau magnet link, gunakan perintah /qbleech
<i>contoh:</i>
<pre languange="bash">/qbleech magnet:?xt=xxxx</pre>

• Argumen yang ada di bantuan mirror dan leech, bisa juga digunakan di qbtorrent, seperti -z,-e, dll
"""

YTDLP_HELP = f"""
<b>Yt-Dlp Adalah fitur untuk download atau leech dari situs yang disupport oleh modul yt-dlp seperti:
- youtube, instagram, tiktok, twitter, facebook dll.

Ini adalah <a href='https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md'>Kumpulan Situs</a> yang sudah disupport ytdlp</b>

• Untuk mirror atau leech link dengan Yt-Dlp, gunakan perintah dibawah:

<pre languange="bash">/ytdl (link_anda) = Untuk mirror ke google drive</pre>
<pre languange="bash">/ytdlleech (link_anda) = Untuk leech ke telegram</pre>

• Argumen yang ada di bantuan mirror/leech juga bisa dipakai untuk yt-dlp
"""

OTHER_HELP = f"""
<b>Selain Mirror dan leech, ini ada beberpa fitur tambahan dari bot ini:</b>

• /bypass = Membypass shortlink atau mengambil direct link
• /clone = Mengclone file dari link google drive lain
• /count = Menghitung jumelah file dan folder pada link google drive yang diberikan
• /list = Mencari file/folder didalam google drive
• /remove = Menghapus file/folder dari google drive hasil mirror
• /rename = Mengganti nama file/folder yang sudah di mirror
• /usetting = Membuka pengaturan untuk pengguna
• /search = Mencari link magnet/torrent dengan API dari bot
• /status = Melihat semua tugas yang sedang berjalan
• /stats = Melihat spesifikasi server bot
• /ping = Cek respon bot
• /speedtest = Cek speed koneksi server bot
• /mediainfo = Untuk melihat info dari file atau media
• /upload = Upload gambar/short video ke telegraph
• /asupan = Video asupan dari bot.
• /donate = Fitur unggulan hehe :)
"""

CLONE_HELP_MESSAGE = f"""
<b>Perintah clone hanya untuk link google drive !</b>

Gunakan /help untuk cek command yang lain.

"""

PASSWORD_ERROR_MESSAGE = """
<b>This link requires a password!</b>
- Insert <b>::</b> after the link and write the password after the sign.

<b>Contoh :</b>
<pre languange="bash"><code>/mirror {}::ini password</code></pre>

<b>Note :</b>
- Tidak ada spasi setelah tanda <code>::</code>
- Password bisa menggunakan spasi
"""

MIRROR_HELP_MESSAGE = """<b>Link tidak ditemukan, atau format perintah yang anda berikan salah, silahkan gunakan /help untuk melihat bantuan!</b>"""
LEECH_HELP_MESSAGE = """<b>Link tidak ditemukan, atau format perintah yang anda berikan salah, silahkan gunakan /help untuk melihat bantuan!</b>"""
QBMIRROR_HELP_MESSAGE = """<b>Link tidak ditemukan, atau format perintah yang anda berikan salah, silahkan gunakan /help untuk melihat bantuan!</b>"""
QBLEECH_HELP_MESSAGE = """<b>Link tidak ditemukan, atau format perintah yang anda berikan salah, silahkan gunakan /help untuk melihat bantuan!</b>"""
YT_HELP_MESSAGE = """<b>Link tidak ditemukan, atau format perintah yang anda berikan salah, silahkan gunakan /help untuk melihat bantuan!</b>"""
RSS_HELP_MESSAGE = """<b>Link tidak ditemukan, atau format perintah yang anda berikan salah, silahkan gunakan /help untuk melihat bantuan!</b>"""

#ORIGINAL HELP MESSAGE

mirror = """<b>Send link along with command line or </b>

/cmd link

<b>By replying to link/file</b>:

/cmd -n new name -e -up upload destination

<b>NOTE:</b>
1. Commands that start with <b>qb</b> are ONLY for torrents."""

yt = """<b>Send link along with command line</b>:

/cmd link
<b>By replying to link</b>:
/cmd -n new name -z password -opt x:y|x1:y1

Check here all supported <a href='https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md'>SITES</a>
Check all yt-dlp api options from this <a href='https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L184'>FILE</a> or use this <a href='https://t.me/mltb_official_channel/177'>script</a> to convert cli arguments to api options."""

new_name = """<b>New Name</b>: -n

/cmd link -n new name
Note: Doesn't work with torrents"""

multi_link = """<b>Multi links only by replying to first link/file</b>: -i

/cmd -i 10(number of links/files)"""

same_dir = """<b>Multi links within same upload directory only by replying to first link/file</b>: -m

/cmd -i 10(number of links/files) -m folder name (multi message)
/cmd -b -m folder name (bulk-message/file)"""

thumb = """<b>Thumbnail for current task</b>: -t

/cmd link -t tg-message-link(doc or photo)"""

split_size = """<b>Split size for current task</b>: -sp

/cmd link -sp (500mb or 2gb or 4000000000)
Note: Only mb and gb are supported or write in bytes without unit!"""

upload = """<b>Upload Destination</b>: -up

/cmd link -up rcl/gdl (To select rclone config/token.pickle, remote & path/ gdrive id or Tg id/username)
You can directly add the upload path: -up remote:dir/subdir or -up (Gdrive_id) or -up id/username
If DEFAULT_UPLOAD is `rc` then you can pass up: `gd` to upload using gdrive tools to GDRIVE_ID.
If DEFAULT_UPLOAD is `gd` then you can pass up: `rc` to upload to RCLONE_PATH.
If you want to add path or gdrive manually from your config/token (uploaded from usetting) add mrcc: for rclone and mtp: before the path/gdrive_id without space.
/cmd link -up mrcc:main:dump or -up mtp:gdrive_id or -up b:id/username(leech by bot) or -up u:id/username(leech by user)
Incase you want to specify whether using token or service accounts you can add tp:link or tp:gdrive_id or sa:link or sa:gdrive_id. This for links and upload destination.
DEFAULT_UPLOAD doesn't effect on leech cmds.
"""

rcf = """<b>Rclone Flags</b>: -rcf

/cmd link|path|rcl -up path|rcl -rcf --buffer-size:8M|--drive-starred-only|key|key:value
This will override all other flags except --exclude
Check here all <a href='https://rclone.org/flags/'>RcloneFlags</a>."""

bulk = """<b>Bulk Download</b>: -b

Bulk can be used by text message and by replying to text file contains links seperated by new line.
You can use it only by reply to message(text/file).
Example:
link1 -n new name -up remote1:path1 -rcf |key:value|key:value
link2 -z -n new name -up remote2:path2
link3 -e -n new name -up remote2:path2
Reply to this example by this cmd -> /cmd -b(bulk) or /cmd -b -m folder name
You can set start and end of the links from the bulk like seed, with -b start:end or only end by -b :end or only start by -b start.
The default start is from zero(first link) to inf."""

rlone_dl = """<b>Rclone Download</b>:

Treat rclone paths exactly like links
/cmd main:dump/ubuntu.iso or rcl(To select config, remote and path)
Users can add their own rclone from user settings
If you want to add path manually from your config add mrcc: before the path without space
/cmd mrcc:main:dump/ubuntu.iso"""

extract_zip = """<b>Extract/Zip</b>: -e -z

/cmd link -e password (extract password protected)
/cmd link -z password (zip password protected)
/cmd link -z password -e (extract and zip password protected)
Note: When both extract and zip added with cmd it will extract first and then zip, so always extract first"""

join = """<b>Join Splitted Files</b>: -j

This option will only work before extract and zip, so mostly it will be used with -m argument (samedir)
By Reply:
/cmd -i 3 -j -m folder name
/cmd -b -j -m folder name
if u have link(folder) have splitted files:
/cmd link -j"""

tg_links = """<b>TG Links</b>:

Treat links like any direct link
Some links need user access so sure you must add USER_SESSION_STRING for it.
Three types of links:
Public: https://t.me/channel_name/message_id
Private: tg://openmessage?user_id=xxxxxx&message_id=xxxxx
Super: https://t.me/c/channel_id/message_id
Range: https://t.me/channel_name/first_message_id-last_message_id
Range Example: tg://openmessage?user_id=xxxxxx&message_id=555-560 or https://t.me/channel_name/100-150
Note: Range link will work only by replying cmd to it"""

sample_video = """<b>Sample Video</b>: -sv

Create sample video for one video or folder of vidoes.
/cmd -sv (it will take the default values which 60sec sample duration and part duration is 4sec).
You can control those values. Example: /cmd -sv 70:5(sample-duration:part-duration) or /cmd -sv :5 or /cmd -sv 70."""

screenshot = """<b>ScreenShots</b>: -ss

Create up to 10 screenshots for one video or folder of vidoes.
/cmd -ss (it will take the default values which is 10 photos).
You can control this value. Example: /cmd -ss 6."""

seed = """<b>Bittorrent seed</b>: -d

/cmd link -d ratio:seed_time or by replying to file/link
To specify ratio and seed time add -d ratio:time.
Example: -d 0.7:10 (ratio and time) or -d 0.7 (only ratio) or -d :10 (only time) where time in minutes"""

zip = """<b>Zip</b>: -z password

/cmd link -z (zip)
/cmd link -z password (zip password protected)"""

qual = """<b>Quality Buttons</b>: -s

Incase default quality added from yt-dlp options using format option and you need to select quality for specific link or links with multi links feature.
/cmd link -s"""

yt_opt = """<b>Options</b>: -opt

/cmd link -opt playliststart:^10|fragment_retries:^inf|matchtitle:S13|writesubtitles:true|live_from_start:true|postprocessor_args:{"ffmpeg": ["-threads", "4"]}|wait_for_video:(5, 100)
Note: Add `^` before integer or float, some values must be numeric and some string.
Like playlist_items:10 works with string, so no need to add `^` before the number but playlistend works only with integer so you must add `^` before the number like example above.
You can add tuple and dict also. Use double quotes inside dict."""

YT_HELP_DICT = {
    "main": yt,
    "New-Name": f"{new_name}\nNote: Don't add file extension",
    "Zip": zip,
    "Quality": qual,
    "Options": yt_opt,
    "Multi-Link": multi_link,
    "Same-Directory": same_dir,
    "Thumb": thumb,
    "Split-Size": split_size,
    "Upload-Destination": upload,
    "Rclone-Flags": rcf,
    "Bulk": bulk,
    "Sample-Video": sample_video,
    "Screenshot": screenshot,
}

MIRROR_HELP_DICT = {
    "main": mirror,
    "New-Name": new_name,
    "DL-Auth": "<b>Direct link authorization</b>: -au -ap\n\n/cmd link -au username -ap password",
    "Headers": "<b>Direct link custom headers</b>: -h\n\n/cmd link -h key: value key1: value1",
    "Extract/Zip": extract_zip,
    "Torrent-Files": "<b>Bittorrent File Selection</b>: -s\n\n/cmd link -s or by replying to file/link",
    "Torrent-Seed": seed,
    "Multi-Link": multi_link,
    "Same-Directory": same_dir,
    "Thumb": thumb,
    "Split-Size": split_size,
    "Upload-Destination": upload,
    "Rclone-Flags": rcf,
    "Bulk": bulk,
    "Join": join,
    "Rclone-DL": rlone_dl,
    "Tg-Links": tg_links,
    "Sample-Video": sample_video,
    "Screenshot": screenshot,
}

RSS_HELP_MESSAGE = """
Use this format to add feed url:
Title1 link (required)
Title2 link -c cmd -inf xx -exf xx
Title3 link -c cmd -d ratio:time -z password

-c command -up mrcc:remote:path/subdir -rcf --buffer-size:8M|key|key:value
-inf For included words filter.
-exf For excluded words filter.

Example: Title https://www.rss-url.com inf: 1080 or 720 or 144p|mkv or mp4|hevc exf: flv or web|xxx
This filter will parse links that it's titles contains `(1080 or 720 or 144p) and (mkv or mp4) and hevc` and doesn't conyain (flv or web) and xxx` words. You can add whatever you want.

Another example: inf:  1080  or 720p|.web. or .webrip.|hvec or x264. This will parse titles that contains ( 1080  or 720p) and (.web. or .webrip.) and (hvec or x264). I have added space before and after 1080 to avoid wrong matching. If this `10805695` number in title it will match 1080 if added 1080 without spaces after it.

Filter Notes:
1. | means and.
2. Add `or` between similar keys, you can add it between qualities or between extensions, so don't add filter like this f: 1080|mp4 or 720|web because this will parse 1080 and (mp4 or 720) and web ... not (1080 and mp4) or (720 and web)."
3. You can add `or` and `|` as much as you want."
4. Take look on title if it has static special character after or before the qualities or extensions or whatever and use them in filter to avoid wrong match.
Timeout: 60 sec.
"""

CLONE_HELP_MESSAGE = """
Send Gdrive|Gdot|Filepress|Filebee|Appdrive|Gdflix link or rclone path along with command or by replying to the link/rc_path by command.

<b>Multi links only by replying to first gdlink or rclone_path:</b> -i
/cmd -i 10(number of links/paths)

<b>Bulk Clone</b>: -b
Bulk can be used by text message and by replying to text file contains links seperated by new line.
You can use it only by reply to message(text/file).
Example:
link1 -up remote1:path1 -rcf |key:value|key:value
link2 -up remote2:path2
link3 -up remote2:path2
Reply to this example by this cmd /cmd -b(bulk)
You can set start and end of the links from the bulk like seed, with -b start:end or only end by -b :end or only start by -b start. The default start is from zero(first link) to inf.

<b>Clone Destination</b>: -up
If DEFAULT_UPLOAD is `rc` then you can pass up: `gd` to upload using gdrive tools to GDRIVE_ID.
If DEFAULT_UPLOAD is `gd` then you can pass up: `rc` to upload to RCLONE_PATH.
If you want to add path or gdrive manually from your config/token (uploaded from usetting) add mrcc: for rclone and mtp: before the path/gdrive_id without space.
Incase you want to specify whether using token or service accounts you can add tp:link or tp:gdrive_id or sa:link or sa:gdrive_id. This for links and upload destination.

<b>Gdrive:</b>
/cmd gdrivelink/gdl/gdrive_id -up gdl/gdrive_id/gd

<b>Rclone:</b>
/cmd rcl/rclone_path -up rcl/rclone_path/rc -rcf flagkey:flagvalue|flagkey|flagkey:flagvalue
"""

PASSWORD_ERROR_MESSAGE = """
<b>This link requires a password!</b>
- Insert <b>::</b> after the link and write the password after the sign.

<b>Example:</b> link::my password
"""