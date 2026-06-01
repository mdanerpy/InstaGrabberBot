import os
import sys
import time
import random
import telebot
from telebot import apihelper
import yt_dlp
import uuid

TOKEN = os.environ.get("BOT_TOKEN")
apihelper.READ_TIMEOUT = 60
apihelper.CONNECT_TIMEOUT = 30
bot = telebot.TeleBot(TOKEN, threaded=False)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

SUPPORTED_SITES = ["instagram.com", "youtube.com", "youtu.be", "tiktok.com", "twitter.com", "x.com"]

# سرویس‌های واسطه اینستاگرام
INSTA_PROXIES = [
    "ddinstagram.com",
    "igdownloader.app",
]

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    try:
        bot.reply_to(message,
            "🎬 *InstaTubeGrabber Free Bot*\n\n"
            "سلام! 👋\n"
            "📷 اینستاگرام | ▶️ یوتیوب | 🎵 تیک‌تاک | 🐦 توییتر\n\n"
            "💡 با سرویس‌های چرخشی برای دور زدن محدودیت",
            parse_mode='Markdown'
        )
    except:
        pass

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    
    if not any(site in url for site in SUPPORTED_SITES):
        try:
            bot.reply_to(message, "❌ لینک معتبر نیست!")
        except:
            pass
        return
    
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
        # 🔄 استفاده از سرویس واسطه برای اینستاگرام
        if "instagram.com" in url:
            proxy_service = random.choice(INSTA_PROXIES)
            url = url.replace("instagram.com", proxy_service)
            print(f"🔄 Using: {proxy_service}")
        
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
        
        if not os.path.exists(final_file):
            for f in os.listdir(DOWNLOAD_DIR):
                if f.startswith(f"video_{unique_id}"):
                    final_file = os.path.join(DOWNLOAD_DIR, f)
                    break
        
        file_size = os.path.getsize(final_file)
        if file_size > 50 * 1024 * 1024:
            try:
                bot.edit_message_text("❌ حجم بیش از 50 مگ!", message.chat.id, loading_msg.message_id)
            except:
                pass
            os.remove(final_file)
            return
        
        try:
            bot.edit_message_text("📤 آپلود...", message.chat.id, loading_msg.message_id)
        except:
            pass
        
        with open(final_file, 'rb') as video:
            bot.send_video(message.chat.id, video, caption=f"✅ دانلود شد!\n📌 {url}", reply_to_message_id=message.message_id, timeout=60)
        
        try:
            bot.delete_message(message.chat.id, loading_msg.message_id)
        except:
            pass
        
        os.remove(final_file)
        print(f"✅ {final_file}")
        
    except Exception as e:
        error_msg = str(e)[:150]
        print(f"❌ {error_msg}")
        try:
            bot.edit_message_text(f"❌ خطا:\n`{error_msg}`", message.chat.id, loading_msg.message_id, parse_mode='Markdown')
        except:
            pass

print("🤖 InstaTubeGrabber Free Bot | 24/7 | Proxy Rotation")
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        print(f"⚠️ {e}")
        time.sleep(5)
