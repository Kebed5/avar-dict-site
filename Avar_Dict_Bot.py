import logging
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avar_dict_site.settings')
import django
django.setup()
import asyncio
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler,
)
from asgiref.sync import sync_to_async
from django.db.models import Q
from django.contrib.postgres.search import TrigramSimilarity
from deep_translator import GoogleTranslator
from dictapp.models import Entry, SuggestedEntry
from telegram.constants import ParseMode
from telegram import File
from dictapp.models import Entry, AudioEntry
from django.core.files.base import ContentFile
import aiohttp


# ✅ Set up environment
nest_asyncio.apply()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avar_dict_site.settings')
django.setup()

# 📜 Enable logging
logging.basicConfig(level=logging.INFO)

# Default user language pairs, e.g. {user_id: 'avar-rus'}
user_lang_pairs = {}
user_contributions = {}
user_audio_contributions = {}

# 🚀 /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "👋 *Hello!*\n\n"
        "Send me a word in Avar, Russian, or English.\n"
        "I'll try to find it in the dictionary.\n\n"
        "Use /help to see all options."
    )
    await update.message.reply_text(welcome)

# 🚀 /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
    "ℹ️ *How to use this bot:*\n\n"
    "1. Send a word to look it up.\n"
    "2. Set your translation direction using the buttons below or:\n"
    "`/setpair avar-rus`, `/setpair rus-avar`, `/setpair avar-eng`, `/setpair eng-avar`\n\n"
    "📝 Want to suggest a new word? Use /contribute and follow the steps.\n\n"
    "Use /start to reset or /help to see this again.\n"
    "🎤 Want to add pronunciation? Use /contribute_audio to send a recording.\n\n"
)

    keyboard = [
    [
        InlineKeyboardButton("Avar → Russian", callback_data='avar-rus'),
        InlineKeyboardButton("Russian → Avar", callback_data='rus-avar'),
    ],
    [
        InlineKeyboardButton("Avar → English", callback_data='avar-eng'),
        InlineKeyboardButton("English → Avar", callback_data='eng-avar'),
    ],
    [
        InlineKeyboardButton("📝 Suggest a Word", callback_data='start-contribution')
    ]
]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(help_text, reply_markup=reply_markup)

# 🔁 /setpair command
async def setpair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🔁 Usage: /setpair avar-rus, rus-avar, avar-eng, eng-avar")
        return
    pair = context.args[0].lower()
    if pair not in ["avar-rus", "rus-avar", "avar-eng", "eng-avar"]:
        await update.message.reply_text("❌ Invalid pair. Choose from: avar-rus, rus-avar, avar-eng, eng-avar")
        return
    user_lang_pairs[update.effective_user.id] = pair
    await update.message.reply_text(f"✅ Translation direction set to *{pair}*")

# 📌 Inline button callback
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'start-contribution':
        await contribute(update, context)
        return

    elif query.data == 'contrib_word':
        user_contributions[user_id] = {'step': 'avar'}
        await query.edit_message_text("✍️ Please enter the Avar word you'd like to contribute:")
        return

    elif query.data == 'contrib_voice':
        user_audio_contributions[user_id] = {"step": "word"}
        await query.edit_message_text("🎤 Please type the Avar word you want to record audio for:")
        return

    elif query.data == 'contrib_both':
        user_contributions[user_id] = {'step': 'avar', 'include_voice': True}
        await query.edit_message_text("📝 Great! Start by entering the Avar word:")
        return

    # Handle translation direction
    if query.data in ['avar-rus', 'rus-avar', 'avar-eng', 'eng-avar']:
        user_lang_pairs[user_id] = query.data
        await query.edit_message_text(f"✅ Translation pair set to *{query.data}*")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id  
    query = update.message.text.strip()
    print(f"📥 {user_id}: {query}")
    pair = user_lang_pairs.get(user_id, "avar-rus")

    @sync_to_async
    def search_entries():
        if pair == "avar-rus":
            return list(Entry.objects.annotate(
                similarity=TrigramSimilarity("avar_word", query)
            ).filter(similarity__gt=0.3).order_by("-similarity")[:10])
        elif pair == "rus-avar":
            return list(Entry.objects.annotate(
                similarity=TrigramSimilarity("russian_translations", query)
            ).filter(similarity__gt=0.3).order_by("-similarity")[:10])
        elif pair == "avar-eng":
            return list(Entry.objects.annotate(
                similarity=TrigramSimilarity("avar_word", query)
            ).filter(similarity__gt=0.3).order_by("-similarity")[:10])
        elif pair == "eng-avar":
            return list(Entry.objects.annotate(
                similarity=TrigramSimilarity("english_translations", query)
            ).filter(similarity__gt=0.3).order_by("-similarity")[:10])

    matches = await search_entries()

    if matches:
        if pair in ["avar-rus", "rus-avar"]:
            results = "\n".join([f"📘 {e.avar_word} — 🇷🇺 {e.russian_translations}" for e in matches])
        else:
            results = "\n".join([f"📘 {e.avar_word} — 🇬🇧 {e.english_translations}" for e in matches])
    else:
        try:
            target = "ru" if "rus" in pair else "en"
            translated = GoogleTranslator(source='auto', target=target).translate(query)
            results = f"🤖 Not found in dictionary.\nGoogle Translate: *{translated}*"
        except Exception as e:
            results = f"❌ No match and translation failed.\nError: {e}"

    await update.message.reply_text(results)



# /contribute command - unified flow with inline buttons
async def contribute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("✍️ Add Word", callback_data='contrib_word'),
            InlineKeyboardButton("🎤 Add Voice", callback_data='contrib_voice')
        ],
        [
            InlineKeyboardButton("📝 Both", callback_data='contrib_both')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            "🧩 What would you like to contribute?",
            reply_markup=reply_markup
        )
    elif update.callback_query:
        await update.callback_query.message.reply_text(
            "🧩 What would you like to contribute?",
            reply_markup=reply_markup
        )

# /contribute_audio command
async def contribute_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_audio_contributions[user_id] = {"step": "word"}
    await update.message.reply_text("🎤 Please type the Avar word you want to record audio for:")    


@sync_to_async
def save_suggestion(data):
    SuggestedEntry.objects.create(
        user_id=data['user_id'],
        avar_word=data['avar_word'],
        russian_translation=data['russian'],
        english_translation=data.get('english', ''),
        example=data.get('example', '')
    )

@sync_to_async
def save_voice_audio(user_id, avar_word, file_name, audio_bytes):
    try:
        entry = Entry.objects.filter(avar_word__iexact=avar_word).first()
        if entry:
            audio = AudioEntry(
                entry=entry,
                user_id=user_id,
                audio_file=ContentFile(audio_bytes, name=file_name)
            )
            audio.save()
            return True
        return False
    except Exception as e:
        print(f"❌ Error saving audio: {e}")
        return False

@sync_to_async
def save_audio_entry(word, file_id, user_id):
    try:
        entry = Entry.objects.filter(avar_word__iexact=word).first()
        if not entry:
            return False

        # Download the file (you'll need to pass bot context instead to get file)
        return False  # Placeholder – voice already handled above
    except Exception as e:
        print(f"❌ Error saving audio entry: {e}")
        return False


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Ask user for which word this audio belongs to
    if not update.message.voice:
        await update.message.reply_text("❌ No voice message found.")
        return

    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)

    # Ask user what word this voice is for
    await update.message.reply_text("📌 Please tell me which Avar word this recording is for.")
    
    # Save audio to context.user_data temporarily
    context.user_data["pending_voice"] = file.file_id

async def link_audio_to_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    file_id = context.user_data.get("pending_voice")
    if not file_id:
        await update.message.reply_text("ℹ️ No audio pending. Please send a voice message first.")
        return

    file = await context.bot.get_file(file_id)

    # Download the file as bytes
    async with aiohttp.ClientSession() as session:
        async with session.get(file.file_path) as resp:
            audio_bytes = await resp.read()

    file_name = f"{text}_{user_id}.ogg"
    success = await save_voice_audio(user_id, text, file_name, audio_bytes)

    if success:
        await update.message.reply_text("✅ Voice recording saved and linked to the word!")
    else:
        await update.message.reply_text("❌ Couldn't link the recording. Maybe the word isn't in the dictionary.")

    context.user_data.pop("pending_voice", None)

# Handle contribution steps
async def handle_contribution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id not in user_contributions:
        await handle_message(update, context)  # fallback to normal search
        return

    step = user_contributions[user_id]['step']

    # Handle contribution steps
async def handle_contribution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id not in user_contributions:
        await handle_message(update, context)  # fallback to normal search
        return

    step = user_contributions[user_id]['step']

    if step == 'avar':
        user_contributions[user_id]['avar_word'] = text
        user_contributions[user_id]['step'] = 'russian'
        await update.message.reply_text("🇷🇺 Now enter the Russian translation:")
        return

    elif step == 'russian':
        user_contributions[user_id]['russian'] = text
        user_contributions[user_id]['step'] = 'english'
        await update.message.reply_text("🇬🇧 Now enter the English translation (or type 'skip'):")
        return

    elif step == 'english':
        user_contributions[user_id]['english'] = text if text.lower() != 'skip' else ''
        user_contributions[user_id]['step'] = 'example'
        await update.message.reply_text("💬 Add an example sentence (or type 'skip'):")
        return

    elif step == 'example':
        user_contributions[user_id]['example'] = text if text.lower() != 'skip' else ''
        user_contributions[user_id]['user_id'] = user_id
        await save_suggestion(user_contributions[user_id])

        if user_contributions[user_id].get("include_voice"):
            word = user_contributions[user_id]['avar_word']
            user_audio_contributions[user_id] = {"step": "voice", "word": word}
            await update.message.reply_text("🎤 Now send a voice recording of this word:")
        else:
            await update.message.reply_text("✅ Thank you! Your suggestion has been submitted.")

        del user_contributions[user_id]
        return


async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in user_contributions:
        await handle_contribution(update, context)
    elif user_id in user_audio_contributions:
        await handle_audio_contribution(update, context)
    else:
        await handle_message(update, context)


# Handle text and voice
async def handle_audio_contribution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Step 1: User sends the word
    if user_id in user_audio_contributions and user_audio_contributions[user_id]["step"] == "word":
        user_audio_contributions[user_id]["word"] = update.message.text.strip()
        user_audio_contributions[user_id]["step"] = "voice"
        await update.message.reply_text("🎧 Now send a voice recording of that word:")
        return

    # Step 2: User sends the voice message
    if (
        user_id in user_audio_contributions 
        and user_audio_contributions[user_id]["step"] == "voice"
        and update.message.voice
    ):
        word = user_audio_contributions[user_id]["word"]
        file_id = update.message.voice.file_id

        # Save entry
        await save_audio_entry(word, file_id, user_id)
        await update.message.reply_text(f"✅ Thank you! Your voice for *{word}* was saved.")
        del user_audio_contributions[user_id]
        return

    # If not in the flow
    await update.message.reply_text("❗ Please start by using /contribute_audio.")


# 🚀 Main function to run the bot
async def run_bot():
    app = ApplicationBuilder().token("7597669860:AAEczhlKat_HyjW_pVxED4M9xKs1PbSM5Fo").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("setpair", setpair))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(CommandHandler("contribute", contribute))
    app.add_handler(CommandHandler("contribute_audio", contribute_audio))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))
    app.add_handler(MessageHandler(filters.VOICE, handle_audio_contribution))

    print("🤖 Bot is running...")
    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(run_bot())



