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
ALLOWED_USER_IDS = os.getenv("ALLOWED_USER_IDS", "").split(",")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Browser command mapping
BROWSER_COMMANDS = {
    "chrome": "google-chrome",
    "kde": "kde",
    "chromium": "chromium",
    "edge": "microsoft-edge",
    "opera": "opera",
    "vivaldi": "vivaldi",
    "ungoogled_chromium": "ungoogled-chromium",
    "brave": "brave",
    "firefox": "firefox",
    "latest": "latest",
    "remmina": "remmina",
    "xfce": "xfce",
    "vlc": "vlc"
}



def is_authorized(user_id: int) -> bool:
    return str(user_id) in ALLOWED_USER_IDS

def run_curl_command(command: str) -> str:
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        return f"✅ Successfully executed!\n{result.stdout}"
    else:
        return f"❌ Error occurred!\nExit Code: {result.returncode}\n{result.stderr}"

async def start_browser(update: Update, context):
    if not is_authorized(update.message.from_user.id):
        await update.message.reply_text("⛔ You are not authorized to use this bot.")
        return
    
    command_text = update.message.text.split("/")[1]  # Extract command name
    image_name = BROWSER_COMMANDS.get(command_text, None)
    if not image_name:
        await update.message.reply_text("❌ Invalid command!")
        return
    
    chat_id = update.message.chat.id
    print(f'Chat ID: {chat_id}')  # Get chat ID dynamically
    
    command = f'''
    curl -L -X POST \
      -H "Accept: application/vnd.github+json" \
      -H "Authorization: Bearer {GITHUB_TOKEN}" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      https://api.github.com/repos/dikeckaan/neko-actions/actions/workflows/telegram-bot.yml/dispatches \
      -d '{{"ref": "master", "inputs": {{ "chatid": "{chat_id}", "image": "{image_name}", "bottoken": "{BOT_TOKEN}" }} }}'
    '''
    print(f'Generated command: {command}')
    response = run_curl_command(command)
    await update.message.reply_text(response)

async def stop_machine(run_id: str, query):
    command = f'''
    curl -L -X POST \
      -H "Accept: application/vnd.github+json" \
      -H "Authorization: Bearer {GITHUB_TOKEN}" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      https://api.github.com/repos/dikeckaan/neko-actions/actions/runs/{run_id}/cancel
    '''
    response = run_curl_command(command)
    await query.edit_message_text(f"🟠 Machine with Run ID {run_id} is being stopped!\n{response}")

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




async def actions_list(update: Update, context):
    """Lists available commands for starting a browser or other applications."""
    command_list = "\n".join([f"/{cmd}" for cmd in BROWSER_COMMANDS.keys()])
    response_text = (
        "You can run these commands in this chat:\n\n"
        f"{command_list}\n\n"
        "To run a command, simply type it in the chat (e.g., `/chrome`)."
    )
    await update.message.reply_text(response_text)
    return
    
    
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers dynamically for all browsers
    for command in BROWSER_COMMANDS.keys():
        app.add_handler(CommandHandler(command, start_browser))
    
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(CommandHandler("actionslist", actions_list))
    
    app.run_polling()

if __name__ == "__main__":
    main()
