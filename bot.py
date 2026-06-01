import os
import telebot
from telebot import types
import yt_dlp
import uuid

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# لیست سایت‌های پشتیبانی شده
SUPPORTED_SITES = [
    "instagram.com",
    "youtube.com",
    "youtu.be",
    "tiktok.com",
    "twitter.com",
    "x.com",
]

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message,
        "🎬 *InstaGrabberPro Free Bot*\n\n"
        "سلام! 👋\n"
        "لینک ویدیو رو برام بفرست تا برات دانلودش کنم.\n\n"
        "🟢 *سایت‌های پشتیبانی شده:*\n"
        "📷 اینستاگرام (Reels, Posts)\n"
        "▶️ یوتیوب (Shorts, Videos)\n"
        "🎵 تیک‌تاک\n"
        "🐦 توییتر/X\n\n"
        "🟢 *ربات ۲۴ ساعته فعاله!*\n"
        "💰 *کاملاً رایگان*",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    
    # چک کردن معتبر بودن لینک
    if not any(site in url for site in SUPPORTED_SITES):
        bot.reply_to(message, "❌ لطفاً یه لینک معتبر بفرست!\n📷 اینستاگرام | ▶️ یوتیوب | 🎵 تیک‌تاک | 🐦 توییتر")
        return
    
    loading_msg = bot.reply_to(message, "⏳ در حال دانلود ویدیو... لطفاً صبر کن.")
    
    try:
        unique_id = str(uuid.uuid4())[:8]
        output_path = os.path.join(DOWNLOAD_DIR, f"video_{unique_id}.%(ext)s")
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
            'max_filesize': 50 * 1024 * 1024,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final_file = ydl.prepare_filename(info)
        
        if not os.path.exists(final_file):
            for f in os.listdir(DOWNLOAD_DIR):
                if f.startswith(f"video_{unique_id}"):
                    final_file = os.path.join(DOWNLOAD_DIR, f)
                    break
        
        file_size = os.path.getsize(final_file)
        if file_size > 50 * 1024 * 1024:
            bot.edit_message_text("❌ حجم ویدیو بیشتر از 50 مگابایته!", message.chat.id, loading_msg.message_id)
            os.remove(final_file)
            return
        
        bot.edit_message_text("📤 در حال آپلود ویدیو...", message.chat.id, loading_msg.message_id)
        
        with open(final_file, 'rb') as video:
            bot.send_video(message.chat.id, video, caption=f"✅ دانلود شد!\n📌 {url}", reply_to_message_id=message.message_id)
        
        bot.delete_message(message.chat.id, loading_msg.message_id)
        os.remove(final_file)
        print(f"✅ ویدیو ارسال و پاک شد: {final_file}")
        
    except Exception as e:
        bot.edit_message_text(f"❌ خطا:\n`{str(e)[:200]}`", message.chat.id, loading_msg.message_id, parse_mode='Markdown')
        print(f"❌ خطا: {e}")

print("🤖 InstaGrabberPro Free Bot is running 24/7!")
print("📷 Instagram | ▶️ YouTube | 🎵 TikTok | 🐦 Twitter")
bot.infinity_polling()
