import requests
import traceback
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, ConversationHandler, CallbackQueryHandler, MessageHandler, Filters

# Set your Telegram bot token and GitHub access token here
TELEGRAM_TOKEN = '6689453018:AAH21FYYGFqaXc0wPRWGhFnhLxF5gl5LCdE'
GITHUB_ACCESS_TOKEN = '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'

#kindly note that these are old tokens and do not work at the moment

# Set your GitHub username
GITHUB_USERNAME = 'Emperor-Grey'
# GitHub API endpoint for getting the user's repositories
GITHUB_API_ENDPOINT = f'https://api.github.com/users/{GITHUB_USERNAME}/repos'

# Bot states
SELECT_REPO = 1

# Command handler for the '/start' command
def start(update: Update, context: CallbackContext):
    update.message.reply_text('Welcome to the APK download bot! Use /download to see your repositories.')

# Command handler for the '/download' command
def download(update: Update, context: CallbackContext):
    # Fetch the user's repositories from GitHub
    headers = {'Authorization': f'token {GITHUB_ACCESS_TOKEN}'}
    response = requests.get(GITHUB_API_ENDPOINT, headers=headers)

    if response.status_code == 200:
        repositories_data = response.json()
        buttons = [
            [
                InlineKeyboardButton(repo['name'], callback_data=str(repo['name']))
            ] for repo in repositories_data if repo['private'] is False  # Filter out private repositories
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        update.message.reply_text('Select a repository:', reply_markup=reply_markup)

        return SELECT_REPO
    else:
        update.message.reply_text('Failed to fetch repository information. Please try again later.')

# Callback handler for repository selection
def select_repo(update: Update, context: CallbackContext):
    query = update.callback_query
    repo_name = query.data
    query.edit_message_text(f'You selected: {repo_name}\nKindly Wait Few Minutes')

    # Get the latest release for the selected repository
    headers = {'Authorization': f'token {GITHUB_ACCESS_TOKEN}'}
    release_url = f'https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/releases/latest'
    response = requests.get(release_url, headers=headers)

    if response.status_code == 200:
        try:
            release_data = response.json()
            assets = release_data['assets']

            for asset in assets:
                download_url = asset['browser_download_url']
                if download_url.endswith('.apk'):
                    apk_response = requests.get(download_url)
                    if apk_response.status_code == 200:
                        # Get the actual filename from the asset data
                        filename = asset['name']
                        # Send the APK file as a document with the actual filename
                        bot = context.bot
                        bot.send_document(update.effective_chat.id, apk_response.content, filename=filename)
                        return ConversationHandler.END
                    else:
                        query.message.reply_text('Failed to download the APK file.')
                        return ConversationHandler.END

            query.message.reply_text('No APK file found in the latest release.')
        except Exception as e:
            traceback.print_exc()  # Print the traceback for debugging purposes
            query.message.reply_text(f'Error occurred while processing the release information: {str(e)}')
    else:
        query.message.reply_text('The Master has provided an Apk File Yet')

    return ConversationHandler.END

# Default handler for any other commands/messages
def default_handler(update: Update, context: CallbackContext):
    update.message.reply_text("Unknown command. Type /download or /start to use the bot")

# Main function to run the bot
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Add command handlers
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('download', download))

    # Add conversation handler with the select_repo function as the entry point
    conversation_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_repo, pattern='^.*$')],
        states={},
        fallbacks=[],
    )
    dispatcher.add_handler(conversation_handler)

    # Add default handler for any other commands/messages
    dispatcher.add_handler(MessageHandler(~Filters.command, default_handler))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
