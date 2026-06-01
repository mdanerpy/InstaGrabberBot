import os
import telebot
from telebot import types
import yt_dlp
import uuid
from datetime import datetime, time
import pytz

# ====== تنظیمات ======
TOKEN = os.environ.get("BOT_TOKEN")  # از GitHub Secrets میخونه
bot = telebot.TeleBot(TOKEN)

# منطقه زمانی ایران
IRAN_TZ = pytz.timezone("Asia/Tehran")

# ساعات کاری
WORK_START = time(12, 0)   # ۱۲ ظهر
WORK_END = time(23, 59)    # ۱۲ شب

# پوشه دانلود
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# ====== چک کردن ساعت کاری ======
def is_working_hour():
    now = datetime.now(IRAN_TZ).time()
    return WORK_START <= now <= WORK_END

# ====== هندلرها ======
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if is_working_hour():
        bot.reply_to(message,
            "🎬 *InstaGrabber Bot*\n\n"
            "سلام! 👋\n"
            "لینک ویدیو یا ریلز اینستاگرام رو برام بفرست تا برات دانلودش کنم.\n\n"
            "🕐 *ساعت کاری:* ۱۲ ظهر تا ۱۲ شب (به وقت ایران)\n"
            "💰 *هزینه:* رایگان\n\n"
            "🔹 *نکته:* فقط لینک پست‌های عمومی",
            parse_mode='Markdown'
        )
    else:
        bot.reply_to(message,
            "⏰ *خارج از ساعت کاری!*\n\n"
            "🕐 ربات فقط از *۱۲ ظهر تا ۱۲ شب* فعاله.\n"
            "لطفاً توی این بازه زمانی پیام بدید.\n\n"
            "🙏 ممنون از صبوریت!",
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if not is_working_hour():
        bot.reply_to(message,
            "⏰ *ربات الان خوابیده!*\n"
            "🕐 لطفاً بین *۱۲ ظهر تا ۱۲ شب* پیام بدید.",
            parse_mode='Markdown'
        )
        return
    
    url = message.text.strip()
    
    if "instagram.com" not in url:
        bot.reply_to(message, "❌ لطفاً یه لینک معتبر اینستاگرام بفرست!")
        return
    
    loading_msg = bot.reply_to(message, "⏳ در حال دانلود ویدیو... لطفاً صبر کن.")
    
    try:
        unique_id = str(uuid.uuid4())[:8]
        output_path = os.path.join(DOWNLOAD_DIR, f"insta_video_{unique_id}.%(ext)s")
        
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
                if f.startswith(f"insta_video_{unique_id}"):
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

# ====== اجرای ربات ======
print("🤖 InstaGrabber Bot is running...")
print(f"🕐 Working hours: 12:00 - 23:59 Iran time")
bot.infinity_polling()