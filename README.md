# Bot-Pengingat-v1
Bot Ini Diciptakan Oleh Rifqi Noval H
# 🤖 Bot Pengingat Jadwal Telegram

Bot Telegram yang membantu Anda mengatur dan mendapatkan pengingat untuk jadwal penting. Bot ini dilengkapi dengan sistem pengingat multi-level dan interface yang user-friendly.

## ✨ Fitur Utama

### 🔐 **Sistem Registrasi**
- Registrasi nama pengguna saat pertama kali menggunakan bot
- Personalisasi pesan dengan nama pengguna
- Validasi dan penyimpanan data user yang aman

### 📅 **Manajemen Jadwal**
- Tambah jadwal dengan input terpisah untuk tanggal dan waktu
- Format input yang mudah dipahami (DD-MM-YYYY untuk tanggal, HH:MM untuk waktu)
- Validasi otomatis untuk memastikan jadwal di masa depan
- Tampilan daftar jadwal yang terorganisir dengan status aktif/non-aktif

### ⏰ **Sistem Pengingat Multi-Level**
- **H-12 jam**: Pengingat 12 jam sebelum event
- **H-4 jam**: Pengingat 4 jam sebelum event  
- **H-1 jam**: Pengingat 1 jam sebelum event
- Kombinasi pengingat yang dapat disesuaikan
- Pilihan untuk tidak menggunakan pengingat

### 🛑 **Kontrol Pengingat**
- Fitur stop/pause pengingat untuk jadwal tertentu
- Interface interaktif dengan tombol untuk memilih jadwal
- Status aktif/non-aktif untuk setiap jadwal

### 🎯 **Interface User-Friendly**
- Pesan dengan emoji dan formatting menarik
- Tombol interaktif untuk kemudahan navigasi
- Validasi input dengan pesan error yang jelas
- Bantuan lengkap dengan command `/help`

## 🚀 Cara Menggunakan

### **Command yang Tersedia:**
- `/start` - Memulai bot dan registrasi nama
- `/tambah` - Tambah jadwal baru
- `/list` - Lihat daftar jadwal aktif
- `/stop` - Hentikan pengingat jadwal
- `/help` - Tampilkan bantuan lengkap
- `/cancel` - Batalkan operasi yang sedang berjalan

### **Alur Penggunaan:**
1. **Registrasi**: Ketik `/start` dan masukkan nama Anda
2. **Tambah Jadwal**: 
   - Ketik `/tambah`
   - Masukkan nama event
   - Masukkan tanggal (format: DD-MM-YYYY)
   - Masukkan waktu (format: HH:MM)
   - Pilih jenis pengingat yang diinginkan
3. **Lihat Jadwal**: Ketik `/list` untuk melihat semua jadwal aktif
4. **Hentikan Pengingat**: Ketik `/stop` dan pilih jadwal yang ingin dihentikan

### **Format Input:**
- **Tanggal**: DD-MM-YYYY (contoh: 25-12-2024)
- **Waktu**: HH:MM (contoh: 14:30, 09:15)

## 🛠️ Instalasi dan Setup

### **Prerequisites:**
- Python 3.8 atau lebih tinggi
- MySQL Database
- Bot Token dari BotFather Telegram

### **Instalasi Lokal:**

1. **Clone repository:**
   ```bash
   git clone https://github.com/yourusername/telegram-reminder-bot.git
   cd telegram-reminder-bot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup environment variables:**
   Buat file `.env` dan isi dengan:
   ```env
   BOT_TOKEN=your_bot_token_here
   DB_HOST=localhost
   DB_USER=your_db_username
   DB_PASS=your_db_password
   DB_NAME=your_db_name
   ```

4. **Setup Database:**
   ```sql
   CREATE DATABASE your_db_name;
   ```

5. **Jalankan bot:**
   ```bash
   python bot.py
   ```

### **Mendapatkan Bot Token:**
1. Chat dengan [@BotFather](https://t.me/BotFather) di Telegram
2. Ketik `/newbot`
3. Ikuti instruksi untuk membuat bot baru
4. Simpan token yang diberikan

## 🗄️ Struktur Database

Bot ini menggunakan dua tabel utama:

### **Tabel `users`:**
- `id` (INT, AUTO_INCREMENT, PRIMARY KEY)
- `chat_id` (BIGINT, UNIQUE, NOT NULL)
- `name` (VARCHAR(255), NOT NULL)
- `created_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)

### **Tabel `jadwal`:**
- `id` (INT, AUTO_INCREMENT, PRIMARY KEY)
- `nama_event` (VARCHAR(255), NOT NULL)
- `tanggal_event` (DATETIME, NOT NULL)
- `chat_id` (BIGINT, NOT NULL)
- `ingatkan_h12` (TINYINT(1), DEFAULT 0)
- `ingatkan_h4` (TINYINT(1), DEFAULT 0)
- `ingatkan_h1` (TINYINT(1), DEFAULT 0)
- `is_active` (TINYINT(1), DEFAULT 1)
- `created_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)

## 🌐 Deploy ke Production

### **Opsi Hosting:**

#### **1. Railway (Gratis & Mudah):**
- Daftar di [railway.app](https://railway.app)
- Connect repository GitHub
- Tambah MySQL database
- Set environment variables
- Deploy otomatis!

#### **2. VPS (Recommended untuk Production):**
- Gunakan VPS seperti DigitalOcean, Linode, atau Vultr
- Setup dengan systemd service untuk auto-restart
- Monitoring dengan logs dan health checks

#### **3. Heroku:**
- Deploy dengan Procfile
- Gunakan add-on database seperti ClearDB atau JawsDB
- Scale worker process

#### **4. Docker:**
- Build dengan Dockerfile yang disediakan
- Deploy dengan docker-compose
- Mudah untuk scaling dan maintenance

### **Environment Variables untuk Production:**
```env
BOT_TOKEN=your_production_bot_token
DB_HOST=your_production_db_host
DB_USER=your_production_db_user
DB_PASS=your_production_db_password
DB_NAME=your_production_db_name
```

## 📊 Fitur Sistem

### **Auto-Initialization:**
- Database tables dibuat otomatis saat pertama kali dijalankan
- Migration otomatis untuk kolom baru
- Backward compatibility untuk database existing

### **Error Handling:**
- Comprehensive error logging
- Graceful failure handling
- User-friendly error messages
- Auto-retry untuk database connections

### **Performance:**
- Efficient database queries
- Async/await pattern untuk non-blocking operations
- Connection pooling untuk database
- Optimized reminder checking (setiap 30 menit)

### **Security:**
- Environment variables untuk sensitive data
- Input validation dan sanitization
- SQL injection prevention
- Rate limiting ready

## 🔧 Development

### **Struktur Project:**
```
telegram-reminder-bot/
├── bot.py              # Main bot file
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (tidak di-commit)
├── .env.example       # Template environment variables
├── README.md          # Dokumentasi
├── Dockerfile         # Docker configuration
├── docker-compose.yml # Docker compose setup
└── .gitignore         # Git ignore file
```

### **Menambah Fitur Baru:**
1. Fork repository
2. Buat branch baru: `git checkout -b feature/nama-fitur`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push branch: `git push origin feature/nama-fitur`
5. Submit Pull Request

### **Testing:**
- Test bot secara lokal sebelum deploy
- Test dengan berbagai skenario input
- Verifikasi database operations
- Test error handling

## 📈 Monitoring dan Maintenance

### **Logs:**
- Bot logging tersimpan di console dan file
- Database operation logging
- Error tracking dan debugging
- Performance monitoring

### **Health Checks:**
- Automatic health monitoring
- Database connection checks
- Memory usage monitoring
- Uptime tracking

### **Backup:**
- Regular database backups
- Environment configuration backup
- Code versioning dengan Git

## 🤝 Contributing

Kontribusi sangat diterima! Silakan:

1. Fork project ini
2. Buat feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Buka Pull Request

## 📝 License

Project ini menggunakan MIT License. Lihat file `LICENSE` untuk detail lengkap.

## 🆘 Support

Jika Anda mengalami masalah atau memiliki pertanyaan:

1. **Issues**: Buat issue di GitHub repository
2. **Documentation**: Baca dokumentasi lengkap di README
3. **Community**: Join grup Telegram untuk diskusi

## 🚀 Roadmap

### **Future Features:**
- [ ] Multi-language support (Indonesia, English)
- [ ] Recurring events (harian, mingguan, bulanan)
- [ ] Event categories dan tags
- [ ] Export/import jadwal
- [ ] Admin panel untuk monitoring
- [ ] Analytics dan usage statistics
- [ ] Integration dengan Google Calendar
- [ ] Webhook mode untuk better performance
- [ ] Rich text formatting untuk event description
- [ ] Time zone support
- [ ] Bulk operations (delete multiple schedules)
- [ ] Event sharing antar users
- [ ] Custom reminder times
- [ ] Email notifications backup
- [ ] Mobile app companion

## 🏷️ Version History

### **v1.0.0** (Current)
- ✅ Basic reminder functionality
- ✅ User registration system
- ✅ Multi-level reminders (H-12, H-4, H-1)
- ✅ Schedule management (add, list, stop)
- ✅ MySQL database integration
- ✅ Error handling dan logging
- ✅ Production-ready deployment

---

**Dibuat dengan ❤️ untuk membantu Anda mengatur jadwal dengan lebih baik!**

*Bot ini akan terus dikembangkan dengan fitur-fitur baru. Stay tuned!* 🚀
