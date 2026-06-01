import os
import telebot
from telebot import types
import yt_dlp
import uuid
import requests
import re
import json

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
        "📷 اینستاگرام\n"
        "▶️ یوتیوب\n"
        "🎵 تیک‌تاک\n"
        "🐦 توییتر/X\n\n"
        "🟢 *۲۴ ساعته | رایگان*",
        parse_mode='Markdown'
    )

def download_instagram_snapinsta(url):
    """دانلود اینستاگرام با SnapInsta (بدون لاگین)"""
    api_url = "https://snapinsta.app/action2.php"
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://snapinsta.app/"
    }
    
    data = {
        "url": url,
        "action": "post"
    }
    
    # گرفتن لینک دانلود
    response = requests.post(api_url, data=data, headers=headers, timeout=30)
    
    # پیدا کردن لینک ویدیو
    video_match = re.search(r'href="(https://snapinsta\.app/download/.*?)"', response.text)
    if video_match:
        video_page = video_match.group(1)
        # گرفتن لینک مستقیم
        vid_response = requests.get(video_page, headers=headers, timeout=30)
        direct_match = re.search(r'href="(https://.*?\.(?:mp4|mov))"', vid_response.text)
        if direct_match:
            direct_url = direct_match.group(1)
            # دانلود فایل
            output_path = os.path.join(DOWNLOAD_DIR, f"insta_{uuid.uuid4().hex[:8]}.mp4")
            vid_data = requests.get(direct_url, headers=headers, timeout=60)
            with open(output_path, 'wb') as f:
                f.write(vid_data.content)
            return output_path
    
    raise Exception("نتونست از SnapInsta دانلود کنه")

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
        bot.reply_to(message, "❌ لینک معتبر نیست!")
        return
    
    loading_msg = bot.reply_to(message, "⏳ در حال دانلود... صبر کن.")
    
    try:
        if "instagram.com" in url:
            # تلاش با SnapInsta
            try:
                final_file = download_instagram_snapinsta(url)
            except:
                # اگر نشد، با yt-dlp مستقیم
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
        else:
            unique_id = str(uuid.uuid4())[:8]
            output_path = os.path.join(DOWNLOAD_DIR, f"video_{unique_id}.%(ext)s")
            final_file = download_other(url, output_path)
        
        # چک کردن وجود فایل
        if not os.path.exists(final_file):
            for f in os.listdir(DOWNLOAD_DIR):
                if os.path.getsize(os.path.join(DOWNLOAD_DIR, f)) > 0:
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
print("📷 IG (SnapInsta) | ▶️ YT | 🎵 TT | 🐦 X")
bot.infinity_polling()
