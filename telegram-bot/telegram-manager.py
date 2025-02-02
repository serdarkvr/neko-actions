import os
import subprocess
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = os.getenv("ALLOWED_USER_ID")

def is_authorized(user_id: int) -> bool:
    return str(user_id) == ALLOWED_USER_ID

def run_curl_command(command: str) -> str:
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        return f"✅ Successfully executed!\n{result.stdout}"
    else:
        return f"❌ Error occurred!\nExit Code: {result.returncode}\n{result.stderr}"

async def newchrome(update: Update, context):
    if not is_authorized(update.message.from_user.id):
        await update.message.reply_text("⛔ You are not authorized to use this bot.")
        return
    
    command = f"""
    curl -L -X POST \
      -H "Accept: application/vnd.github+json" \
      -H "Authorization: Bearer {GITHUB_TOKEN}" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      https://api.github.com/repos/dikeckaan/neko-actions/actions/workflows/neko_with_localtunnel-googlechrome.yml/dispatches \
      -d '{{"ref":"master"}}'
    """
    response = run_curl_command(command)
    await update.message.reply_text(response)

async def stop_machine(run_id: str, query):
    command = f"""
    curl -L -X POST \
      -H "Accept: application/vnd.github+json" \
      -H "Authorization: Bearer {GITHUB_TOKEN}" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      https://api.github.com/repos/dikeckaan/neko-actions/actions/runs/{run_id}/cancel
    """
    response = run_curl_command(command)
    await query.edit_message_text(f"🛑 Machine with Run ID {run_id} is being stopped!\n{response}")

async def button_handler(update: Update, context):
    query = update.callback_query
    if not is_authorized(query.from_user.id):
        await query.answer("⛔ You are not authorized to perform this action.", show_alert=True)
        return
    
    await query.answer()
    run_id = query.data  # The callback_data is the run_id itself
    await stop_machine(run_id, query)

async def message_handler(update: Update, context):
    if not is_authorized(update.message.from_user.id):
        await update.message.reply_text("⛔ You are not authorized to use this bot.")
        return
    
    # Check if the incoming message is from another bot and contains Run ID
    if update.message.reply_markup and update.message.reply_markup.inline_keyboard:
        for row in update.message.reply_markup.inline_keyboard:
            for button in row:
                if "callback_data" in button.to_dict():
                    run_id = button.callback_data  # Extract the run ID from the button
                    context.application.add_handler(CallbackQueryHandler(button_handler, pattern=f"^{run_id}$"))

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("newchrome", newchrome))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    app.run_polling()

if __name__ == "__main__":
    main()
