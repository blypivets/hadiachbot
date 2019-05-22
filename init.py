from parser import get_busses

import datetime

import asyncio
import os
import logging

from aiogram import Bot, types, Dispatcher, executor
from aiogram.utils.callback_data import CallbackData

API_TOKEN = os.environ['API_TOKEN']

# Configure logging
logging.basicConfig(level=logging.INFO)

loop = asyncio.get_event_loop()
bot = Bot(token=API_TOKEN, loop=loop)
dp = Dispatcher(bot)
bus_cb = CallbackData('bus', 'wkday', 'date', 'time') # post:<id>:<action>
WEEK_DAYS = ('Понеділок', 'Вівторок', 'Середа', 'Четвер', "П'ятниця", 'Субота', 'Неділя')
WEEK_DAYS_IMG = ( 'http://clipart-library.com/image_gallery2/Calendar-PNG-Picture.png',
                'http://clipart-library.com/image_gallery2/Calendar-PNG-Picture.png',
                'http://clipart-library.com/image_gallery2/Calendar-PNG-Picture.png',
                'http://clipart-library.com/image_gallery2/Calendar-PNG-Picture.png',
                'http://clipart-library.com/image_gallery2/Calendar-PNG-Picture.png',
                'http://clipart-library.com/image_gallery2/Calendar-PNG-Picture.png',
                'http://clipart-library.com/image_gallery2/Calendar-PNG-Picture.png')
DEPARTURE_TIME = ['5:45', '13:15']

def next_weekday(day, wkday):
    delta = wkday - day.weekday()
    if delta <= 0: delta += 7
    return day + datetime.timedelta(delta)

def prepare_items(items):
    title = 'Суми - Гадяч'
    description_base = 'Дізнатись кількість вільних місць'
    ask_choose_bus = 'Оберіть час відправлення'


    result = []
    for day, desc in items.items():
        # markup
        markup = types.InlineKeyboardMarkup()
        for idx in range(len(DEPARTURE_TIME)):
            markup.insert(
                    types.InlineKeyboardButton(
                    DEPARTURE_TIME[idx],
                    callback_data=bus_cb.new(wkday=desc['wkday'], date=desc['day'], time=str(idx)))
                    )

        # message
        msg = '🚌 Звєздольт Суми -> Гадяч' + '\n' + '\n'
        msg += '📅 ' + desc['wkday'] + ', '
        msg += desc['day'] + '\n' + '\n'
        msg += ask_choose_bus

        input_content = types.InputTextMessageContent(msg)
        item = types.InlineQueryResultArticle(id=desc['id'],
                                            title=title + ' [' + desc['title_info'] + '][' + desc['day'] + ']',
                                            input_message_content=input_content,
                                            reply_markup = markup,
                                            description= description_base,
                                            thumb_url = desc['thumb_url'],)
        result.append(item)
    return result

@dp.inline_handler()
async def inline_echo(inline_query: types.InlineQuery):
    articles = {}

    today_item_msgs = {}
    today_item_msgs['day'] = datetime.date.today().strftime("%d/%m/%Y")
    today_item_msgs['wkday'] = WEEK_DAYS[datetime.date.today().weekday()]
    today_item_msgs['id'] = '2'
    today_item_msgs['thumb_url'] = 'http://www.cndajin.com/data/wls/201/18443229.png'
    today_item_msgs['title_info'] = 'Сьогодні'

    articles['today'] = today_item_msgs

    if len(inline_query.query) > 0:
        custom_item_msgs = {}
        custom_date = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, int(inline_query.query))
        custom_item_msgs['day'] = custom_date.strftime("%d/%m/%Y")
        custom_item_msgs['wkday'] = WEEK_DAYS[custom_date.weekday()]
        custom_item_msgs['id'] = '1'
        custom_item_msgs['thumb_url'] = 'http://clipart-library.com/image_gallery2/Calendar-PNG-Picture.png'
        custom_item_msgs['title_info'] = 'Вказана дата'
        articles['custom'] = custom_item_msgs

    today_wkday = datetime.date.today().weekday()
    week_days_list = WEEK_DAYS[today_wkday + 1:] + WEEK_DAYS[:today_wkday + 1]
    counter = 3
    for d in week_days_list:
        item_msgs={}
        wkday_index = WEEK_DAYS.index(d)
        custom_date = next_weekday(datetime.datetime.now(), wkday_index)

        item_msgs['day'] = custom_date.strftime("%d/%m/%Y")
        item_msgs['wkday'] = d
        item_msgs['id'] = str(counter)
        item_msgs['thumb_url'] = WEEK_DAYS_IMG[wkday_index]
        item_msgs['title_info'] = d

        articles[d] = item_msgs
        counter +=1


    items = prepare_items(articles)

    await bot.answer_inline_query(inline_query.id, results=items, cache_time=1)

@dp.callback_query_handler(lambda cb : True)
async def query_view(query: types.CallbackQuery):
    w_day = query.data.split(':')[1]
    date = query.data.split(':')[2]
    dep_time = DEPARTURE_TIME[int(query.data.split(':')[3])]

    full_list = get_busses(date.replace('/', '.'))
    if(len(full_list) == 0):
        await query.answer('Обраний маршрут недоступний' , show_alert=True)
        return
    print(full_list)

    bus = list(filter(lambda bus: bus['from_departure_time'] == dep_time, full_list))[0]

    msg = 'Рейс №' + bus['number'] + '\n'
    msg += bus['fdepdest_short'] + '\n' + '\n'
    msg += w_day + ', ' + date + '\n'
    msg += 'Відправлення: ' + bus['from_departure_time'] + '\n'
    msg += 'Прибуття: ' + bus['to_arrival'] + '\n'
    msg += 'В дорозі: ' + bus['tr'] + '\n' + '\n'
    msg += 'Залишилось ' + bus['seats_kol'] + ' місць' + '\n'
    msg += 'Ціна квитка: ' + bus['price'] + ' грн'

    await query.answer(msg , show_alert=True)


if __name__ == '__main__':
    executor.start_polling(dp, loop=loop, skip_updates=True)
