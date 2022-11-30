from telegram import Bot, BotCommand, Update, InlineKeyboardButton as BT, InlineKeyboardMarkup as MU
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from datetime import datetime
from menu import *
import json
import logging

import random

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)


def open_token():
    with open('token.json', 'r') as token_file:
        token_data = json.load(token_file)
        return token_data['prod']
        # return token_data['dev']


def echo(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(F"ECHO: {update.message.text}")


def make_user_name(update: Update):
    query = update.callback_query
    last_name = ''
    first_name = ''
    if query.from_user.last_name is not None:
        last_name = query.from_user.last_name
    if query.from_user.first_name is not None:
        first_name = query.from_user.first_name

    user_name = last_name + first_name
    if len(user_name) < 1:
        user_name = '점심추천봇'
    else:
        user_name = user_name + '님'

    return user_name


def select_menu(category):
    menu = ''
    if category == 0:
        choice = random.randrange(0, len(menus))
        menu = menus[choice]
    else:
        new_menus = create_new_menus(category)
        choice = random.randrange(0, len(new_menus))
        menu = new_menus[choice]
    return menu


def random_select(category):
    menu = select_menu(category)  # 랜덤으로 메뉴를 뽑는다
    # print('menu', menu)
    weight = menu['weight']
    if weight < 100:  # 메뉴의 가중치가 100보다 작으면 확률 굴림을 한다
        submit = random.randrange(0, 100)
        if weight < submit:
            print('승인 실패: ', menu)
            menu = select_menu(category)  # 확률 굴림 실패시 다시 한번 랜덤으로 메뉴를 뽑는다(2번 연속 뽑혔다면 운명 이겠지)
    return menu


def create_new_menus(category):
    return list((item for item in menus if item['category'] == category))


def start_command_btn_show(update: Update, context: CallbackContext):
    전체랜덤 = BT(text="오늘 점심은 어디로? (완전 랜덤)", callback_data="start_1")
    카테고리선택 = BT(text="끌리는 종류가 있어요!", callback_data="start_2")
    mu = MU(inline_keyboard=[
        [전체랜덤],
        [카테고리선택]
    ])

    context.bot.send_message(
        chat_id=str(update.message.chat.id)
        , text='오지큐 근처 식당 찾기'
        , reply_markup=mu
    )


def category_command_btn_show(update: Update, context: CallbackContext):
    탕 = BT(text="탕,찌개", callback_data="category_1")
    일식 = BT(text="돈까스,일식", callback_data="category_2")
    양식 = BT(text="양식", callback_data="category_3")
    중식 = BT(text="중식", callback_data="category_4")
    아시안 = BT(text="아시안", callback_data="category_5")
    백반 = BT(text="백반,국수", callback_data="category_6")
    분식 = BT(text="분식", callback_data="category_7")
    패스트푸드 = BT(text="패스트푸드", callback_data="category_8")
    mu = MU(inline_keyboard=[
        [탕, 일식, 양식, 중식],
        [아시안, 백반, 패스트푸드, 분식]
    ])

    context.bot.send_message(
        chat_id=str(update.callback_query.message.chat.id)
        , text='드시고 싶은 종류를 선택해주세요'
        , reply_markup=mu
    )


def start_command_list_show(update: Update, context: CallbackContext):
    menu_list = ''
    for i in range(len(menus)):
        if i == len(menus):
            menu_list = menu_list + menus[i]['name']
        else:
            menu_list = menu_list + menus[i]['name'] + '\n'
    context.bot.sendMessage(
        text=f'********** 등록된 가게 목록 *********\n{menu_list}',
        chat_id=str(update.message.chat.id)
    )


def start_btn_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    today = datetime.today().strftime("%Y-%m-%d")

    # user_name = query.from_user.last_name + query.from_user.first_name
    user_name = make_user_name(update)

    if data == 'start_1':
        menu = random_select(0)
        name = menu['name']
        url = menu['url']
        context.bot.sendMessage(
            text=f'************ 완전 무작위! ************\n{today}\n{user_name}이 선택한 오늘의 점심은~ \n{name}!\n{url}',
            chat_id=str(query.message.chat.id)
        )
    elif data == 'start_2':
        category_command_btn_show(update, context)


def category_btn_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    today = datetime.today().strftime("%Y-%m-%d")
    # user_name = query.from_user.last_name + query.from_user.first_name
    user_name = make_user_name(update)
    category_text = ''

    if data == 'category_1':
        category_text = '탕,찌개'
        menu = random_select(1)
    elif data == 'category_2':
        category_text = '돈까스,일식'
        menu = random_select(2)
    elif data == 'category_3':
        category_text = '양식'
        menu = random_select(3)
    elif data == 'category_4':
        category_text = '중식'
        menu = random_select(4)
    elif data == 'category_5':
        category_text = '아시안'
        menu = random_select(5)
    elif data == 'category_6':
        category_text = '백반,국수'
        menu = random_select(6)
    elif data == 'category_7':
        category_text = '분식'
        menu = random_select(7)
    elif data == 'category_8':
        category_text = '패스트푸드'
        menu = random_select(8)

    name = menu['name']
    url = menu['url']
    context.bot.sendMessage(
        text=f'************************************\n{today}\n- {category_text} - 종류 중에서\n{user_name}이 선택한 오늘의 점심은~ \n{name}!\n{url}',
        chat_id=str(query.message.chat.id)
    )


def button_callback_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data

    if data.find('start') > -1:
        start_btn_callback(update, context)
    elif data.find('category') > -1:
        category_btn_callback(update, context)
    else:
        context.bot.sendMessage(
            text='안녕히가세요',
            chat_id=str(query.message.chat.id)
        )


def main():
    token = open_token()
    bot = Bot(token)
    command = [BotCommand("start", "시작"), BotCommand("list", "등록된 가게 목록(등록순)")]
    bot.set_my_commands(command)

    updater = Updater(token)
    dispatcher = updater.dispatcher
    # dispatcher.add_handler(MessageHandler(Filters.text, echo)) # 메시지 핸들러 (유저의 일반 채팅에 반응 하므로 여기선 사용 안함)
    dispatcher.add_handler(CommandHandler('start', start_command_btn_show))  # 커맨드 핸들러
    dispatcher.add_handler(CommandHandler('list', start_command_list_show))  # 커맨드 핸들러
    dispatcher.add_handler(CallbackQueryHandler(button_callback_handler))  # 버튼 클릭 핸들러
    updater.start_polling()
    updater.idle()


main()
