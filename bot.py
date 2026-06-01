import os
import telebot
from telebot import types
import yt_dlp
import uuid

# ====== تنظیمات ======
TOKEN = os.environ.get("BOT_TOKEN")  # از GitHub Secrets میخونه
bot = telebot.TeleBot(TOKEN)

# پوشه دانلود
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# ====== پیام خوش‌آمد ======
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message,
        "🎬 *InstaGrabber Bot*\n\n"
        "سلام! 👋\n"
        "لینک ویدیو یا ریلز اینستاگرام رو برام بفرست تا برات دانلودش کنم.\n\n"
        "🟢 *ربات ۲۴ ساعته فعاله!*\n"
        "💰 *کاملاً رایگان*\n\n"
        "🔹 *نکته:* فقط لینک پست‌های عمومی رو می‌تونم دانلود کنم.",
        parse_mode='Markdown'
    )

# ====== دریافت لینک و دانلود ======
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    
    # چک کردن معتبر بودن لینک
    if "instagram.com" not in url:
        bot.reply_to(message, "❌ لطفاً یه لینک معتبر اینستاگرام بفرست!")
        return
    
    # پیام در حال دانلود
    loading_msg = bot.reply_to(message, "⏳ در حال دانلود ویدیو... لطفاً صبر کن.")
    
    try:
        # نام فایل یکتا برای جلوگیری از تداخل
        unique_id = str(uuid.uuid4())[:8]
        output_path = os.path.join(DOWNLOAD_DIR, f"insta_video_{unique_id}.%(ext)s")
        
        # تنظیمات yt-dlp
        ydl_opts = {
            'format': 'best',  # بهترین کیفیت ویدیو
            'outtmpl': output_path,  # مسیر ذخیره
            'quiet': True,  # لوگ اضافی نده
            'no_warnings': True,
            'max_filesize': 50 * 1024 * 1024,  # محدودیت 50 مگ (تلگرام محدودیت داره)
        }
        
        # دانلود ویدیو
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final_file = ydl.prepare_filename(info)
        
        # چک کردن اینکه فایل وجود داره
        if not os.path.exists(final_file):
            # بعضی وقتا فرمت خروجی mp4 نیست و باید پیداش کنیم
            for f in os.listdir(DOWNLOAD_DIR):
                if f.startswith(f"insta_video_{unique_id}"):
                    final_file = os.path.join(DOWNLOAD_DIR, f)
                    break
        
        # حجم فایل رو چک کن
        file_size = os.path.getsize(final_file)
        if file_size > 50 * 1024 * 1024:
            bot.edit_message_text(
                "❌ حجم ویدیو بیشتر از 50 مگابایته و تلگرام اجازه آپلودش رو نمیده!",
                message.chat.id,
                loading_msg.message_id
            )
            os.remove(final_file)
            return
        
        # ارسال ویدیو به کاربر
        bot.edit_message_text("📤 در حال آپلود ویدیو...", message.chat.id, loading_msg.message_id)
        
        with open(final_file, 'rb') as video:
            bot.send_video(
                message.chat.id,
                video,
                caption=f"✅ ویدیو با موفقیت دانلود شد!\n\n📌 منبع: {url}",
                reply_to_message_id=message.message_id
            )
        
        # پاک کردن پیام "در حال دانلود"
        bot.delete_message(message.chat.id, loading_msg.message_id)
        
        # پاک کردن فایل از سرور
        os.remove(final_file)
        
        print(f"✅ ویدیو ارسال و پاک شد: {final_file}")
        
    except Exception as e:
        bot.edit_message_text(
            f"❌ خطا در دانلود ویدیو:\n\n`{str(e)[:200]}`\n\n🔹 ممکنه لینک خصوصی باشه یا اینستاگرام محدودیت گذاشته باشه.",
            message.chat.id,
            loading_msg.message_id,
            parse_mode='Markdown'
        )
        print(f"❌ خطا: {e}")

# ====== اجرای ربات ======
print("🤖 InstaGrabber Bot is running 24/7!")
bot.infinity_polling()
