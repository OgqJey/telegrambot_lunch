import threading

from telegram import Bot, BotCommand, Update, InlineKeyboardButton as BT, InlineKeyboardMarkup as MU
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
import datetime
import time
from datetime import timezone
import pytz
import holidays
import re
import requests
from bs4 import BeautifulSoup
from menu import *
import json
import logging
import random

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

global token

kr_holidays = holidays.country_holidays('KR')
# Set timezone to Korea time
korea_tz = pytz.timezone('Asia/Seoul')


def open_token():
    with open('token.json', 'r') as token_file:
        token_data = json.load(token_file)
        return token_data['prod']
        # return token_data['dev']


token = open_token()


def get_weather_text(weather):
    # weather = get_weather()
    if weather is not None:
        temperature = weather['temperature']
        cast = weather['cast']
        emoji = weather_emoji(cast)
        dust = weather['dust']
        weather_txt = f'현재 기온: {temperature}°. \n날씨: {cast}{emoji} / 미세먼지: {dust}'
        return weather_txt
    else:
        return None


def get_weather():
    weather = {}
    오지큐주소 = '서울도곡동'
    url = f'https://search.naver.com/search.naver?sm=tab_hty.top&where=nexearch&query={오지큐주소}날씨'
    response = requests.get(url)
    bs = BeautifulSoup(response.text, "lxml")
    # print('bs', bs)
    weather_info = bs.select("div._today")
    # print('weather_info', weather_info)

    if len(weather_info) > 0:
        temperature_info = bs.select("div.temperature_text > strong")
        # print('temperature_info', temperature_info)
        cast_text = bs.select("div.weather_main")
        # print('cast_text', cast_text)
        dust = bs.select("ul.today_chart_list")[0].text.strip()
        # print(dust)

        if len(temperature_info) > 0 and len(cast_text) > 0:
            temperature_txt = temperature_info[0].text.strip()  # '현재기온15.5도'
            # print(temperature_txt)
            temperature_txt = re.sub(r'[^0-9`.-]', '', temperature_txt)  # '15.5'
            현재기온 = float(temperature_txt)  # 15.5
            # print('temperature', 현재기온)
            날씨 = cast_text[0].text.strip()  # 맑음, 흐림 등
            # print('cast', 날씨)
            미세먼지 = ''
            if dust.find('보통') > -1:
                미세먼지 = '보통'
            elif dust.find('나쁨') > -1:
                미세먼지 = '나쁨'
            elif dust.find('좋음') > -1:
                미세먼지 = '좋음'
            weather['temperature'] = 현재기온
            weather['cast'] = 날씨
            weather['dust'] = 미세먼지
            return weather
    else:
        return None


def weather_emoji(cast):
    emoji = ''
    if cast == '맑음':
        emoji = '☀️'
    elif cast.find('흐림') > -1:
        emoji = '⛅️️'
    elif cast.find('구름많음') > -1:
        emoji = '☁️'
    elif cast.find('비') > -1:
        emoji = '🌧'
    elif cast.find('눈') > -1:
        emoji = '🌨'
    return emoji


def bad_weather(cast):
    if cast.find('비') > -1 or cast.find('눈') > -1:
        return True
    else:
        return False


def select_weather_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    today = datetime.datetime.today().strftime("%Y-%m-%d")
    user_name = make_user_name(update)
    weather = get_weather()
    print('weather', weather)
    weather_txt = get_weather_text(weather)
    temperature = weather['temperature']
    cast = weather['cast']
    dust = weather['dust']
    is_bad_weather = bad_weather(cast)
    menu_list = []
    추가메세지 = ''
    delivery = 2
    if temperature < 4:
        if is_bad_weather:
            if dust.find('나쁨') > -1:
                menu_list = list((item for item in menus if item['distance'] < 250
                                  and not item['weather_category'] == 4 and not item['temperature_category'] == 3))
                delivery = 60
                추가메세지 = '춥고 궂은 '
            else:
                menu_list = list((item for item in menus if item['distance'] < 250
                                  and not item['weather_category'] == 4 and not item['temperature_category'] == 3))
                delivery = 40
        else:
            if dust.find('매우나쁨') > -1:
                menu_list = list((item for item in menus if item['distance'] < 350
                                  and not item['temperature_category'] == 3))
                delivery = 30
                추가메세지 = '미세먼지 심한 '
            else:
                menu_list = list((item for item in menus if item['distance'] < 500
                                  and not item['temperature_category'] == 3))
                delivery = 10
                추가메세지 = ''
    elif temperature > 28:
        if is_bad_weather:
            if dust.find('나쁨') > -1:
                menu_list = list((item for item in menus if item['distance'] < 250))
                delivery = 50
                추가메세지 = '덥고 궂은 '
            else:
                menu_list = list((item for item in menus if item['distance'] < 350
                                  and not item['weather_category'] == 4 and not item['temperature_category'] == 2))
                delivery = 20
        else:
            if dust.find('매우나쁨') > -1:
                menu_list = list((item for item in menus if item['distance'] < 250
                                  and not item['temperature_category'] == 2))
                delivery = 10
                추가메세지 = '미세먼지 심한 '
    else:
        menu_list = menus

    delivery_submit = random.randrange(0, 100)
    # print('delivery', delivery)
    # print('delivery_submit', delivery_submit)
    if delivery_submit < delivery:
        context.bot.sendMessage(
            text=f'*********** {today} ***********\n{weather_txt}\n\n오늘 같은 {추가메세지}날씨엔 배달은 어떠신가요?',
            chat_id=str(query.message.chat.id)
        )
    else:
        menu = menu_choice(menu_list)  # 랜덤으로 메뉴를 뽑는다
        weight = menu['weight']
        if weight < 100:  # 메뉴의 가중치가 100보다 작으면 확률 굴림을 한다
            submit = random.randrange(0, 100)
            if weight < submit:
                print('승인 실패: ', menu)
                menu = menu_choice(menu_list)  # 확률 굴림 실패시 다시 한번 랜덤으로 메뉴를 뽑는다
        name = menu['name']
        url = menu['url']
        message = menu['message']
        context.bot.sendMessage(
            text=f'*********** {today} ***********\n{weather_txt}\n'
                 f'\n{user_name}, 오늘 같은 {추가메세지}날씨엔 여기 어떠신가요?\n-> {message}<b>{name}!</b>\n{url}',
            chat_id=str(query.message.chat.id),
            parse_mode='Html'
        )
        selfAlarm(user_name)


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
        user_name = '사용자님'
    else:
        user_name = user_name + '님'

    return user_name


def select_category_menu(category):
    menu = ''
    if category == 0:
        menu = menu_choice(menus)
    else:
        new_menus = create_new_menus_by_category(category)
        menu = menu_choice(new_menus)
    return menu


def menu_choice(menu_list):
    choice = random.randrange(0, len(menu_list))
    menu = menu_list[choice]
    return menu


def random_category_select(category):
    menu = select_category_menu(category)  # 랜덤으로 메뉴를 뽑는다
    # print('menu', menu)
    weight = menu['weight']
    if weight < 100:  # 메뉴의 가중치가 100보다 작으면 확률 굴림을 한다
        submit = random.randrange(0, 100)
        if weight < submit:
            print('승인 실패: ', menu)
            menu = select_category_menu(category)  # 확률 굴림 실패시 다시 한번 랜덤으로 메뉴를 뽑는다(2번 연속 뽑혔다면 운명 이겠지)
    return menu


def create_new_menus_by_category(category):
    return list((item for item in menus if item['category'] == category))


def start_command_btn_show(update: Update, context: CallbackContext):
    전체랜덤 = BT(text="오늘 점심은 어디로? (완전 랜덤)", callback_data="start_1")
    카테고리선택 = BT(text="끌리는 종류가 있어요!", callback_data="start_2")
    날씨별추천 = BT(text="🌏 날씨를 보고 추천해 드려요 🌏", callback_data="start_3")
    mu = MU(inline_keyboard=[
        [전체랜덤],
        [날씨별추천],
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
        text=f'********** 등록된 가게 목록(등록순) *********\n{menu_list}\n\n현재 {len(menus)} 곳이 등록 되어 있습니다',
        chat_id=str(update.message.chat.id)
    )


def start_command_weather_show(update: Update, context: CallbackContext):
    weather = get_weather()
    weather_txt = get_weather_text(weather)
    if weather_txt is None:
        weather_txt = '날씨 정보를 찾을 수 없습니다'
    context.bot.sendMessage(
        text=f'{weather_txt}',
        chat_id=str(update.message.chat.id)
    )


def start_btn_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    today = datetime.datetime.today().strftime("%Y-%m-%d")

    # user_name = query.from_user.last_name + query.from_user.first_name
    user_name = make_user_name(update)

    if data == 'start_1':
        menu = random_category_select(0)
        name = menu['name']
        url = menu['url']
        message = menu['message']
        context.bot.sendMessage(
            text=f'************ 완전 무작위! ************\n{today}'
                 f'\n점심 추천봇이 {user_name}께 추천하는 오늘의 점심은~ \n-> {message}<b>{name}!</b>\n{url}',
            chat_id=str(query.message.chat.id),
            parse_mode='Html'
        )
        selfAlarm(user_name)
    elif data == 'start_2':
        category_command_btn_show(update, context)
    elif data == 'start_3':
        weather_btn_callback(update, context)


def category_btn_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    today = datetime.datetime.today().strftime("%Y-%m-%d")
    # user_name = query.from_user.last_name + query.from_user.first_name
    user_name = make_user_name(update)
    category_text = ''

    if data == 'category_1':
        category_text = '탕,찌개'
        menu = random_category_select(1)
    elif data == 'category_2':
        category_text = '돈까스,일식'
        menu = random_category_select(2)
    elif data == 'category_3':
        category_text = '양식'
        menu = random_category_select(3)
    elif data == 'category_4':
        category_text = '중식'
        menu = random_category_select(4)
    elif data == 'category_5':
        category_text = '아시안'
        menu = random_category_select(5)
    elif data == 'category_6':
        category_text = '백반,국수'
        menu = random_category_select(6)
    elif data == 'category_7':
        category_text = '분식'
        menu = random_category_select(7)
    elif data == 'category_8':
        category_text = '패스트푸드'
        menu = random_category_select(8)

    name = menu['name']
    url = menu['url']
    context.bot.sendMessage(
        text=f'************************************\n{today}\n- {category_text} - 종류 중에서\n{user_name}을 위해 선택한 오늘의 점심은~ \n<b>{name}!</b>\n{url}',
        chat_id=str(query.message.chat.id),
        # parse_mode='Markdown'
        parse_mode='Html'
    )
    selfAlarm(user_name)


def weather_btn_callback(update: Update, context: CallbackContext):
    select_weather_menu(update, context)


def button_callback_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data

    if data.find('start') > -1:
        start_btn_callback(update, context)
    elif data.find('category') > -1:
        category_btn_callback(update, context)
    elif data.find('weather') > -1:
        weather_btn_callback(update, context)
    else:
        context.bot.sendMessage(
            text='안녕히가세요',
            chat_id=str(query.message.chat.id)
        )


def alarm():
    while True:
        # Get the current time
        now = datetime.datetime.now(tz=korea_tz)
        date = now.date()
        current_time = datetime.datetime.now(tz=korea_tz).time()
        current_time_str = current_time.strftime('%H:%M:%S')
        alarm_time = datetime.time(hour=11, minute=30, tzinfo=korea_tz)
        alarm_time_str = alarm_time.strftime('%H:%M:%S')
        # chat_id = '1643754742'
        chat_id = '-854598255'

        if (0 <= now.weekday() <= 4) and (current_time_str == alarm_time_str) and date not in kr_holidays:
            display_time = current_time_str[0:5]
            message1 = f'⏰<b>{display_time}</b> 데일리 점심 알람 입니다\n'
            message2 = select_weather_menu_str()
            message = message1+message2
            sendMessage(chat_id, message)

        # Sleep for 1 second before checking the time again
        time.sleep(1)


def sendMessage(chat_id, message):
    bot = Bot(token)
    bot.sendMessage(chat_id=chat_id, text=message, parse_mode='Html')


def selfAlarm(name):
    chat_id = '1643754742'
    sendMessage(chat_id, f'{name}이 이용하셨어요')


def select_weather_menu_str():
    today = datetime.datetime.today().strftime("%Y-%m-%d")
    weather = get_weather()
    print('weather', weather)
    weather_txt = get_weather_text(weather)
    temperature = weather['temperature']
    cast = weather['cast']
    dust = weather['dust']
    is_bad_weather = bad_weather(cast)
    menu_list = []
    추가메세지 = ''
    delivery = 2
    if temperature < 4:
        if is_bad_weather:
            if dust.find('나쁨') > -1:
                menu_list = list((item for item in menus if item['distance'] < 250
                                  and not item['weather_category'] == 4 and not item['temperature_category'] == 3))
                delivery = 60
                추가메세지 = '춥고 궂은 '
            else:
                menu_list = list((item for item in menus if item['distance'] < 250
                                  and not item['weather_category'] == 4 and not item['temperature_category'] == 3))
                delivery = 40
        else:
            if dust.find('매우나쁨') > -1:
                menu_list = list((item for item in menus if item['distance'] < 350
                                  and not item['temperature_category'] == 3))
                delivery = 30
                추가메세지 = '미세먼지 심한 '
            else:
                menu_list = list((item for item in menus if item['distance'] < 500
                                  and not item['temperature_category'] == 3))
                delivery = 10
                추가메세지 = ''
    elif temperature > 28:
        if is_bad_weather:
            if dust.find('나쁨') > -1:
                menu_list = list((item for item in menus if item['distance'] < 250))
                delivery = 50
                추가메세지 = '덥고 궂은 '
            else:
                menu_list = list((item for item in menus if item['distance'] < 350
                                  and not item['weather_category'] == 4 and not item['temperature_category'] == 2))
                delivery = 20
        else:
            if dust.find('매우나쁨') > -1:
                menu_list = list((item for item in menus if item['distance'] < 250
                                  and not item['temperature_category'] == 2))
                delivery = 10
                추가메세지 = '미세먼지 심한 '
    else:
        menu_list = menus

    delivery_submit = random.randrange(0, 100)
    # print('delivery', delivery)
    # print('delivery_submit', delivery_submit)
    if delivery_submit < delivery:
        text = f'*********** {today} ***********\n{weather_txt}\n\n점심 알람봇이 추천 합니다.\n오늘 같은 {추가메세지}날씨엔 배달은 어떠신가요?'
    else:
        menu = menu_choice(menu_list)  # 랜덤으로 메뉴를 뽑는다
        weight = menu['weight']
        if weight < 100:  # 메뉴의 가중치가 100보다 작으면 확률 굴림을 한다
            submit = random.randrange(0, 100)
            if weight < submit:
                print('승인 실패: ', menu)
                menu = menu_choice(menu_list)  # 확률 굴림 실패시 다시 한번 랜덤으로 메뉴를 뽑는다
        name = menu['name']
        url = menu['url']
        message = menu['message']
        text = f'*********** {today} ***********\n{weather_txt}\n점심 알람봇이 추천 합니다.\n여기 어떠신가요?\n-> {message}<b>{name}!</b>\n{url}'

    return text


def main():
    bot = Bot(token)
    command = [BotCommand("start", "시작"), BotCommand("list", "등록된 가게 목록(등록순)")]
    bot.set_my_commands(command)
    t = threading.Thread(target=alarm)
    t.daemon = True
    t.start()

    updater = Updater(token)
    dispatcher = updater.dispatcher
    # dispatcher.add_handler(MessageHandler(Filters.text, echo)) # 메시지 핸들러 (유저의 일반 채팅에 반응 하므로 여기선 사용 안함)
    dispatcher.add_handler(CommandHandler('start', start_command_btn_show))  # 커맨드 핸들러
    dispatcher.add_handler(CommandHandler('list', start_command_list_show))  # 커맨드 핸들러
    dispatcher.add_handler(CommandHandler('weather', start_command_weather_show))  # 커맨드 핸들러
    dispatcher.add_handler(CallbackQueryHandler(button_callback_handler))  # 버튼 클릭 핸들러
    updater.start_polling()
    updater.idle()


main()
