from wb_requests import *
import tracking
import _thread
token = "5088143255:AAGbgzxo6I12YUZebl9RGdPb5R8RYRIM9RY"
bot = telebot.TeleBot(token)

warehouses = {'Казань': '117986', 'Екатеринбург': '1733', 'Подольск': '507', 'Коледино': '3158', 'Новосибирск': '686', 'Санкт-Петербург': '2737', 'Склад краснодар': '130744', 'Хабаровск': '1193', 'Электросталь': '120762', 'Электросталь КБТ': '121709'}
inv_warehouses = {v: k for k, v in warehouses.items()}
types = {'Моно': 'mono', 'Микс': 'mix', 'Монопаллета': 'monoPallet', 'Суперсейф': 'superSafe'}
inv_types = {v: k for k, v in types.items()}
times = {'Сегодня': 'today', 'Завтра': 'tomorrow', 'Неделя (включая сегодня)': 'week', 'Искать пока не найдется': 'until_found', 'Ввести даты самостоятельно': 'enter_manually'}
warehouses_btns = [InlineKeyboardButton(city, callback_data=warehouses[city]) for city in warehouses.keys()]
types_btns = [InlineKeyboardButton(type1, callback_data=types[type1]) for type1 in types.keys()]
time_btns = [InlineKeyboardButton(time, callback_data=times[time]) for time in times.keys()]

users = dict()  # {chat.message.id: [function_name: (str), [warehouse_id: (str, None), tracking_type: (str, None), quantity: (int, None), time: (str, None)]]}

track = tracking.Tracking(warehouses, types, bot)

_thread.start_new_thread(track.polling, ())


@bot.message_handler(commands=['start'])
def main_menu(message):
    users[message.chat.id] = ['main_menu', [None, None, None, None]]
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("Добавить отслеживание", callback_data="select_city"), InlineKeyboardButton("Мои отслеживания", callback_data="my_tracks"))
    bot.send_message(message.chat.id, 'Выберете пункт в меню', reply_markup=markup)

def my_tracks(message):
    users[message.chat.id] = ["my_tracks", [None, None, None, None]]
    if message.chat.id not in track.user_tracks.keys():
        bot.send_message(message.chat.id, "Нет отслеживаний")
        main_menu(message)
    else:
        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        markup.add(*[InlineKeyboardButton(f"{track.tracks[track_id]['quantity']} шт, {inv_warehouses[track.tracks[track_id]['warehouse_id']]}, {inv_types[track.tracks[track_id]['type']]}, {', '.join([track.tracks[track_id]['time'][0][i1].strftime('%d.%m.%Y') for i1 in range(len(track.tracks[track_id]['time'][0]))])}", callback_data=f"my_track:{track_id}") for track_id in track.user_tracks[message.chat.id]], InlineKeyboardButton("Назад", callback_data="my_tracks_back"))
        bot.send_message(message.chat.id, "Выберете пункт в меню", reply_markup=markup)

def my_track(message, track_id):
    users[message.chat.id] = ['my_track', [track_id, None, None, None]]
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("Изменить отслеживание", callback_data=f"change_track:{track_id}"), InlineKeyboardButton("Удалить отслеживание", callback_data=f"remove_track:{track_id}"), InlineKeyboardButton("Назад", callback_data="my_track_back"), InlineKeyboardButton("В главное меню", callback_data="main_menu"))
    bot.send_message(message.chat.id, f"{track.tracks[track_id]['quantity']} шт, {inv_warehouses[track.tracks[track_id]['warehouse_id']]}, {inv_types[track.tracks[track_id]['type']]}, {', '.join([date.strftime('%d.%m.%Y') for date in track.tracks[track_id]['time'][0]])}", reply_markup=markup)

def confirm_removal(message, track_id):
    users[message.chat.id][0] = 'confirm_removal'
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("Да, удалить", callback_data=f"confirm_yes:{track_id}"), InlineKeyboardButton("Нет, я передумал", callback_data=f"confirm_no:{track_id}"))
    bot.send_message(message.chat.id, "Уверены, что хотите удалить?", reply_markup=markup)

def change_track_message(message, track_id):
    users[message.chat.id][0] = 'change_track_message'
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("Склад", callback_data=f"change_warehouse:{track_id}"), InlineKeyboardButton("Тип", callback_data=f"change_type:{track_id}"), InlineKeyboardButton("Количество", callback_data=f"change_quantity:{track_id}"), InlineKeyboardButton("Дату", callback_data=f"change_time:{track_id}"), InlineKeyboardButton("Ничего, я передумал", callback_data="my_track_back"))
    bot.send_message(message.chat.id, "Что хотите поменять?", reply_markup=markup)

def change_warehouse(message, track_id):
    users[message.chat.id][0] = 'change_warehouse'
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(*[InlineKeyboardButton(key, callback_data=f"ch_warehouse:{warehouses[key]}:{track_id}") for key in warehouses.keys()], InlineKeyboardButton("Назад", callback_data=f"ch_back:{track_id}"))
    bot.send_message(message.chat.id, 'Выберете пункт в меню', reply_markup=markup)

def change_type(message, track_id):
    users[message.chat.id][0] = 'change_warehouse'
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(*[InlineKeyboardButton(key, callback_data=f"ch_type:{types[key]}:{track_id}") for key in types.keys()], InlineKeyboardButton("Выбрать другой склад", callback_data=f"ch_back:{track_id}"), InlineKeyboardButton("В главное меню", callback_data="main_menu"))
    bot.send_message(message.chat.id, 'Выберете пункт в меню', reply_markup=markup)

def change_time(message, track_id):
    users[message.chat.id][0] = 'select_time'
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(*[InlineKeyboardButton(key, callback_data=f"ch_time:{times[key]}:{track_id}") for key in times.keys()], InlineKeyboardButton("Назад", callback_data=f"ch_back:{track_id}"), InlineKeyboardButton("В главное меню", callback_data="main_menu"))
    bot.send_message(message.chat.id, 'Выберите даты для поисков лимитов', reply_markup=markup)

def select_city(message):
    users[message.chat.id][0] = 'select_city'
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(*warehouses_btns, InlineKeyboardButton("Назад", callback_data="back"))
    bot.send_message(message.chat.id, 'Выберете пункт в меню', reply_markup=markup)

def select_type(message):
    users[message.chat.id] = ['select_type', [users[message.chat.id][1][0], None, None, None]]
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(*types_btns, InlineKeyboardButton("Выбрать другой склад", callback_data="back"), InlineKeyboardButton("В главное меню", callback_data="main_menu"))
    bot.send_message(message.chat.id, 'Выберете пункт в меню', reply_markup=markup)

def select_time(message):
    users[message.chat.id] = ['select_time', [*users[message.chat.id][1][:3], None]]
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(*time_btns, InlineKeyboardButton("Выбрать другой склад", callback_data="back"), InlineKeyboardButton("В главное меню", callback_data="main_menu"))
    bot.send_message(message.chat.id, f'Вы указали {users[message.chat.id][1][2]} штук. Теперь выберите даты для поисков лимитов', reply_markup=markup)

def created_track(message):
    track.add(message.chat.id, *users[message.chat.id][1])
    users[message.chat.id][0] = 'created_track'
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("Да, добавить ешё отслеживание", callback_data="select_city"), InlineKeyboardButton("Спасибо, не нужно", callback_data="main_menu"), InlineKeyboardButton("Показать мои отслеживания", callback_data="my_tracks"))
    bot.send_message(message.chat.id, f"{users[message.chat.id][1][2]} штук {inv_warehouses[users[message.chat.id][1][0]]} успешно добавлено на {', '.join([users[message.chat.id][1][3][0][i].strftime('%d.%m.%Y') for i in range(len(users[message.chat.id][1][3][0]))])}.\nХотите добавть ещё?", reply_markup=markup)

@bot.message_handler(content_types='text')
def text_handler(message):
    if message.chat.id not in users.keys():
        main_menu(message)
    elif users[message.chat.id][0] == 'select_quantity':
        if message.text.isnumeric() and int(message.chat.id) > 0:
            users[message.chat.id][1][2] = int(message.text)
            select_time(message)
        else:
            bot.send_message(message.chat.id, "Веденное Вами число не соответствует формату, повторите попытку")

    elif users[message.chat.id][0] == 'enter_manually':
        try:
            times = []
            split_msg = message.text.split(', ')
            for time in split_msg:
                times.append(datetime.datetime.strptime(time, "%d.%m.%Y").date())
                times.sort()
        except ValueError:
            bot.send_message(message.chat.id, "Введенные Вами даты не соответствуют формату. Введите даты через запятую, начиная с сегодня и заканчивая не далее чем через 4 недели в формате dd.mm.yyyy. Пример: 12.12.2012, 13.12.2013. ")
        else:
            if datetime.timedelta(weeks=4) >= times[0] - datetime.date.today() >= datetime.timedelta():
                users[message.chat.id][1][3][0] = times
                created_track(message)
            else:
                bot.send_message(message.chat.id, "Введенные Вами даты не соответствуют формату. Введите даты через запятую, начиная с сегодня и заканчивая не далее чем через 4 недели в формате dd.mm.yyyy. Пример: 12.12.2012, 13.12.2013")

    elif users[message.chat.id][0] == 'change_quantity':
        if message.text.isnumeric() and int(message.chat.id) > 0:
            track.tracks[users[message.chat.id][1][0]]['quantity'] = int(message.text)
            my_track(message, users[message.chat.id][1][0])
        else:
            bot.send_message(message.chat.id, "Веденное Вами число не соответствует формату, повторите попытку")

    elif users[message.chat.id][0] == 'change_time_manually':
        try:
            times = []
            split_msg = message.text.split(', ')
            for time in split_msg:
                times.append(datetime.datetime.strptime(time, "%d.%m.%Y").date())
                times.sort()
        except ValueError:
            bot.send_message(message.chat.id, "Введенные Вами даты не соответствуют формату. Введите даты через запятую, начиная с сегодня и заканчивая не далее чем через 4 недели в формате dd.mm.yyyy. Пример: 12.12.2012, 13.12.2013. ")
        else:
            if datetime.timedelta(weeks=4) >= times[0] - datetime.date.today() >= datetime.timedelta():
                track.tracks[users[message.chat.id][1][0]]['time'] = [times, 'enter_manually']
                my_track(message, users[message.chat.id][1][0])
            else:
                bot.send_message(message.chat.id, "Введенные Вами даты не соответствуют формату. Введите даты через запятую, начиная с сегодня и заканчивая не далее чем через 4 недели в формате dd.mm.yyyy. Пример: 12.12.2012, 13.12.2013")
    else:
        main_menu(message)


functions = ["main_menu", "select_city", 'select_type', 'select_time', 'select_quantity']
track_functions = ["main_menu", "my_tracks", "my_track", "change_track_message"]


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    print("received callback:", call.data)
    data = call.data.split(':')
    if call.data == 'back':
        print("call is back")
        new_function = functions[max(0, functions.index(users[call.message.chat.id][0]) - 1)]
        eval(new_function + '(call.message)')
    elif call.data in ['main_menu', 'select_city', 'my_tracks']:
        print("call in eval")
        eval(call.data + '(call.message)')
    elif call.data in warehouses.values():
        print("call in warehouse")
        users[call.message.chat.id][1][0] = call.data
        select_type(call.message)
    elif call.data in types.values():
        print("call in type")
        bot.send_message(call.message.chat.id, "Укажите необходимый лимит в условном значении. Указывайте точное количества товара в вашей поставке. Это количество указано в скобках рядом с номером заказа в разделе - Управление поставками")
        users[call.message.chat.id][0] = "select_quantity"
        users[call.message.chat.id][1][1] = call.data
    elif call.data in times.values():
        today = datetime.date.today()
        print("call in time")
        if call.data == "today":
            users[call.message.chat.id][1][3] = [[today], call.data]
            created_track(call.message)
        elif call.data == "tomorrow":
            users[call.message.chat.id][1][3] = [[today + datetime.timedelta(days=1)], call.data]
            created_track(call.message)
        elif call.data == "week":
            users[call.message.chat.id][1][3] = [[today + datetime.timedelta(days=i) for i in range(7)], call.data]
            created_track(call.message)
        elif call.data == "until_found":
            users[call.message.chat.id][1][3] = call.data
            created_track(call.message)
        elif call.data == "enter_manually":
            bot.send_message(call.message.chat.id, "Введите даты через запятую, начиная с сегодня и заканчивая не далее чем черз 4 недели в формате dd.mm.yyyy. Пример: 12.12.2012, 13.12.2013")
            users[call.message.chat.id][0] = call.data
            users[call.message.chat.id][1][3] = [None, call.data]
    elif call.data == "mu_track_back":
        print("call is track_back")
        new_function = track_functions[max(0, functions.index(users[call.message.chat.id][0]) - 1)]
        eval(new_function + '(call.message)')
    elif data[0] == "my_track":
        my_track(call.message, int(data[1]))
    elif data[0] == "change_track":
        change_track_message(call.message, int(data[1]))
    elif data[0] == "change_warehouse":
        change_warehouse(call.message, int(data[1]))
    elif data[0] == "change_type":
        change_type(call.message, int(data[1]))
    elif data[0] == "change_time":
        change_time(call.message, int(data[1]))
    elif data[0] == "change_quantity":
        bot.send_message(call.message.chat.id, "Укажите необходимый лимит в условном значении. Указывайте точное количества товара в вашей поставке. Это количество указано в скобках рядом с номером заказа в разделе - Управление поставками")
        users[call.message.chat.id][0] = 'change_quantity'
        users[call.message.chat.id][1][0] = int(data[1])
    elif data[0] == "ch_back":
        change_track_message(call.message, int(data[1]))
    elif data[0] == "ch_warehouse":
        track.tracks[int(data[2])]['warehouse_id'] = data[1]
        my_track(call.message, int(data[2]))
    elif data[0] == "ch_type":
        track.tracks[int(data[2])]['type'] = data[1]
        my_track(call.message, int(data[2]))
    elif data[0] == "ch_time":
        today = datetime.date.today()
        if data[1] == "enter_manually":
            bot.send_message(call.message.chat.id, 'Введите даты через запятую, начиная с сегодня и заканчивая не далее чем черз 4 недели в формате dd.mm.yyyy. Пример: 12.12.2012, 13.12.2013')
            users[call.message.chat.id][0] = 'change_time_manually'
        elif data[1] == "today":
            track.tracks[users[call.message.chat.id][1][0]]['time'][0] = [today]
            my_track(call.message, int(data[2]))
        elif data[1] == "tomorrow":
            track.tracks[users[call.message.chat.id][1][0]]['time'][0] = [today + datetime.timedelta(days=1)]
            my_track(call.message, int(data[2]))
        elif data[1] == "week":
            track.tracks[users[call.message.chat.id][1][0]]['time'][0] = [today + datetime.timedelta(days=i) for i in range(7)]
            my_track(call.message, int(data[2]))
        elif data[1] == "until_found":
            track.tracks[users[call.message.chat.id][1][0]]['time'][0] = 'any'
            my_track(call.message, int(data[2]))

    elif data[0] == "remove_track":
        confirm_removal(call.message, int(data[1]))
    elif data[0] == "confirm_yes":
        track.remove(int(data[1]))
        main_menu(call.message)
    elif data[0] == "confirm_no":
        main_menu(call.message)
    elif "yes:" in call.data or "no:" in call.data:
        print("call in yes/no")
        data = call.data.split(':')
        if data[0] == "found_yes" or data[0] == "expired_no":
            track.remove(int(data[1]))
        elif data[0] == "found_no":
            track.run(int(data[1]))
        elif data[0] == "expired_yes":
            track.renew(int(data[1]))
        main_menu(call.message)


    else:
        print("received unknown callback")
        main_menu(call.message)



bot.infinity_polling()
