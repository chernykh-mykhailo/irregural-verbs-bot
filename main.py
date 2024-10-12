import logging
import random
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters
from config import TELEGRAM_TOKEN  # Import token from configuration file
from irregular_verbs import irregular_verbs  # Import irregular verbs

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Hi! I am your Irregular Verb Learning Bot. '
                                    'Use /verb <base_form> to get the past tense '
                                    'and past participle of a verb. '
                                    'Use /verbs to get the list of all irregular verbs. '
                                    'Use /random to get a random irregular verb. '
                                    'Use /quiz to start a quiz on irregular verbs. '
                                    'Use /big_quiz to start a 2-minute quiz on irregular verbs. '
                                    'Use /stop_quiz to stop the ongoing quiz.')

async def verb(update: Update, context: CallbackContext) -> None:
    if context.args:
        base_form = context.args[0].lower()
        if base_form in irregular_verbs:
            past_tense, past_participle = irregular_verbs[base_form]
            await update.message.reply_text(f'{base_form.capitalize()}: Past Tense - {past_tense}, Past Participle - {past_participle}')
        else:
            await update.message.reply_text('Sorry, I do not know this verb.')
    else:
        await update.message.reply_text('Please provide a base form of a verb.')

async def verbs(update: Update, context: CallbackContext) -> None:
    verbs_list = "Base Form | Past Tense | Past Participle\n"
    verbs_list += "----------|------------|----------------\n"
    for base_form, (past_tense, past_participle) in irregular_verbs.items():
        verbs_list += f'{base_form} | {past_tense} | {past_participle}\n'
    await update.message.reply_text(f'Here are the irregular verbs:\n{verbs_list}')

async def random_verb(update: Update, context: CallbackContext) -> None:
    base_form, (past_tense, past_participle) = random.choice(list(irregular_verbs.items()))
    await update.message.reply_text(f'Random Verb: {base_form.capitalize()} - {past_tense} - {past_participle}')

async def quiz(update: Update, context: CallbackContext) -> None:
    base_form, (past_tense, past_participle) = random.choice(list(irregular_verbs.items()))
    context.user_data['quiz_answer'] = (past_tense, past_participle)
    context.user_data['quiz_base_form'] = base_form
    await update.message.reply_text(f'What are the past tense and past participle of "{base_form}"?')

async def handle_message(update: Update, context: CallbackContext) -> None:
    if 'quiz_answer' in context.user_data:
        correct_past_tense, correct_past_participle = context.user_data['quiz_answer']
        user_response = update.message.text.lower().strip().split()
        if len(user_response) == 2:
            user_past_tense, user_past_participle = user_response
            if user_past_tense == correct_past_tense and user_past_participle == correct_past_participle:
                await update.message.reply_text('Correct!')
            else:
                await update.message.reply_text(f'Incorrect. The correct answers are: Past Tense - {correct_past_tense}, Past Participle - {correct_past_participle}')
        else:
            await update.message.reply_text('Please provide both the past tense and past participle.')
        del context.user_data['quiz_answer']
        del context.user_data['quiz_base_form']

async def big_quiz(update: Update, context: CallbackContext) -> None:
    context.user_data['big_quiz_active'] = True
    context.user_data['remaining_verbs'] = list(irregular_verbs.items())
    random.shuffle(context.user_data['remaining_verbs'])  # Shuffle the list to ensure randomness
    await update.message.reply_text('Starting a 2-minute quiz. Answer as many as you can!')

    async def end_quiz():
        await asyncio.sleep(120)
        if context.user_data.get('big_quiz_active'):
            context.user_data['big_quiz_active'] = False
            await update.message.reply_text('Time is up! The quiz has ended.')

    asyncio.create_task(end_quiz())
    await ask_next_verb(update, context)

async def stop_quiz(update: Update, context: CallbackContext) -> None:
    if context.user_data.get('big_quiz_active'):
        context.user_data['big_quiz_active'] = False
        await update.message.reply_text('The quiz has been stopped.')

async def ask_next_verb(update: Update, context: CallbackContext) -> None:
    if context.user_data.get('big_quiz_active') and context.user_data['remaining_verbs']:
        base_form, (past_tense, past_participle) = context.user_data['remaining_verbs'].pop(0)
        context.user_data['quiz_answer'] = (past_tense, past_participle)
        context.user_data['quiz_base_form'] = base_form
        await update.message.reply_text(f'What are the past tense and past participle of "{base_form}"?')
    elif not context.user_data['remaining_verbs']:
        context.user_data['big_quiz_active'] = False
        await update.message.reply_text('You have answered all the verbs! The quiz has ended.')

async def handle_big_quiz_message(update: Update, context: CallbackContext) -> None:
    if context.user_data.get('big_quiz_active') and 'quiz_answer' in context.user_data:
        correct_past_tense, correct_past_participle = context.user_data['quiz_answer']
        user_response = update.message.text.lower().strip().split()
        if len(user_response) == 2:
            user_past_tense, user_past_participle = user_response
            if (user_past_tense in correct_past_tense.split('/') and user_past_participle == correct_past_participle):
                await update.message.reply_text('Correct!')
                await ask_next_verb(update, context)
            else:
                await update.message.reply_text(f'Incorrect. The correct answers are: Past Tense - {correct_past_tense}, Past Participle - {correct_past_participle}')
                await ask_next_verb(update, context)
        else:
            await update.message.reply_text('Please provide both the past tense and past participle.')


def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("verb", verb))
    application.add_handler(CommandHandler("verbs", verbs))
    application.add_handler(CommandHandler("random", random_verb))
    application.add_handler(CommandHandler("quiz", quiz))
    application.add_handler(CommandHandler("big_quiz", big_quiz))
    application.add_handler(CommandHandler("stop_quiz", stop_quiz))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_big_quiz_message))

    application.run_polling()

if __name__ == '__main__':
    main()