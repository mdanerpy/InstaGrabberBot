import os
import sys
import time
import telebot
from telebot import types
from telebot import apihelper
import yt_dlp
import uuid

TOKEN = os.environ.get("BOT_TOKEN")

# افزایش تایم‌اوت
apihelper.READ_TIMEOUT = 60
apihelper.CONNECT_TIMEOUT = 30

bot = telebot.TeleBot(TOKEN, threaded=False)  # Single thread برای پایداری بیشتر

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

SUPPORTED_SITES = ["instagram.com", "youtube.com", "youtu.be", "tiktok.com", "twitter.com", "x.com"]
DOWNLOAD_COUNT = 0  # شمارنده دانلود

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    try:
        bot.reply_to(message,
            "🎬 *InstaTubeGrabber Free Bot*\n\n"
            "سلام! 👋\n"
            "لینک ویدیو رو برام بفرست.\n\n"
            "📷 اینستاگرام | ▶️ یوتیوب | 🎵 تیک‌تاک | 🐦 توییتر\n\n"
            "⚠️ اینستاگرام: بعد از دانلود ری‌استارت میشه\n"
            "🟢 بقیه: بدون محدودیت",
            parse_mode='Markdown'
        )
    except:
        pass  # اگه نتونست پیام بده، بی‌خیال شو

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global DOWNLOAD_COUNT
    url = message.text.strip()
    
    if not any(site in url for site in SUPPORTED_SITES):
        try:
            bot.reply_to(message, "❌ لینک معتبر نیست!")
        except:
            pass
        return
    
    # ارسال پیام با تلاش مجدد
    loading_msg = None
    for attempt in range(3):
        try:
            loading_msg = bot.reply_to(message, "⏳ در حال دانلود...")
            break
        except:
            time.sleep(2)
    
    if not loading_msg:
        return
    
    try:
        unique_id = str(uuid.uuid4())[:8]
        output_path = os.path.join(DOWNLOAD_DIR, f"video_{unique_id}.%(ext)s")
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
            'max_filesize': 50 * 1024 * 1024,
            'socket_timeout': 30,
            'retries': 3,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final_file = ydl.prepare_filename(info)
        
        # پیدا کردن فایل
        if not os.path.exists(final_file):
            for f in os.listdir(DOWNLOAD_DIR):
                if f.startswith(f"video_{unique_id}"):
                    final_file = os.path.join(DOWNLOAD_DIR, f)
                    break
        
        if not os.path.exists(final_file):
            raise Exception("فایل دانلود نشد!")
        
        file_size = os.path.getsize(final_file)
        if file_size > 50 * 1024 * 1024:
            try:
                bot.edit_message_text("❌ حجم بیش از 50 مگ!", message.chat.id, loading_msg.message_id)
            except:
                pass
            os.remove(final_file)
            return
        
        # آپلود با تلاش مجدد
        try:
            bot.edit_message_text("📤 در حال آپلود...", message.chat.id, loading_msg.message_id)
        except:
            pass
        
        for attempt in range(3):
            try:
                with open(final_file, 'rb') as video:
                    bot.send_video(
                        message.chat.id,
                        video,
                        caption=f"✅ دانلود شد!\n📌 {url}",
                        reply_to_message_id=message.message_id,
                        timeout=60
                    )
                break
            except Exception as e:
                if attempt == 2:
                    raise e
                time.sleep(3)
        
        try:
            bot.delete_message(message.chat.id, loading_msg.message_id)
        except:
            pass
        
        os.remove(final_file)
        DOWNLOAD_COUNT += 1
        print(f"✅ دانلود #{DOWNLOAD_COUNT}: {final_file}")
        
        # ری‌استارت برای اینستاگرام
        if "instagram.com" in url:
            print("🔄 ری‌استارت برای ریست Rate-Limit...")
            try:
                bot.send_message(message.chat.id, "✅ دانلود شد! ربات برای دانلود بعدی ری‌استارت میشه...")
            except:
                pass
            time.sleep(2)
            os._exit(0)
        
    except Exception as e:
        error_msg = str(e)[:150]
        print(f"❌ خطا: {error_msg}")
        try:
            bot.edit_message_text(
                f"❌ خطا:\n`{error_msg}`\n\n🔄 ربات ری‌استارت میشه...",
                message.chat.id,
                loading_msg.message_id,
                parse_mode='Markdown'
            )
        except:
            pass
        
        # ری‌استارت حتی در صورت خطا (برای اینستاگرام)
        if "instagram.com" in url:
            time.sleep(2)
            os._exit(0)

# ====== اجرا با مدیریت خطا ======
print("🤖 InstaTubeGrabber Free Bot | 24/7 | Auto-Restart")
print(f"📊 Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        print(f"⚠️ Connection error: {e}")
        print("🔄 Restarting in 5 seconds...")
        time.sleep(5)
