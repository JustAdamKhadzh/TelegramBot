from telegram.ext import CommandHandler, Filters, Updater, MessageHandler, ConversationHandler, RegexHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
import logging
import requests
import json

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

logger = logging.getLogger()

TOKEN = '757561487:AAG4Fhx3ftLSKyuX2j6YngsVvGMHim0OuUA'#токен для телеграм бота
# api_token = 'e1bf14ba-f18d-42e3-b5fd-809990e63de3'#токен для доступа к яндекс картам
api_token = 'dc84d856-d194-48d4-9a02-bb9e290cc5c7'
updater = Updater(token = TOKEN)
dispatcher = updater.dispatcher
location = 'No'

MEAL = 0
IS_RESTR = 1
YES_RESTR = 2
MONEY = 3
LOCATION = 4
GET_LOCATION = 5
LOC = 6
EXTRA_REQUERMENTS = 7
GET_EXTRA_REQ = 8
PROCESS = 9
use_loc = False

def query_to_ymaps(text):
    query = 'https://search-maps.yandex.ru/v1/?text=txt'.replace('txt',text)
    query += '&type=biz&lang=ru_RU&results=500&apikey=mkey'.replace('mkey', api_token)
    response = requests.get(query).json()
    return response['features']

def startCommand(bot, update):
    update.message.reply_text('Привет, Меня зовут EatingTimeBot. Я помогу Вам найти место, где можно хорошо подкрепиться.\
Вы можете начать поиск с помощью команды /search. Если Вы передумали, то можете завершить наш разговор командой /cancel\n')
    
def searchCommand(bot, update):
    update.message.reply_text('Скажите, что Вы предпочитаете. Это может быть что-то конкретное вроде бургеров или пиццы, либо \
                              национальная кухня. Например: итальянская еда.\n')
    return MEAL

def get_meal(bot, update, user_data):
    user_data['request'] = update.message.text
    user_data['restriction'] = ''
    logger.info("Получил %s", update.message.text)
    reply_list = [['Да', 'Нет']]
    update.message.reply_text('Хорошо, есть ли у Вас какие-то ограничения в еде?',
                             reply_markup=ReplyKeyboardMarkup(reply_list, one_time_keyboard=True))
    return IS_RESTR

def answer_to_restrictions(bot, update, user_data):
    answer = update.message.text
    logger.info('Получил %s', answer)
    if answer.lower() == 'да':
        update.message.reply_text('Не проблема, попытаюсь что то найти для Вас.\
        Я могу подобрать для Вас место учитывая следующие ограничения:\n\
        халяль, лактоза, кошер, глютен, веган, вегетарианец.', reply_markup=ReplyKeyboardRemove())
        update.message.reply_text('Что нужно учесть?')
        return YES_RESTR
    else:
        update.message.reply_text('Понятно, сколько Вы готовы потратить на одного человека?', reply_markup=ReplyKeyboardRemove())
        return MONEY
    
def get_restrictions(bot, update, user_data):
    user_data['restriction']  = update.message.text
    logger.info('Получил %s', update.message.text)
    update.message.reply_text('Хорошо, учту при поиске.\
    Сколько Вы готовы потратить на одного человека?\n')
    return MONEY

def money_topay(bot, update, user_data):
    user_data['ready_topay'] = update.message.text
    logger.info('Получил %s', update.message.text)
    reply_list = [['Без разницы','Поблизости']]
    update.message.reply_text('Желаемое месторасположение заведения?',
                              reply_markup=ReplyKeyboardMarkup(reply_list, one_time_keyboard=True))
    return LOCATION

def location(bot, update, user_data):
    answer = update.message.text
    logger.info('in location func получил %s', answer)
    if answer == 'Поблизости':
        user_data['is_near'] = True
        reply_list = [['Да','Нет']]
        update.message.reply_text('Нам нужно узнать Ваше местоположение. Разрешаете ли Вы использовать вашу геопозицию?', 
                                  reply_markup=ReplyKeyboardMarkup(reply_list, one_time_keyboard=True))
        return GET_LOCATION
    else:
        user_data['is_near'] = False
        user_data['use_loc'] = False
    update.message.reply_text('Хорошо!')
    reply_list = [['Да', 'Нет']]
    update.message.reply_text('Есть у Вас какие-то доп пожелания к месту?',
                              reply_markup=ReplyKeyboardMarkup(reply_list, one_time_keyboard=True))
    return EXTRA_REQUERMENTS

def get_location(bot, update, user_data):
    if update.message.text == 'Да':
        reply_list = [[KeyboardButton(text='Разрешить', request_location=True)]]
        update.message.reply_text('Нажмите кнопку', reply_markup=ReplyKeyboardMarkup(reply_list, one_time_keyboard=True))
        user_data['use_loc'] = True
        return LOC
    else:
        user_data['use_loc'] = False
        update.message.reply_text('Принято, будем искать по городу', reply_markup=ReplyKeyboardRemove())
        reply_list = [['Да', 'Нет']]
        update.message.reply_text('Есть ли у Вас какие-то доп пожелания к месту?', 
                                  reply_markup=ReplyKeyboardMarkup(reply_list, one_time_keyboard=True))
        return EXTRA_REQUERMENTS

def print_location(bot, update, user_data):
    logger.info('Получил координаты' + str(update.message.location.longitude) + str(update.message.location.latitude))
    user_data['longitude'] = update.message.location.longitude
    user_data['latitude'] = update.message.location.latitude
    update.message.reply_text('Принято', reply_markup=ReplyKeyboardRemove())
    reply_list = [['Да', 'Нет']]
    update.message.reply_text('Есть ли у Вас какие-то доп пожелания к месту?', 
                                  reply_markup=ReplyKeyboardMarkup(reply_list, one_time_keyboard=True))
    return EXTRA_REQUERMENTS

def extra_requerments(bot, update, user_data):
    answer = update.message.text
    logger.info('Получил %s', answer)
    if answer.lower() == 'да':
        update.message.reply_text('Что нужно учесть?', reply_markup=ReplyKeyboardRemove())
        return GET_EXTRA_REQ
    else:
        update.message.reply_text('Пошел искать. Ждите, скоро вернусь!', reply_markup=ReplyKeyboardRemove())
#         with open('centrdata.json','r') as f:
#             info_place = json.load(f)
        info_place = query_to_ymaps(user_data['request'] + ',' + user_data['restriction'])
    
        print('Начинаю искать')
        scores = {i:0 for i in range(len(info_place))}
        target = user_data['request'] #'американская'
        type_price = price_level(user_data['ready_topay'])
        for ind, obj in enumerate(info_place):
            try:
                for d in obj['properties']['CompanyMetaData']['Features']:
                        if d['id'] == 'type_cuisine':
                            for v in d['values']:
                                if v['value'] == target:
                                    scores[ind] += 1
                        if d['id'] == 'price_category':
                            for v in d['values']:
                                if v['value'].split('–')[0] == type_price:
                                    scores[ind] += 1
            except KeyError:
                continue
        print('done!')
        idx = [key for key, val in sorted(scores.items(), key=lambda x: x[1], reverse=True)]
        update.message.reply_text('\n'.join(return_result(idx[:10], info_place)))
        return ConversationHandler.END
def return_result(ixs,data):
    return [data[i]['properties']['name'] for i in ixs]

def price_level(price):
    pr = int(price)
    if pr < 350:
        return 'низкие'
    elif 350 <= pr < 600:
        return 'средние'
    elif 600 <= pr < 900:
        return 'выше среднего'
    else:
        return 'высокие'
    
    
def get_extra_req(bot, update, user_data):
    user_data['hopes_for_place'] = update.message.text
    logger.info('Получил %s', hopes_for_place)
    update.message.reply_text('Пошел искать. Ждите, скоро вернусь!)')
#     with open('centrdata.json','r') as f:
#         info_place = json.load(f)
    info_place = query_to_ymaps(user_data['request'] + ',' + user_data['restriction'])
    print('Начинаю искать')
    scores = {i:0 for i in range(len(info_place))}
    target = user_data['request'] #'американская'
    type_price = price_level(user_data['ready_topay'])
    for ind, obj in enumerate(info_place):
        try:
            for d in obj['properties']['CompanyMetaData']['Features']:
                    if d['id'] == 'type_cuisine':
                        for v in d['values']:
                            if v['value'] == target:
                                scores[ind] += 1
                    if d['id'] == 'price_category':
                        for v in d['values']:
                            if v['value'].split('–')[0] == type_price:
                                scores[ind] += 1
        except KeyError:
            continue
    idx = [key for key, val in sorted(scores.items(), key=lambda x: x[1], reverse=True)]
    update.message.reply_text('\n'.join(return_result(idx[:10], info_place)))
    return ConversationHandler.END
    
                                                                                                                       
def nameCommand(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text = 'I\'m FoodSeekerBot')

def cancelCommand(bot, update):
    bot.send_message(chat_id=update.message.chat_id,text = 'До скорой встречи!')
    return ConversationHandler.END

starthandler = CommandHandler('start', startCommand)
cancelhandler = CommandHandler('cancel', cancelCommand)
namehandler = CommandHandler('name', nameCommand)
conv_handler = ConversationHandler(
entry_points = [CommandHandler('search', searchCommand)],
states = {
    MEAL: [MessageHandler(Filters.text, get_meal, pass_user_data=True)],
    IS_RESTR: [MessageHandler(Filters.text, answer_to_restrictions, pass_user_data=True)],
    YES_RESTR: [MessageHandler(Filters.text, get_restrictions,pass_user_data=True)],
    MONEY: [MessageHandler(Filters.text, money_topay,pass_user_data=True)],
    LOCATION: [MessageHandler(Filters.text, location,pass_user_data=True)],
    GET_LOCATION: [MessageHandler(Filters.text, get_location,pass_user_data=True)],
    LOC: [MessageHandler(Filters.location, print_location,pass_user_data=True)],
    EXTRA_REQUERMENTS: [MessageHandler(Filters.text, extra_requerments,pass_user_data=True)],
#     ANSWER_EXTRA_REQ: [MessageHandler(Filters.text, answer_extra_req)],
    GET_EXTRA_REQ: [MessageHandler(Filters.text, get_extra_req,pass_user_data=True)]},
fallbacks = [CommandHandler('cancel', cancelCommand)])

dispatcher.add_handler(starthandler)
dispatcher.add_handler(namehandler)
dispatcher.add_handler(cancelhandler)
dispatcher.add_handler(conv_handler)


updater.start_polling(clean=True)
updater.idle()


























