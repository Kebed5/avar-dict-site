import logging
import os
import django
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from asgiref.sync import sync_to_async
from django.db.models import Q
from django.contrib.postgres.search import TrigramSimilarity
from deep_translator import GoogleTranslator

# ✅ Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avar_dict_site.settings')
django.setup()

# ✅ Now import models (AFTER setup)
from dictapp.models import Entry

# 📜 Enable logging
logging.basicConfig(level=logging.INFO)

# 📌 Handle /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello! Send me an Avar word and I’ll translate it to Russian.")

# 📌 Handle any Avar, Russian or English word with fuzzy search
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    print(f"📥 Received message: {query}")

    @sync_to_async
    def search_entries():
        return list(
            Entry.objects.annotate(
                similarity=TrigramSimilarity('avar_word', query) +
                           TrigramSimilarity('russian_translations', query) +
                           TrigramSimilarity('english_translations', query)
            ).filter(similarity__gt=0.3).order_by('-similarity')[:10]
        )

    matches = await search_entries()
    
    if matches:
        results = "\n".join([f"📘 {entry.avar_word} — 🇷🇺 {entry.russian_translations}" for entry in matches])
    else:
        # 🔁 Try to translate using Google Translate
        try:
            translated = GoogleTranslator(source='auto', target='ru').translate(query)
            results = f"🤖 Not found in dictionary. Translation: \"{translated}\""
        except Exception as e:
            results = f"❌ No match and translation failed: {e}"

    await update.message.reply_text(results)


# 🚀 Main function to run the bot
def main():
    app = ApplicationBuilder().token("7597669860:AAEczhlKat_HyjW_pVxED4M9xKs1PbSM5Fo").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()




