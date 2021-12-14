from wb_requests import *


class Tracking:
    def __init__(self, warehouses: dict, types: dict, bot: telebot.TeleBot, poll_timeout: int = 10, warehouse_timeout: int = 0.2):
        self.bot = bot
        self.tracks = dict()
        self.user_tracks = dict()
        self.queue = dict()
        self.warehouses = {id1: [] for id1 in warehouses.values()}
        self.inv_warehouses = {warehouses[key]: key for key in warehouses.keys()}
        self.types = types
        self.inv_types = {self.types[key]: key for key in self.types.keys()}
        self.auth3, self.x_supplier_id = get_auth()
        self.poll_timeout = poll_timeout
        self.warehouse_timeout = warehouse_timeout

    def add(self, user_id: int, warehouse_id: str, type1: str, quantity: int, raw_time: (list, str)):
        if len(self.tracks.keys()) != 0:
            not_used_ids = [track_id for track_id in range(max(self.tracks.keys())) if track_id not in self.tracks.keys()]
            if len(not_used_ids) == 0:
                track_id = max(self.tracks.keys()) + 1
            else:
                track_id = min(not_used_ids)
        else:
            track_id = 0
        if type(raw_time[0]) == datetime.datetime:
            time1 = raw_time
        else:
            if raw_time == 'until_found':
                time1 = 'any'
            else:
                time1 = raw_time
        self.tracks[track_id] = {'user_id': user_id, 'warehouse_id': warehouse_id, 'type': type1, 'quantity': quantity, 'time': time1}
        if user_id not in self.user_tracks.keys():
            self.user_tracks[user_id] = [track_id]
        else:
            self.user_tracks[user_id].append(track_id)
        self.run(track_id)
        return track_id

    def pause(self, track_id):
        if track_id in self.queue.keys():
            del self.queue[track_id]
        if track_id in self.warehouses[self.tracks[track_id]['warehouse_id']]:
            self.warehouses[self.tracks[track_id]['warehouse_id']].remove(track_id)

    def remove(self, track_id):
        self.pause(track_id)
        if track_id in self.tracks.keys():
            del self.user_tracks[self.tracks[track_id]['user_id']]
            del self.tracks[track_id]

    def run(self, track_id):
        if track_id in self.tracks.keys():
            self.queue[track_id] = self.tracks[track_id]
            self.warehouses[self.tracks[track_id]['warehouse_id']].append(track_id)

    def renew(self, track_id):
        today = datetime.date.today()
        old_time, time_type = self.tracks[track_id]['time']
        if time_type == "today":
            new_time = [today]
        elif time_type == "tomorrow":
            new_time = [today + datetime.timedelta(days=1)]
        elif time_type == "week":
            new_time = [today + datetime.timedelta(days=i) for i in range(7)]
        self.tracks[track_id]['time'][0] = new_time
        self.run(track_id)

    def validate_tracks(self):
        for track_id in self.queue.keys():
            if self.tracks[track_id]['time'][0][-1] < datetime.date.today():
                self.pause(track_id)
                markup = InlineKeyboardMarkup()
                markup.row_width = 1
                markup.add(InlineKeyboardButton("Я хочу продолжить отслеживание", callback_data=f"expired_no:{track_id}"), InlineKeyboardButton("Я не хочу продолжать отслеживание", callback_data=f"expired_yes:{track_id}"))
                if self.tracks[track_id][time][1] != 'enter_manually':
                    self.bot.send_message(self.tracks[track_id]['user_id'], f"За указанный Вами промежуток времени не было найдено мест для вашей поставки на склад {self.inv_warehouses[self.tracks[track_id]['warehouse']]} {self.tracks[track_id]['quantity']} штук типа {self.inv_types[self.tracks[track_id]['type']]}. Хотите ли Вы продолжить отслеживание лимитов. Параметры отслеживания при этом перенесутся, начиная с сегодняшнего дня.", reply_markup=markup)
                else:
                    self.bot.send_message(self.tracks[track_id]['user_id'], f"За указанный Вами промежуток времени не было найдено мест для вашей поставки на склад {self.inv_warehouses[self.tracks[track_id]['warehouse']]} {self.tracks[track_id]['quantity']} штук типа {self.inv_types[self.tracks[track_id]['type']]}.")

    def check_tracks(self, warehouse, limits):
        for track_id in self.warehouses[warehouse]:
            for date in self.tracks[track_id]['time'][0]:
                if (date in limits.keys() or date == 'any') and limits[date][self.tracks[track_id]['type']] >= self.tracks[track_id]['quantity']:
                    print("найдено место для", track_id)
                    self.pause(track_id)
                    self.bot.send_message(self.tracks[track_id]['user_id'], f"Место для поставки на склад {self.inv_warehouses[self.tracks[track_id]['warehouse_id']]} на {self.tracks[track_id]['quantity']} мест с типом {self.inv_types[self.tracks[track_id]['type']]} найдено на дату {date.strftime('%d.%m.%Y')}")
                    markup = InlineKeyboardMarkup()
                    markup.row_width = 1
                    markup.add(InlineKeyboardButton("Я не успел и хочу продолжить отслеживание", callback_data=f"found_no:{track_id}"), InlineKeyboardButton("Я успел и добавил доставку", callback_data=f"found_yes:{track_id}"))
                    self.bot.send_message(self.tracks[track_id]['user_id'], "Надеюсь вы успели добавить поставку в календарь, но если это не так, то вы можете продолжить отслеживание лимитов и как только они появятся, бот вас сразу оповестит. Параметры отслеживания при этом сохраняются.", reply_markup=markup)
                    break

    def polling(self):
        today_date = datetime.date.today()
        while True:
            print(self.tracks.keys())
            if today_date != datetime.date.today():
                self.validate_tracks()
                today_date = datetime.date.today()
            for warehouse in self.warehouses.keys():
                print("Warehouse:", warehouse, self.warehouses[warehouse])
                if self.warehouses[warehouse]:
                    from_time = datetime.datetime.combine(today_date, datetime.time())
                    to_time = from_time + datetime.timedelta(weeks=4)
                    limits = get_limits(self.auth3, self.x_supplier_id, round(from_time.timestamp()), round(to_time.timestamp()), warehouse)
                    if type(limits) == str:
                        print(limits)
                    else:
                        self.check_tracks(warehouse, limits)
                    time.sleep(self.poll_timeout)
                time.sleep(self.warehouse_timeout)

