import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import mysql.connector
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler
)
import asyncio
from threading import Thread

# Load environment variables
load_dotenv()

# Debug environment variables
print(f"Current working directory: {os.getcwd()}")
print(f".env file exists: {os.path.exists('.env')}")

# Read .env file manually to debug
if os.path.exists('.env'):
    with open('.env', 'r', encoding='utf-8') as f:
        print("Content of .env file:")
        content = f.read()
        print(repr(content))  # This will show hidden characters

TOKEN = os.getenv('BOT_TOKEN')
print(f"TOKEN loaded: {'Yes' if TOKEN else 'No'}")
if TOKEN:
    print(f"TOKEN length: {len(TOKEN)}")
    print(f"TOKEN starts with: {TOKEN[:10]}...")

# Alternative: Load directly from file if environment variable fails
if not TOKEN:
    print("Trying to load TOKEN directly from .env file...")
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('BOT_TOKEN='):
                    TOKEN = line.split('=', 1)[1].strip()
                    print(f"TOKEN loaded directly: {'Yes' if TOKEN else 'No'}")
                    break

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database connection
def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            database=os.getenv('DB_NAME')
        )
    except mysql.connector.Error as err:
        logger.error(f"Database connection error: {err}")
        return None

# States for conversation
GET_NAME, GET_EVENT_NAME, GET_EVENT_DATE, GET_EVENT_TIME, GET_REMINDER_CHOICE = range(5)

# Initialize database tables
def init_database():
    conn = get_db_connection()
    if conn is None:
        logger.error("Cannot connect to database for initialization")
        return False
    
    cursor = conn.cursor()
    try:
        # Create users table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                chat_id BIGINT UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create jadwal table if not exists (with h1 column added)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jadwal (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nama_event VARCHAR(255) NOT NULL,
                tanggal_event DATETIME NOT NULL,
                chat_id BIGINT NOT NULL,
                ingatkan_h12 TINYINT(1) DEFAULT 0,
                ingatkan_h4 TINYINT(1) DEFAULT 0,
                ingatkan_h1 TINYINT(1) DEFAULT 0,
                is_active TINYINT(1) DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add h1 column if it doesn't exist (for existing databases)
        cursor.execute("""
            ALTER TABLE jadwal 
            ADD COLUMN IF NOT EXISTS ingatkan_h1 TINYINT(1) DEFAULT 0
        """)
        
        # Add is_active column if it doesn't exist
        cursor.execute("""
            ALTER TABLE jadwal 
            ADD COLUMN IF NOT EXISTS is_active TINYINT(1) DEFAULT 1
        """)
        
        conn.commit()
        logger.info("Database tables initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# Helper functions
def get_user_name(chat_id):
    conn = get_db_connection()
    if conn is None:
        return None
    
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM users WHERE chat_id = %s", (chat_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error getting user name: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def save_user_name(chat_id, name):
    conn = get_db_connection()
    if conn is None:
        return False
    
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (chat_id, name) VALUES (%s, %s) "
            "ON DUPLICATE KEY UPDATE name = %s",
            (chat_id, name, name)
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error saving user name: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# Bot commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Check if user already has a name
    existing_name = get_user_name(chat_id)
    
    if existing_name:
        await update.message.reply_text(
            f"Halo {existing_name}! Selamat datang kembali! 👋\n\n"
            "📋 Menu yang tersedia:\n"
            "• /tambah - Tambah jadwal baru\n"
            "• /list - Lihat daftar jadwal\n"
            "• /stop - Hentikan pengingat jadwal\n"
            "• /help - Bantuan lengkap\n\n"
            "Apa yang ingin Anda lakukan hari ini?"
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            f"Halo {user.first_name}! 👋\n\n"
            "Selamat datang di Bot Pengingat Jadwal! 🤖\n\n"
            "Untuk memulai, silakan masukkan nama Anda:"
        )
        return GET_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    chat_id = update.effective_chat.id
    
    if len(name) < 2:
        await update.message.reply_text("Nama terlalu pendek. Silakan masukkan nama yang valid (minimal 2 karakter):")
        return GET_NAME
    
    if save_user_name(chat_id, name):
        await update.message.reply_text(
            f"Terima kasih {name}! 😊\n\n"
            "Sekarang Anda sudah terdaftar dan bisa menggunakan bot ini.\n\n"
            "📋 Menu yang tersedia:\n"
            "• /tambah - Tambah jadwal baru\n"
            "• /list - Lihat daftar jadwal\n"
            "• /stop - Hentikan pengingat jadwal\n"
            "• /help - Bantuan lengkap\n\n"
            "Silakan ketik /tambah untuk membuat jadwal pertama Anda!"
        )
    else:
        await update.message.reply_text("Gagal menyimpan nama. Silakan coba lagi nanti.")
    
    return ConversationHandler.END

async def tambah_jadwal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    user_name = get_user_name(chat_id)
    
    if not user_name:
        await update.message.reply_text(
            "Anda belum terdaftar. Silakan ketik /start terlebih dahulu untuk mendaftar."
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        f"Halo {user_name}! 📝\n\n"
        "Silakan kirim nama event/jadwal yang ingin Anda tambahkan:"
    )
    return GET_EVENT_NAME

async def get_event_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['event_name'] = update.message.text.strip()
    await update.message.reply_text(
        "📅 Silakan kirim tanggal event (format: DD-MM-YYYY):\n"
        "Contoh: 25-12-2024"
    )
    return GET_EVENT_DATE

async def get_event_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        date_text = update.message.text.strip()
        event_date = datetime.strptime(date_text, '%d-%m-%Y').date()
        
        # Check if the date is in the future or today
        if event_date < datetime.now().date():
            await update.message.reply_text(
                "📅 Tanggal event harus hari ini atau di masa depan. Silakan masukkan tanggal yang valid.\n"
                "Format: DD-MM-YYYY (contoh: 25-12-2024)"
            )
            return GET_EVENT_DATE
        
        context.user_data['event_date'] = event_date
        
        await update.message.reply_text(
            "⏰ Silakan kirim waktu event (format: HH:MM):\n"
            "Contoh: 14:30 atau 09:15"
        )
        return GET_EVENT_TIME
    except ValueError:
        await update.message.reply_text(
            "❌ Format tanggal tidak valid. Silakan kirim dalam format DD-MM-YYYY\n"
            "Contoh: 25-12-2024"
        )
        return GET_EVENT_DATE

async def get_event_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        time_text = update.message.text.strip()
        event_time = datetime.strptime(time_text, '%H:%M').time()
        
        # Combine date and time
        event_date = context.user_data['event_date']
        event_datetime = datetime.combine(event_date, event_time)
        
        # Check if the datetime is in the future
        if event_datetime <= datetime.now():
            await update.message.reply_text(
                "⏰ Waktu event harus di masa depan. Silakan masukkan waktu yang valid.\n"
                "Format: HH:MM (contoh: 14:30)"
            )
            return GET_EVENT_TIME
        
        context.user_data['event_datetime'] = event_datetime
        
        keyboard = [
            [
                InlineKeyboardButton("H-12 jam", callback_data='h12'),
                InlineKeyboardButton("H-4 jam", callback_data='h4'),
                InlineKeyboardButton("H-1 jam", callback_data='h1'),
            ],
            [
                InlineKeyboardButton("H-12 & H-4", callback_data='h12_h4'),
                InlineKeyboardButton("H-4 & H-1", callback_data='h4_h1'),
            ],
            [
                InlineKeyboardButton("Semua (H-12, H-4, H-1)", callback_data='all'),
                InlineKeyboardButton("Tidak perlu", callback_data='none'),
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📋 **Ringkasan Jadwal:**\n"
            f"📅 Event: {context.user_data['event_name']}\n"
            f"📆 Tanggal: {event_datetime.strftime('%d-%m-%Y')}\n"
            f"⏰ Waktu: {event_datetime.strftime('%H:%M')}\n\n"
            "🔔 Pilih pengingat yang diinginkan:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return GET_REMINDER_CHOICE
    except ValueError:
        await update.message.reply_text(
            "❌ Format waktu tidak valid. Silakan kirim dalam format HH:MM\n"
            "Contoh: 14:30 atau 09:15"
        )
        return GET_EVENT_TIME

async def save_jadwal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    chat_id = update.effective_chat.id
    event_name = context.user_data['event_name']
    event_datetime = context.user_data['event_datetime']
    
    # Determine reminder settings based on callback data
    h12 = 1 if query.data in ['h12', 'h12_h4', 'all'] else 0
    h4 = 1 if query.data in ['h4', 'h12_h4', 'h4_h1', 'all'] else 0
    h1 = 1 if query.data in ['h1', 'h4_h1', 'all'] else 0
    
    conn = get_db_connection()
    if conn is None:
        await query.edit_message_text("❌ Gagal terhubung ke database. Silakan coba lagi nanti.")
        return ConversationHandler.END
    
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO jadwal (nama_event, tanggal_event, chat_id, ingatkan_h12, ingatkan_h4, ingatkan_h1) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (event_name, event_datetime, chat_id, h12, h4, h1)
        )
        conn.commit()
        
        reminder_text = []
        if h12:
            reminder_text.append("H-12 jam")
        if h4:
            reminder_text.append("H-4 jam")
        if h1:
            reminder_text.append("H-1 jam")
        reminder_str = ", ".join(reminder_text) if reminder_text else "Tidak ada"
        
        await query.edit_message_text(
            f"✅ **Jadwal berhasil disimpan!**\n\n"
            f"📅 Event: {event_name}\n"
            f"📆 Tanggal: {event_datetime.strftime('%d-%m-%Y')}\n"
            f"⏰ Waktu: {event_datetime.strftime('%H:%M')}\n"
            f"🔔 Pengingat: {reminder_str}\n\n"
            f"Gunakan /list untuk melihat semua jadwal Anda.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error saving schedule: {e}")
        await query.edit_message_text("❌ Gagal menyimpan jadwal. Silakan coba lagi.")
    finally:
        cursor.close()
        conn.close()
    
    return ConversationHandler.END

async def list_jadwal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_name = get_user_name(chat_id)
    
    if not user_name:
        await update.message.reply_text(
            "Anda belum terdaftar. Silakan ketik /start terlebih dahulu untuk mendaftar."
        )
        return
    
    conn = get_db_connection()
    if conn is None:
        await update.message.reply_text("❌ Gagal terhubung ke database. Silakan coba lagi nanti.")
        return
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            "SELECT id, nama_event, tanggal_event, ingatkan_h12, ingatkan_h4, ingatkan_h1, is_active "
            "FROM jadwal WHERE chat_id = %s AND tanggal_event > NOW() AND is_active = 1 ORDER BY tanggal_event",
            (chat_id,)
        )
        jadwals = cursor.fetchall()
        
        if not jadwals:
            await update.message.reply_text(
                f"Halo {user_name}! 📋\n\n"
                "Anda belum memiliki jadwal aktif atau semua jadwal sudah berlalu.\n\n"
                "Gunakan /tambah untuk membuat jadwal baru."
            )
            return
        
        message = f"📋 **Daftar Jadwal {user_name}:**\n\n"
        for i, jadwal in enumerate(jadwals, 1):
            status = "🟢 Aktif" if jadwal['is_active'] else "🔴 Tidak Aktif"
            message += (
                f"{i}. 📅 **{jadwal['nama_event']}**\n"
                f"   📆 {jadwal['tanggal_event'].strftime('%d-%m-%Y')}\n"
                f"   ⏰ {jadwal['tanggal_event'].strftime('%H:%M')}\n"
                f"   🔔 Pengingat: "
            )
            reminders = []
            if jadwal['ingatkan_h12']:
                reminders.append("H-12 jam")
            if jadwal['ingatkan_h4']:
                reminders.append("H-4 jam")
            if jadwal['ingatkan_h1']:
                reminders.append("H-1 jam")
            message += ", ".join(reminders) if reminders else "Tidak ada"
            message += f"\n   {status}\n\n"
        
        message += "Gunakan /stop untuk menghentikan pengingat jadwal tertentu."
        
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error fetching schedules: {e}")
        await update.message.reply_text("❌ Gagal mengambil daftar jadwal. Silakan coba lagi.")
    finally:
        cursor.close()
        conn.close()

async def stop_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_name = get_user_name(chat_id)
    
    if not user_name:
        await update.message.reply_text(
            "Anda belum terdaftar. Silakan ketik /start terlebih dahulu untuk mendaftar."
        )
        return
    
    conn = get_db_connection()
    if conn is None:
        await update.message.reply_text("❌ Gagal terhubung ke database. Silakan coba lagi nanti.")
        return
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            "SELECT id, nama_event, tanggal_event "
            "FROM jadwal WHERE chat_id = %s AND tanggal_event > NOW() AND is_active = 1 ORDER BY tanggal_event",
            (chat_id,)
        )
        jadwals = cursor.fetchall()
        
        if not jadwals:
            await update.message.reply_text(
                f"Halo {user_name}! 🔴\n\n"
                "Tidak ada jadwal aktif yang bisa dihentikan."
            )
            return
        
        # Create inline keyboard with schedule options
        keyboard = []
        for jadwal in jadwals:
            button_text = f"{jadwal['nama_event']} - {jadwal['tanggal_event'].strftime('%d/%m %H:%M')}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"stop_{jadwal['id']}")])
        
        keyboard.append([InlineKeyboardButton("❌ Batal", callback_data="cancel_stop")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"🔴 **Hentikan Pengingat Jadwal**\n\n"
            f"Pilih jadwal yang ingin dihentikan pengingatnya:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error fetching schedules for stop: {e}")
        await update.message.reply_text("❌ Gagal mengambil daftar jadwal. Silakan coba lagi.")
    finally:
        cursor.close()
        conn.close()

async def handle_stop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_stop":
        await query.edit_message_text("❌ Operasi dibatalkan.")
        return
    
    if query.data.startswith("stop_"):
        jadwal_id = int(query.data.split("_")[1])
        chat_id = update.effective_chat.id
        
        conn = get_db_connection()
        if conn is None:
            await query.edit_message_text("❌ Gagal terhubung ke database.")
            return
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Get schedule details first
            cursor.execute(
                "SELECT nama_event, tanggal_event FROM jadwal WHERE id = %s AND chat_id = %s",
                (jadwal_id, chat_id)
            )
            jadwal = cursor.fetchone()
            
            if not jadwal:
                await query.edit_message_text("❌ Jadwal tidak ditemukan.")
                return
            
            # Deactivate the schedule
            cursor.execute(
                "UPDATE jadwal SET is_active = 0 WHERE id = %s AND chat_id = %s",
                (jadwal_id, chat_id)
            )
            conn.commit()
            
            await query.edit_message_text(
                f"✅ **Pengingat dihentikan!**\n\n"
                f"📅 Event: {jadwal['nama_event']}\n"
                f"📆 Tanggal: {jadwal['tanggal_event'].strftime('%d-%m-%Y %H:%M')}\n\n"
                f"Pengingat untuk jadwal ini telah dinonaktifkan.",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error stopping reminder: {e}")
            await query.edit_message_text("❌ Gagal menghentikan pengingat.")
        finally:
            cursor.close()
            conn.close()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_name = get_user_name(chat_id)
    
    greeting = f"Halo {user_name}! " if user_name else "Halo! "
    
    help_text = (
        f"{greeting}📚 **Bantuan Bot Pengingat Jadwal**\n\n"
        "🤖 **Perintah yang tersedia:**\n"
        "• `/start` - Memulai bot dan registrasi nama\n"
        "• `/tambah` - Tambah jadwal baru\n"
        "• `/list` - Lihat daftar jadwal aktif\n"
        "• `/stop` - Hentikan pengingat jadwal\n"
        "• `/help` - Tampilkan bantuan ini\n\n"
        "⏰ **Opsi Pengingat:**\n"
        "• H-12 jam - Pengingat 12 jam sebelum event\n"
        "• H-4 jam - Pengingat 4 jam sebelum event\n"
        "• H-1 jam - Pengingat 1 jam sebelum event\n\n"
        "📝 **Format Input:**\n"
        "• Tanggal: DD-MM-YYYY (contoh: 25-12-2024)\n"
        "• Waktu: HH:MM (contoh: 14:30)\n\n"
        "❓ **Tips:**\n"
        "• Anda bisa memilih kombinasi pengingat\n"
        "• Jadwal yang sudah berlalu akan otomatis hilang\n"
        "• Gunakan `/stop` untuk menonaktifkan pengingat\n"
        "• Bot akan mengirim notifikasi sesuai waktu yang dipilih"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Operasi dibatalkan.")
    return ConversationHandler.END

# Global variable to track if reminders are already running
reminder_running = False

async def check_reminders(app: Application):
    global reminder_running
    if reminder_running:
        return
    
    reminder_running = True
    logger.info("Starting reminder checker...")
    
    while True:
        try:
            now = datetime.now()
            conn = get_db_connection()
            if conn is None:
                logger.error("Cannot connect to database for reminder check")
                await asyncio.sleep(1800)  # Wait 30 minutes before retry
                continue
            
            cursor = conn.cursor(dictionary=True)
            
            # Cek jadwal yang perlu diingatkan H-12 jam (11-13 jam dari sekarang)
            cursor.execute(
                "SELECT id, nama_event, tanggal_event, chat_id "
                "FROM jadwal "
                "WHERE ingatkan_h12 = 1 AND is_active = 1 "
                "AND tanggal_event > NOW() "
                "AND TIMESTAMPDIFF(HOUR, NOW(), tanggal_event) BETWEEN 11 AND 13"
            )
            h12_jadwals = cursor.fetchall()
            
            for jadwal in h12_jadwals:
                try:
                    user_name = get_user_name(jadwal['chat_id'])
                    greeting = f"Halo {user_name}! " if user_name else "Halo! "
                    
                    await app.bot.send_message(
                        chat_id=jadwal['chat_id'],
                        text=f"{greeting}⏰ **Peringatan H-12 jam!**\n\n"
                             f"📅 Event: {jadwal['nama_event']}\n"
                             f"🕐 Waktu: {jadwal['tanggal_event'].strftime('%d-%m-%Y %H:%M')}\n\n"
                             f"Jangan lupa persiapkan diri Anda! 🚀",
                        parse_mode='Markdown'
                    )
                    logger.info(f"Sent H-12 reminder for event: {jadwal['nama_event']}")
                except Exception as e:
                    logger.error(f"Failed to send H-12 reminder: {e}")
            
            # Cek jadwal yang perlu diingatkan H-4 jam (3-5 jam dari sekarang)
            cursor.execute(
                "SELECT id, nama_event, tanggal_event, chat_id "
                "FROM jadwal "
                "WHERE ingatkan_h4 = 1 AND is_active = 1 "
                "AND tanggal_event > NOW() "
                "AND TIMESTAMPDIFF(HOUR, NOW(), tanggal_event) BETWEEN 3 AND 5"
            )
            h4_jadwals = cursor.fetchall()
            
            for jadwal in h4_jadwals:
                try:
                    user_name = get_user_name(jadwal['chat_id'])
                    greeting = f"Halo {user_name}! " if user_name else "Halo! "
                    
                    await app.bot.send_message(
                        chat_id=jadwal['chat_id'],
                        text=f"{greeting}🔔 **Peringatan H-4 jam!**\n\n"
                             f"📅 Event: {jadwal['nama_event']}\n"
                             f"🕐 Waktu: {jadwal['tanggal_event'].strftime('%d-%m-%Y %H:%M')}\n\n"
                             f"Event akan segera dimulai! ⏰",
                        parse_mode='Markdown'
                    )
                    logger.info(f"Sent H-4 reminder for event: {jadwal['nama_event']}")
                except Exception as e:
                    logger.error(f"Failed to send H-4 reminder: {e}")
            
            # Cek jadwal yang perlu diingatkan H-1 jam (45-75 menit dari sekarang)
            cursor.execute(
                "SELECT id, nama_event, tanggal_event, chat_id "
                "FROM jadwal "
                "WHERE ingatkan_h1 = 1 AND is_active = 1 "
                "AND tanggal_event > NOW() "
                "AND TIMESTAMPDIFF(MINUTE, NOW(), tanggal_event) BETWEEN 45 AND 75"
            )
            h1_jadwals = cursor.fetchall()
            
            for jadwal in h1_jadwals:
                try:
                    user_name = get_user_name(jadwal['chat_id'])
                    greeting = f"Halo {user_name}! " if user_name else "Halo! "
                    
                    await app.bot.send_message(
                        chat_id=jadwal['chat_id'],
                        text=f"{greeting}🚨 **Peringatan H-1 jam!**\n\n"
                             f"📅 Event: {jadwal['nama_event']}\n"
                             f"🕐 Waktu: {jadwal['tanggal_event'].strftime('%d-%m-%Y %H:%M')}\n\n"
                             f"Event akan dimulai dalam 1 jam! Bersiaplah! 🔥",
                        parse_mode='Markdown'
                    )
                    logger.info(f"Sent H-1 reminder for event: {jadwal['nama_event']}")
                except Exception as e:
                    logger.error(f"Failed to send H-1 reminder: {e}")
                    
        except Exception as e:
            logger.error(f"Error in reminder checker: {e}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
        
        await asyncio.sleep(1800)  # Check every 30 minutes

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    if update and update.message:
        await update.message.reply_text('Maaf, terjadi kesalahan. Silakan coba lagi.')

def run_scheduler(app: Application):
    """Run the scheduler in a separate thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(check_reminders(app))
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
    finally:
        loop.close()

def main():
    # Validate environment variables
    if not TOKEN:
        logger.error("BOT_TOKEN not found in environment variables")
        return
    
    # Initialize database
    if not init_database():
        logger.error("Failed to initialize database")
        return
    
    # Create the Application
    application = Application.builder().token(TOKEN).build()
    
    # Conversation handler for user registration
    registration_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Conversation handler for adding schedule
    schedule_handler = ConversationHandler(
        entry_points=[CommandHandler('tambah', tambah_jadwal)],
        states={
            GET_EVENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_name)],
            GET_EVENT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_date)],
            GET_EVENT_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_time)],
            GET_REMINDER_CHOICE: [CallbackQueryHandler(save_jadwal)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Register handlers
    application.add_handler(registration_handler)
    application.add_handler(schedule_handler)
    application.add_handler(CommandHandler("list", list_jadwal))
    application.add_handler(CommandHandler("stop", stop_reminder))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(handle_stop_callback, pattern="^(stop_|cancel_stop)"))
    application.add_error_handler(error_handler)
    
    # Test database connection
    conn = get_db_connection()
    if conn:
        logger.info("Database connection successful")
        conn.close()
    else:
        logger.error("Failed to connect to database")
        return
    
    # Start the scheduler in a separate thread
    scheduler_thread = Thread(target=run_scheduler, args=(application,), daemon=True)
    scheduler_thread.start()
    
    logger.info("Bot started successfully")
    
    # Run the bot
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()