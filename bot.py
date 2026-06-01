import os
import telebot
from telebot import types
import yt_dlp
import uuid
import requests
import re

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
        "لینک ویدیو رو برام بفرست تا برات دانلودش کنم.\n\n"
        "🟢 *سایت‌های پشتیبانی شده:*\n"
        "📷 اینستاگرام (Reels, Posts)\n"
        "▶️ یوتیوب (Shorts, Videos)\n"
        "🎵 تیک‌تاک\n"
        "🐦 توییتر/X\n\n"
        "🟢 *۲۴ ساعته | رایگان*",
        parse_mode='Markdown'
    )

def download_instagram(url, output_path):
    """دانلود اینستاگرام بدون نیاز به لاگین - با سرویس واسطه"""
    # تبدیل لینک به ddinstagram
    if "instagram.com" in url:
        url = url.replace("instagram.com", "ddinstagram.com")
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'max_filesize': 50 * 1024 * 1024,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

def download_other(url, output_path):
    """دانلود از یوتیوب، تیک‌تاک، توییتر"""
    ydl_opts = {
        'format': 'best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'max_filesize': 50 * 1024 * 1024,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    
    if not any(site in url for site in SUPPORTED_SITES):
        bot.reply_to(message, "❌ لینک معتبر نیست!\n📷 IG | ▶️ YT | 🎵 TT | 🐦 X")
        return
    
    loading_msg = bot.reply_to(message, "⏳ در حال دانلود... صبر کن.")
    
    try:
        unique_id = str(uuid.uuid4())[:8]
        output_path = os.path.join(DOWNLOAD_DIR, f"video_{unique_id}.%(ext)s")
        
        # تشخیص اینستاگرام
        if "instagram.com" in url:
            final_file = download_instagram(url, output_path)
        else:
            final_file = download_other(url, output_path)
        
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
        
        bot.edit_message_text("📤 در حال آپلود...", message.chat.id, loading_msg.message_id)
        
        with open(final_file, 'rb') as video:
            bot.send_video(message.chat.id, video, caption=f"✅ دانلود شد!\n📌 {url}", reply_to_message_id=message.message_id)
        
        bot.delete_message(message.chat.id, loading_msg.message_id)
        os.remove(final_file)
        print(f"✅ ارسال شد: {final_file}")
        
    except Exception as e:
        bot.edit_message_text(f"❌ خطا:\n`{str(e)[:150]}`", message.chat.id, loading_msg.message_id, parse_mode='Markdown')
        print(f"❌ خطا: {e}")

print("🤖 InstaTubeGrabber Free Bot | 24/7")
bot.infinity_polling()
