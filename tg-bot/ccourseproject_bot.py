from copyreg import constructor

from sc_client.constants.sc_types import sc_type
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, \
    CallbackQueryHandler, Application
import re
from sc_client.models import ScLinkContentType, ScConstruction, ScLinkContent, ScTemplate, ScTemplateResult, ScAddr
from sc_kpm.identifiers import CommonIdentifiers
from sc_kpm import ScKeynodes
from sc_kpm.utils import create_link, get_link_content_data, check_edge
from sc_kpm.utils.action_utils import execute_agent, get_action_answer
from sc_client.constants import sc_types
from sc_client.client import create_elements, connect, disconnect, template_search, get_links_by_content, \
    template_generate
from sc_client.client import template_generate
from sc_kpm.sc_sets import ScStructure
import json

url = "ws://localhost:8090/ws_json"
connect(url)


def get_nika_response(user_message: str) -> str:
    lang = ScKeynodes.resolve('lang_ru', sc_types.NODE_CONST_CLASS)
    text = ScKeynodes.resolve('concept_text_file', sc_types.NODE_CONST_CLASS)
    concept_dialog = ScKeynodes.resolve('concept_dialog', sc_types.NODE_CONST_CLASS)

    concept_dialog = ScKeynodes.resolve('concept_dialog', sc_types.NODE_CONST_CLASS)
    template = ScTemplate()
    dialog_template = ScTemplate()
    dialog_template.triple(
        concept_dialog,
        sc_types.EDGE_ACCESS_VAR_POS_PERM,
        sc_types.NODE_VAR >> "_dialog")
    search_results = template_search(dialog_template)
    dialog = search_results[0].get("_dialog")
    if (dialog.is_valid() == 0):
        dialog_construction = ScConstruction()
        dialog_construction.create_node(sc_types.NODE_CONST, 'dialog')
        dialog = create_elements(dialog_construction)[0]
        template.triple(
            concept_dialog,
            sc_types.EDGE_ACCESS_VAR_POS_PERM,
            dialog)
        print('3')
    construction = ScConstruction()  # Create link for example
    construction.create_link(sc_types.LINK_CONST, ScLinkContent(user_message, ScLinkContentType.STRING))
    message_link = create_elements(construction)[0]

    template = ScTemplate()
    template.triple(
        lang,
        sc_types.EDGE_ACCESS_VAR_POS_PERM,
        message_link
    )
    template.triple(
        text,
        sc_types.EDGE_ACCESS_VAR_POS_PERM,
        message_link
    )
    template_generate(template)

    action_result, is_successfully = execute_agent(arguments={message_link: False, dialog: False},
                                                   concepts=["question", 'action_reply_to_message'], wait_time=3)
    if is_successfully:
        response = get_action_answer(action_result)
        response_text = get_system_answer(response)
    else:
        response_text = "Я не могу ответить на ваш вопрос"

    return response_text


def get_system_answer(action_result: ScAddr) -> str:
    message = ScKeynodes.resolve('concept_message', sc_types.NODE_CONST_CLASS)
    nrel_reply = ScKeynodes.resolve('nrel_reply', sc_types.NODE_CONST_NOROLE)
    nrel_translation = ScKeynodes.resolve('nrel_sc_text_translation', sc_types.NODE_CONST_NOROLE)
    template = ScTemplate()
    template.triple(
        action_result,
        sc_types.EDGE_ACCESS_VAR_POS_PERM,
        sc_types.NODE_VAR >> "_message")
    template.triple(
        message,
        sc_types.EDGE_ACCESS_VAR_POS_PERM,
        "_message")
    template.triple_with_relation(
        "_message",
        sc_types.EDGE_D_COMMON_VAR,
        "_answer_message",
        sc_types.EDGE_ACCESS_VAR_POS_PERM,
        nrel_reply)
    template.triple_with_relation(
        sc_types.NODE_VAR >> "_tuple",
        sc_types.EDGE_D_COMMON_VAR,
        "_answer_message",
        sc_types.EDGE_ACCESS_VAR_POS_PERM,
        nrel_translation)
    template.triple(
        "_tuple",
        sc_types.EDGE_ACCESS_VAR_POS_PERM,
        sc_types.LINK_VAR >> "_link")

    search_results = template_search(template)
    answer_link = search_results[0].get("_link")

    answer_text = get_link_content_data(answer_link)
    return answer_text


# Функция, которая будет вызвана при старте бота (/start)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = '''
    ㅤ\n
    Добро пожаловать в NIKA! 

Мы рады видеть вас в нашей системе. Здесь вы сможете легко общаться с ситемой через интерфейс телеграм-бота.

Если у вас есть вопросы или нужна помощь, не стесняйтесь обращаться. Я всегда готова помочь!\n
    ㅤ\n
    '''
    await update.message.reply_text(text, parse_mode='html')


# Функция для обработки текстовых сообщений с отправкой запроса в NIKA
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    # Получаем ответ от системы NIKA
    nika_response = get_nika_response(user_message)
    # Отправляем ответ пользователю
    await update.message.reply_text(nika_response)


# Функция для команды /info — предоставляет информацию о системе NIKA
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    info_text = (
        "Сюда я добавлю информацию о системе NIKA"
    )
    await update.message.reply_text(info_text)


# Основная функция для запуска бота
def main():
    # Вставьте свой токен, полученный от BotFather
    TOKEN = '7725642650:AAHYT-_c2JUgAAMCTduGImqxK8qbRyYAZlc'

    # Создаем объект приложения
    application = Application.builder().token(TOKEN).build()

    # Регистрируем обработчики команд и сообщений
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("info", info))  # Добавляем команду /info
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    application.run_polling()


if __name__ == "__main__":
    main()
