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
• /donate = Fitur unggulan hehe :)
"""

CLONE_HELP_MESSAGE = f"""
<b>Perintah clone hanya untuk link google drive !</b>

Gunakan /help untuk cek command yang lain.

"""

PASSWORD_ERROR_MESSAGE = """
Link File ini memerlukan password!
Tambahkan password dengan menambahkan tanda <code>::</code> setelah link dan masukan password setelah tanda!

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