import os
import sys
import telebot
from telebot import types
import yt_dlp
import uuid

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

SUPPORTED_SITES = ["instagram.com", "youtube.com", "youtu.be", "tiktok.com", "twitter.com", "x.com"]

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message,
        "🎬 *InstaTubeGrabber Free Bot*\n\n"
        "سلام! 👋\n"
        "لینک ویدیو رو برام بفرست.\n\n"
        "📷 اینستاگرام | ▶️ یوتیوب | 🎵 تیک‌تاک | 🐦 توییتر\n\n"
        "⚠️ اینستاگرام: بعد از هر دانلود، ربات ری‌استارت میشه\n"
        "🟢 یوتیوب و بقیه: بدون محدودیت",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    
    if not any(site in url for site in SUPPORTED_SITES):
        bot.reply_to(message, "❌ لینک معتبر نیست!")
        return
    
    loading_msg = bot.reply_to(message, "⏳ در حال دانلود...")
    
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
            bot.edit_message_text("❌ حجم بیش از 50 مگ!", message.chat.id, loading_msg.message_id)
            os.remove(final_file)
            return
        
        bot.edit_message_text("📤 در حال آپلود...", message.chat.id, loading_msg.message_id)
        
        with open(final_file, 'rb') as video:
            bot.send_video(message.chat.id, video, caption=f"✅ دانلود شد!\n📌 {url}", reply_to_message_id=message.message_id)
        
        bot.delete_message(message.chat.id, loading_msg.message_id)
        os.remove(final_file)
        print(f"✅ {final_file}")
        
        # 🔄 ری‌استارت برای اینستاگرام
        if "instagram.com" in url:
            print("🔄 ری‌استارت برای ریست کردن Rate-Limit اینستاگرام...")
            bot.send_message(message.chat.id, "🔄 ربات در حال ری‌استارت برای دانلود بعدی...")
            os._exit(0)  # خروج کامل = GitHub Actions Job جدید می‌سازه
        
    except Exception as e:
        bot.edit_message_text(f"❌ خطا:\n`{str(e)[:200]}`", message.chat.id, loading_msg.message_id, parse_mode='Markdown')
        print(f"❌ {e}")

print("🤖 InstaTubeGrabber Free Bot | 24/7 | Auto-Restart for IG")
bot.infinity_polling()
