import config
import messages
import technique_type
import locations_map
import naruto_battlefield

import sqlite3
import json


import quests

import random

from datetime import datetime
import time

import telebot
from telebot import TeleBot, types, State

from pymongo import MongoClient
#from bson.objectid import ObjectId  
import bson
#для отрисовки
from PIL import Image, ImageDraw, ImageFont, ImageOps
############################################
####### для переназначения exception #######
import sys
import logging
import linecache
############################################
import os

# Инициализируем телеграмм-бота
bot = telebot.TeleBot(config.TOKEN_BOT)
print(bot.get_me())
from pymongo import MongoClient
# Инициализируем клиент для работы с MongoDB
mongo_client = MongoClient(config.DB_URL)
db = mongo_client['narutofandom']
users_collection = db["users"]
characters_collection = db["characters"]
techniques_collection = db["techniques_list"]
quests_collection = db["quests"]
battle_collection = db["battle"]
mobs_collection = db["mobs"]


#Стартовая команда - /start, при ее нажатии бот проверяет есть ли запись о телеграмм пользователе в базе данных, если нет - то создает запись и выводить приветственное сообщение, с коротким описанием нашего проекта системы фандомов. Если запись о пользователе уже есть в БД, то выводится другое короткое приветственное сообщение.
@bot.message_handler(commands=['start'])
def start_handler(message):
    try:
        # Проверяем, есть ли запись о пользователе в базе данных
        user = users_collection.find_one({"telegram_id": message.chat.id})
        
        
        
        if user:
            # клавиатура start
            markup_start = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=False)
            markup_start.row('👤 Профиль', '🗺️ Квесты')
            markup_start.row('🚶‍♂️ Перемещение персонажа')
            markup_start.row('📄 Справка')
            markup_start.row('Симуляция боя TEST APLHA')
            #markup_start.row('🗺️ Текущие игровые локации')
            #markup_start.row('Добавить технику в БД')
        
            # Если пользователь уже есть в БД, выводим короткое приветственное сообщение
            bot.send_message(message.chat.id, messages.ALREADY_REGISTERED_MESSAGE.format(message.from_user.first_name), reply_markup = markup_start)
        else:
            # Если пользователь новый, создаем запись о нем в БД и выводим приветственное сообщение
            new_user = {
                "telegram_id": message.chat.id,
                "username": message.chat.username,
                "first_name": message.chat.first_name,
                "last_name": message.chat.last_name,
                "registration_date": datetime.now()
            }
            users_collection.insert_one(new_user)
            
            # Создаем инлайн-кнопку "Заполнить анкету"
            reply_markup = types.InlineKeyboardMarkup()
            button1 = types.InlineKeyboardButton(text="🆕 Приступить к выбору страны", callback_data="fill_registration[1]_choose_country")
            reply_markup.add(button1)
            
            bot.send_message(message.chat.id, messages.NEW_USER_MESSAGE, reply_markup=reply_markup)
    except:
        PrintException()
        bot.send_message(message.chat.id, 'Какие-то неполадки. Попробуй еще раз.')














# Обработчик для вывода сообщения с информацией о профиле
@bot.message_handler(regexp='Добавить технику в БД')
def add_technique_to_sqlite(message):
    msg = bot.send_message(message.chat.id, f"Скидывай строчку")
    bot.register_next_step_handler(msg, add_technique_to_sqlite_step)


def add_technique_to_sqlite_step(message):
    technique_data = json.loads(message.text)
    # Парсим данные из переданной записи
    _id = technique_data['_id']['$oid']
    elements = ', '.join(technique_data['elements'])
    jutsu_type = technique_data['jutsu_type']
    type = ', '.join(technique_data['type'])
    description = technique_data['description']
    gif = technique_data.get('jpeg', '') # если ключа нет, возвращаем пустую строку
    gif = technique_data.get('gif', '') # если ключа нет, возвращаем пустую строку
    name = technique_data['name']
    rank = technique_data['rank']
    
    conn = sqlite3.connect('main.db')
    
    # Создаем новый объект cur
    cur = conn.cursor()
    
    # Вставляем данные в таблицу techniques
    cur.execute(f"INSERT INTO techniques (_id, elements, jutsu_type, type, description, gif, name, rank) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (_id, elements, jutsu_type, type, description, gif, name, rank))

    # Сохраняем изменения
    conn.commit()

    # Закрываем соединение с базой данных
    conn.close()
    
    bot.send_message(message.chat.id, f'Сохранил йопта')
    









# Обработчик битв | начало
@bot.message_handler(regexp='Симуляция боя TEST APLHA')
def start_simulation(message):
    user = users_collection.find_one({"telegram_id": message.from_user.id})
    character = characters_collection.find_one({"telegram_id": message.from_user.id})
    if not user:
        bot.send_message(message.chat.id, "К сожалению, я не нашел ваш профиль.")
        return

    reply_markup = types.InlineKeyboardMarkup()       
    button_1 = types.InlineKeyboardButton(text=f'➡️ Начать симуляцию боя', callback_data=f"start_battle_simulation")
    reply_markup.add(button_1)
            
    bot.send_message(message.chat.id, f'Выберите нужный вариант:', reply_markup = reply_markup)
    #bot.register_next_step_handler(msg, start_battle_create_location, opponents_list)
    pass


# обработчик для кнопки start_battle_simulation
@bot.callback_query_handler(func=lambda call: call.data.startswith('start_battle_simulation'))
def start_battle_simulation_callback(call):
    user = users_collection.find_one({"telegram_id": call.message.chat.id})
    user_character = characters_collection.find_one({"telegram_id": call.message.chat.id})
    if not user:
        bot.send_message(call.message.chat.id, "К сожалению, я не нашел ваш профиль.")
        return
    
    characters = list(characters_collection.find())
    player_character_id = user_character["telegram_id"]
    
    battle_id = naruto_battlefield.create_battle_and_record_to_db(call.message.chat.id)
    
    reply_markup = types.InlineKeyboardMarkup()
    for character in characters:
        if character['telegram_id'] == player_character_id:
            continue
        button_text = f"{character['name']}"
        callback_data = f"[SIMBAT]_CO:{str(character['telegram_id'])}:{battle_id}_check"
        button = types.InlineKeyboardButton(text=button_text, callback_data=callback_data)
        reply_markup.add(button)

    bot.edit_message_text('♨️ Выберите соперников боя:', call.message.chat.id, call.message.message_id, reply_markup=reply_markup)


# обработчик для выбора оппонентов боя
@bot.callback_query_handler(func=lambda call: call.data.startswith('[SIMBAT]_CO'))
def select_opponent_callback(call):
    battle_id = call.data.split(':')[2]
    battle_id = battle_id.split('_')[0]

    # Получаем информацию о текущем бое
    current_battle = battle_collection.find_one({"_id": bson.ObjectId(battle_id)})
    if not current_battle:
        bot.send_message(call.message.chat.id, "К сожалению, я не нашел информацию о бое.")
        return
    
    # Получаем информацию о пользователе, который вызвал функцию
    user = users_collection.find_one({"telegram_id": call.message.chat.id})
    user_character = characters_collection.find_one({"telegram_id": call.message.chat.id})
    if not user:
        bot.send_message(call.message.chat.id, "К сожалению, я не нашел ваш профиль.")
        return
    
    # Получаем информацию об оппонентах
    list_of_opponents = current_battle["list_of_opponents"]
    
    # Получаем информацию об оппоненте, на которого нажал пользователь
    opponent_id = int(call.data.split(":")[1])
    opponent = characters_collection.find_one({"telegram_id": opponent_id})
    
    # Проверяем, есть ли оппонент уже в списке оппонентов
    opponent_found = False
    for team in list_of_opponents:
        for player in team["players"]:
            if int(player["player_id"]) == opponent_id:
                team["players"].remove(player)
                opponent_found = True
                break
        if opponent_found:
            break

    # Если оппонент не найден, то добавляем его в список оппонентов
    if not opponent_found:
        new_battle = naruto_battlefield.add_opponent_to_battle(opponent_id, battle_id)
    
    
    # Перерисовываем клавиатуру с именами персонажей и эмодзи
    characters = list(characters_collection.find())
    player_character_id = user_character["telegram_id"]
    
    reply_markup = types.InlineKeyboardMarkup()
    for character in characters:
        if character['telegram_id'] == player_character_id:
            continue
        
        button_text = f"{character['name']}"
        callback_data = f"[SIMBAT]_CO:{str(character['telegram_id'])}:{battle_id}_check"
        # Отмечаем оппонентов зеленым, если они уже выбраны
        opponent_already_chosen = False
        for team in list_of_opponents:
            for player in team["players"]:
                if int(player["player_id"]) == character["telegram_id"]:
                    button_text += " ✅"
                    opponent_already_chosen = True
                    break
            if opponent_already_chosen:
                break
        
        button = types.InlineKeyboardButton(text=button_text, callback_data=callback_data)
        reply_markup.add(button)

    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=reply_markup)





""" # обработчик для кнопок-переключателей оппонентов
@bot.callback_query_handler(func=lambda call: call.data.startswith('[SIMBAT]_CO:'))
def toggle_opponent_callback(call):
    # парсим данные из callback_data
    _, opponent_id, battle_id, _ = call.data.split(':')

    current_battle = battle_collection.find_one({"_id": bson.ObjectId(battle_id)})

    if 'check' in call.data:
        # Добавляем участника в список соперников
        new_battle = naruto_battlefield.add_opponent_to_battle(opponent_id, battle_id)
        list_of_opponents = new_battle["list_of_opponents"]
    elif 'uncheck' in call.data:
        # Проверяем, что игрока еще нет в списке соперников
        for team in current_battle["list_of_opponents"]:
            for player in team["players"]:
                if player["player_id"] == opponent_id:
                    # Удаляем участника из списка соперников
                    new_battle = naruto_battlefield.delete_opponent_from_battle(opponent_id, battle_id)
                    list_of_opponents = new_battle["list_of_opponents"]
        

    # Create a list of all characters except the current user
    characters = list(characters_collection.find({"telegram_id": {"$ne": call.from_user.id}}))

    # Create a keyboard markup with buttons for all characters
    reply_markup = types.InlineKeyboardMarkup()
    for char in characters:
        is_participant = False
        for team in list_of_opponents:
            for player in team['players']:
                if char['telegram_id'] == player['player_id']:
                    is_participant = True
                    break
            if is_participant:
                break

        if is_participant:
            emodji = '✅'
            callback_data = f"[SIMBAT]_choose_opponent:{str(char['telegram_id'])}:{battle_id}"
        else:
            emodji = '⭕️'
            callback_data = f"[SIMBAT]_choose_opponent:{str(char['telegram_id'])}:{battle_id}"
 
        button_text = f"{emodji} {char['name']}"
        button = types.InlineKeyboardButton(text=button_text, callback_data=callback_data)
        reply_markup.add(button)

    # Add "Start Battle" button
    button_text = 'Выбор сделан, начать бой'
    callback_data = f'simulation_battle_start_battle:{battle_id}'
    button = types.InlineKeyboardButton(text=button_text, callback_data=callback_data)
    reply_markup.add(button)

    # Edit the message with the updated keyboard markup
    bot.edit_message_text('♨️ Выберите соперников боя:', call.message.chat.id, call.message.message_id, reply_markup=reply_markup) """



@bot.callback_query_handler(func=lambda call: call.data.startswith('simulation_battle_start_battle'))
def start_battle_callback(call):
    curernt_battle_id = call.data.replace('simulation_battle_start_battle:', '')
    current_battle = battle_collection.find_one({"_id": bson.ObjectId(curernt_battle_id)})
    selected_characters = current_battle["list_of_opponents"]
    print(selected_characters)
    #selected_characters = call.data.replace('simulation_battle_start_battle:', '').split(',')
    if len(selected_characters) < 2:
        bot.answer_callback_query(callback_query_id=call.id, text="Необходимо выбрать хотя бы двух персонажей!")
        return
        # Начало битвы
    else:
        num_of_opponents = len(selected_characters)
        opponents_list = selected_characters

        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_battle_create_location(call.message, num_of_opponents, opponents_list, current_battle)

    # Очищаем переменную
    selected_characters = []




# функция для создания участка леса заданного размера и координатами верхнего левого угла
def create_forest(x, y, width, height, battle_field):
    # если ширина или высота участка леса меньше 3, то выходим из рекурсии
    if width < 3 or height < 3:
        return

    # случайным образом выбираем, какую линию использовать для разбиения
    if random.random() < 0.5:
        # горизонтальное разбиение
        wall_y = random.randint(y+1, y+height-2)

        # случайно выбираем количество деревьев в группе
        num_trees = random.randint(5, 15)

        # случайным образом выбираем место для каждого дерева в группе
        for i in range(num_trees):
            tree_x = random.randint(x+1, x+width-2)
            tree_y = random.randint(wall_y-num_trees+1, wall_y-1)
            battle_field[tree_y][tree_x]['object'] = 'tree_1'

        # создаем два новых участка леса
        create_forest(x, y, width, wall_y-y, battle_field)
        create_forest(x, wall_y+1, width, y+height-wall_y-1, battle_field)

    else:
        # вертикальное разбиение
        wall_x = random.randint(x+1, x+width-2)

        # случайно выбираем количество деревьев в группе
        num_trees = random.randint(5, 15)

        # случайным образом выбираем место для каждого дерева в группе
        for i in range(num_trees):
            tree_x = random.randint(wall_x-num_trees+1, wall_x-1)
            tree_y = random.randint(y+1, y+height-2)
            battle_field[tree_y][tree_x]['object'] = 'tree_2'

        # создаем два новых участка леса
        create_forest(x, y, wall_x-x, height, battle_field)
        create_forest(wall_x+1, y, x+width-wall_x-1, height, battle_field)
    
    return battle_field



# Функция принимает координаты центральной точки карты, длину и ширину дороги, а также поле боя, 
# на котором нужно создать дорогу. Функция случайным образом выбирает направление движения и продвигается 
# в этом направлении, устанавливая на каждую клетку дорожный объект, пока не достигнет нужной длины или 
# не выйдет за пределы поля боя. Если следующая клетка находится за пределами поля боя, 
# генерация дороги прерывается.
def create_roads(x, y, battle_field):
    num_roads = random.randint(3, 7)
    roads = []
    for i in range(num_roads):
        # длина и ширина дороги также могут быть случайными
        length = random.randint(5, 15)
        width = random.randint(1, 3)

        # начинаем с центральной точки карты
        curr_x, curr_y = x, y

        # случайным образом выбираем направление
        direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])

        # продвигаемся в выбранном направлении, пока не достигнем нужной длины
        for j in range(length):
            # проверяем, что следующая клетка находится внутри поля боя
            if 0 <= curr_x+direction[0] < len(battle_field) and 0 <= curr_y+direction[1] < len(battle_field[0]):
                # устанавливаем на текущую клетку дорожный объект
                battle_field[curr_x][curr_y]['object'] = 'road'
                # перемещаемся в следующую клетку
                curr_x += direction[0]
                curr_y += direction[1]
            else:
                # если следующая клетка находится за пределами поля боя, прерываем генерацию дороги
                break

        # добавляем дорогу в список
        roads.append((x, y, length, width))

    return battle_field



# Функция для создания камней на поле боя
def create_stones(num_stones, battle_field):
    # получаем размеры поля боя
    rows = len(battle_field)
    cols = len(battle_field[0])
    # создаем заданное количество камней
    for i in range(num_stones):
        # случайным образом выбираем координаты для камня
        stone_row = random.randint(0, rows-1)
        stone_col = random.randint(0, cols-1)

        # проверяем, что на выбранной клетке нет других объектов
        if 'object' in battle_field[stone_row][stone_col] and battle_field[stone_row][stone_col]['object'] == None:
            # устанавливаем на выбранную клетку камень
            battle_field[stone_row][stone_col]['object'] = 'rock'
    
    return battle_field




# Обработчик битв | создаем поле боя
import numpy as np

def start_battle_create_location(message, num_of_opponents, opponents_list, current_battle):
    cell_size = (50, 50)
    image_size = (15*cell_size[0], 15*cell_size[1])
    battle_field = []

    current_battle_id = current_battle["_id"]

    for y in range(15):
        row = []
        for x in range(15):
            row.append({'x': x, 'y': y, 'object': None}) # добавляем ключ 'object' в каждый элемент массива
        battle_field.append(row)


    print('test 387 hey')
    # создаем участки леса с помощью алгоритма рекурсивного разбиения
    battle_field = create_forest(0, 0, 14, 14, battle_field)

    # создаем дорогу с помощью случайного блуждания
    battle_field = create_roads(8, 8, battle_field)

    # создаем участок камней
    num_of_stones = random.randint(3, 8)
    battle_field = create_stones(num_of_stones, battle_field)
    

    # добавляем игроков и мобов
    player_positions = []
    for team in opponents_list:
        for player in team["players"]:
            if 'player_id' in player:
                # случайно генерируем позицию игрока
                while True:
                    player_x, player_y = (random.randint(0, 14), random.randint(0, 14))
                    if 'object' in battle_field[player_y][player_x] and battle_field[player_y][player_x]['object'] is None:
                        break
                player_positions.append((player_x, player_y))
                battle_field[player_y][player_x]['object'] = f'player_{player["player_id"]}'
            elif 'mob_id' in player:
                # случайно генерируем позицию моба
                while True:
                    mob_x, mob_y = (random.randint(0, 14), random.randint(0, 14))
                    if battle_field[mob_y][mob_x]['object'] is None:
                        break
                player_positions.append((mob_x, mob_y))
                battle_field[mob_y][mob_x]['object'] = 'mob'

    
    # Обновляем запись о бое (battle field) в БД
    battle_collection.update_one({"_id": bson.ObjectId(current_battle_id)}, {"$set": {"battle_field": battle_field}})
    
    # создаем изображение
    image = Image.new('RGBA', image_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)


    STATS_rock = 0
    STATS_tree = 0
    STATS_building = 0
    # рисуем клетки и объекты
    for y in range(15):
        for x in range(15):
            cell = battle_field[y][x]
            if 'object' in cell:
                object_type = cell['object']

                if object_type == 'rock':
                    STATS_rock += 1
                elif object_type == 'tree_1' or object_type == 'tree_2':
                    STATS_tree += 1
                elif object_type == 'building':
                    STATS_building += 1

                object_image_path = f'./images_resources/battle_field_grass.png'
                object_image = Image.open(object_image_path).convert('RGBA')
                object_image = object_image.resize(cell_size, resample=Image.LANCZOS)
                # случайно выбираем угол поворота изображения
                angle = random.choice([90, 180])
                # поворачиваем изображение
                object_image = object_image.rotate(angle, expand=True)
                image.alpha_composite(object_image, dest=(x*cell_size[0], y*cell_size[1]))

                if object_type == None:
                    continue
                else:
                    if "player" in object_type:
                        object_type = object_type.split('_')[0]
                    object_image_path = f'./images_resources/battle_field_{object_type}.png'
                    object_image = Image.open(object_image_path).convert('RGBA')
                    # invert alpha channel
                    alpha = object_image.getchannel('A')
                    inverted_alpha = alpha.point(lambda x: 255 - x)
                    # set inverted alpha as new alpha channel
                    object_image.putalpha(alpha)
                    object_image = object_image.resize(cell_size, resample=Image.LANCZOS)
                    image.alpha_composite(object_image, dest=(x*cell_size[0], y*cell_size[1]))
            else:
                draw.rectangle([(x*cell_size[0], y*cell_size[1]), ((x+1)*cell_size[0], (y+1)*cell_size[1])], fill=(128, 128, 128), outline=(0, 0, 0))

    reply_markup = types.InlineKeyboardMarkup()
    button_1 = types.InlineKeyboardButton(text=f'😡 Начать бой!', callback_data=f"start_battle:{current_battle_id}")
    reply_markup.add(button_1)

    # сохраняем изображение и отправляем пользователю
    image_path = 'battle_field.png'
    image.save(image_path)
    with open(image_path, 'rb') as image_file:
        photo = bot.send_photo(message.chat.id, image_file, caption = f'Обьекты на карте:\n🪨 Камень - {STATS_rock}\n🌲 Дерево - {STATS_tree}\n🏯 Здание - {STATS_building}\n\n', reply_markup=reply_markup)
        photo_id = photo.photo[-1].file_id
        battle_collection.update_one({"_id": bson.ObjectId(current_battle_id)}, {"$set": {"image": photo_id}})

    # удаляем файл
    os.remove(image_path)



@bot.callback_query_handler(func=lambda call: call.data.startswith('start_battle:'))
def choose_type_of_battle_callback(call):
    user = users_collection.find_one({"telegram_id": call.message.chat.id})
    character = characters_collection.find_one({"telegram_id": call.message.chat.id})
    if not user:
        bot.send_message(call.message.chat.id, "К сожалению, я не нашел ваш профиль.")
        return
    
    battle_id = call.data.replace('start_battle:', '')
    current_battle = battle_collection.find_one({"_id": bson.ObjectId(battle_id)})

    # Вычисляем инитиативу для каждого персонажа
    initiative_scores = {}
    for team in current_battle['list_of_opponents']:
        for player in team["players"]:
            character = characters_collection.find_one({"telegram_id": player['player_id']})
            if character:
                initiative = character["characteristics"][0]['dexterity'] + character["characteristics"][0]['speed'] + character["characteristics"][0]['luck']
                initiative_scores[player['player_id']] = initiative

    # Сортируем персонажей по инитиативе
    sorted_initiatives = sorted(initiative_scores.items(), key=lambda x: x[1], reverse=True)

    # Определяем первого игрока
    first_player_id = sorted_initiatives[0][0]

    reply_markup = types.InlineKeyboardMarkup()
    button_1 = types.InlineKeyboardButton(text=f'Вверх', callback_data=f"[BATTLE]:{battle_id}:move_up")
    button_2 = types.InlineKeyboardButton(text=f'Вниз', callback_data=f"[BATTLE]:{battle_id}:move_down")
    button_3 = types.InlineKeyboardButton(text=f'Вправо', callback_data=f"[BATTLE]:{battle_id}:move_right")
    button_4 = types.InlineKeyboardButton(text=f'Влево', callback_data=f"[BATTLE]:{battle_id}:move_left")
    button_5 = types.InlineKeyboardButton(text=f'Навык', callback_data=f"[BATTLE]:{battle_id}:use_skill")
    button_6 = types.InlineKeyboardButton(text=f'Предмет', callback_data=f"[BATTLE]:{battle_id}:use_item")
    button_7 = types.InlineKeyboardButton(text=f'Отмена', callback_data=f"[BATTLE]:{battle_id}:cancel_battle")
    reply_markup.add(button_1)
    reply_markup.add(button_2)
    reply_markup.add(button_3)
    reply_markup.add(button_4)
    reply_markup.add(button_5)
    reply_markup.add(button_6)
    reply_markup.add(button_7)

    info_about_battle = f'Бой начался! Первым ход совершает персонаж {characters_collection.find_one({"telegram_id": first_player_id})["name"]}\n\nСписок участников:\n'
    for i, team in enumerate(current_battle['list_of_opponents']):
        info_about_battle += f"\nКоманда {i + 1}: {team['team_name']}"
        for player in team["players"]:
            character = characters_collection.find_one({"telegram_id": player['player_id']})
            if character:
                info_about_battle += f"\n- {character['name']}"
            else:
                info_about_battle += f"\n- Игрок с id {player['player_id']}"

    bot.delete_message(call.message.chat.id, call.message.message_id)
    # отправляем сообщение всем игрокам в поединке
    for team in current_battle['list_of_opponents']:
        for player in team["players"]:
            if 'player_id' in player:
                bot.send_photo(player["player_id"], current_battle["image"], caption=info_about_battle, reply_markup=reply_markup)










@bot.callback_query_handler(func=lambda call: call.data.startswith('[BATTLE]:'))
def handle_battle_callback(call):
    _, battle_id, action = call.data.split(':')
    user = users_collection.find_one({"telegram_id": call.message.chat.id})
    character = characters_collection.find_one({"telegram_id": call.message.chat.id})
    current_battle = battle_collection.find_one({"_id": bson.ObjectId(battle_id)})

    print(character)
    print(current_battle)

    if not user:
        bot.send_message(call.message.chat.id, "К сожалению, я не нашел ваш профиль.")
        return

    if action == 'move_up':
        # реализация движения вверх
        move_player(character, "up", current_battle)

    elif action == 'move_down':
        # реализация движения вниз
        move_player(character, "down", current_battle)

    elif action == 'move_right':
        # реализация движения вправо
        move_player(character, "right", current_battle)

    elif action == 'move_left':
        # реализация движения влево
        move_player(character, "left", current_battle)

    elif action == 'use_skill':
        # реализация использования навыка
        skill_id = get_skill_id_from_player_menu(current_battle, character)
        use_skill(character, skill_id, current_battle)

    elif action == 'use_item':
        # реализация использования предмета
        item_id = get_item_id_from_player_menu(current_battle, character)
        use_item(character, item_id, current_battle)

    elif action == 'cancel':
        # реализация отмены действия
        cancel_action(character, current_battle)

    else:
        bot.send_message(call.message.chat.id, "Ошибка: неизвестное действие")



def get_current_position(character, current_battle):
    for row in current_battle["battle_field"]:
        for cell in row:
            if "player" in cell["object"]:
                player_id = cell["object"].replace("player_", "")
                if player_id == character["telegram_id"]:
                    return {"x": cell["x"], "y": cell["y"]}


def update_character_position(character, current_battle, new_x, new_y):
    """Обновляет координаты персонажа в боевой сессии."""
    for team in current_battle["list_of_opponents"]:
        for player in team["players"]:
            if player["player_id"] == character["telegram_id"]:
                player["x"], player["y"] = new_x, new_y
                break
    else:
        # Если персонаж не найден в списке игроков, создаем его
        current_battle["list_of_opponents"][0]["players"].append({
            "player_id": character["telegram_id"],
            "x": new_x,
            "y": new_y,
            "start_battle": False
        })




def move_player(character, direction, current_battle):
    # получаем текущие координаты персонажа
    current_position = get_current_position(character, current_battle)
    x, y = current_position["x"], current_position["y"]

    # в зависимости от направления вычисляем новые координаты
    if direction == "up":
        new_x, new_y = x, y - 1
    elif direction == "down":
        new_x, new_y = x, y + 1
    elif direction == "right":
        new_x, new_y = x + 1, y
    elif direction == "left":
        new_x, new_y = x - 1, y

    # проверяем, что новые координаты не выходят за пределы поля боя
    if new_x < 0 or new_y < 0 or new_x >= len(current_battle["battle_field"][0]) or new_y >= len(current_battle["battle_field"]):
        bot.send_message(character["telegram_id"], "Вы не можете двигаться в этом направлении.")
        return

    # проверяем, что на новых координатах нет другого объекта
    new_position = current_battle["battle_field"][new_y][new_x]
    if new_position["object"] is not None:
        bot.send_message(character["telegram_id"], "Вы не можете перейти на эту клетку.")
        return

    # обновляем координаты персонажа
    update_character_position(character, current_battle, new_x, new_y)

    # сообщаем игрокам о перемещении персонажа
    #update_battle_message(current_battle)





















#метод для выдачи базовых квестов при регистрации персонажа
def give_basic_quests_to_character(player_telegram_id):
    character = characters_collection.find_one({'telegram_id': player_telegram_id})
    quests_player_info = quests_collection.find_one({'telegram_id': player_telegram_id})

    # проверяем, что список активных квестов не пустой
    #if not quests_player_info['list_of_active_quests']:
      #  quests_player_info['list_of_active_quests'] = []

    for quest_name, quest_data in quests.base_quests.items():
        if 'character_registration_flag' in quest_data['conditions_to_accepting']:
            # проверяем, что квест еще не был добавлен ранее
            if not any(q['name'] == quest_name for q in quests_player_info['list_of_active_quests']):
                # добавляем квест в список активных квестов персонажа
                new_quest = {
                    'name': quest_name,
                    'quest_id': bson.ObjectId()
                }
                quests_player_info['list_of_active_quests'].append(new_quest)
    
    # обновляем запись персонажа в БД
    quests_collection.update_one({'telegram_id': player_telegram_id}, {'$set': quests_player_info})














# обработчик для кнопки fill_registration
@bot.callback_query_handler(func=lambda call: call.data.startswith('fill_registration'))
def fill_registration_callback(call):
    # Обработчик выбора страны
    if call.data.startswith('fill_registration[1]'):
        # Проверяем, есть ли запись о пользователе в базе данных
        character = characters_collection.find_one({"telegram_id": call.message.chat.id})
        
        if character:
            bot.edit_message_text(f'‼️ У вас уже есть персонаж!', call.message.chat.id, call.message.message_id)
        else:
            if call.data.startswith('fill_registration[1]_choose_country'):
                # Cоздаем запись в БД о персонаже пользователя
                new_character = {
                    "telegram_id": call.message.chat.id,
                    "username": call.message.chat.username,
                    "country": 'NoneYet',
                    "name": 'NoneYet',
                    "level": 1,
                    "current_exp": 0,
                    "lvlup_exp": 100,
                    "money": 0,
                    "gender": 'NoneYet',
                    "biography": 'NoneYet',
                    "element": 'NoneYet',
                    "basic_jutsu": 'NoneYet',
                    "shinobi_rank": 'NoneYet',
                    "current_location": "NoneYet",
                    
                    "characteristics": [{
                    "atack": 1,
                    "defense": 1,
                    "health": 100,
                    "chakra": 100,
                    "speed": 1,
                    "dexterity": 1,
                    "critical_chance": 1,
                    "luck": 1
                    }],
                    "inventory": [{
                        "Камень": [{
                            "count": 5,
                            "description": "Обычный камень, можно отпугивать животных",
                            "id": bson.ObjectId()
                        }]
                    }]
                }
                characters_collection.insert_one(new_character)

                quests_for_character = {
                    "telegram_id": call.message.chat.id,
                    "number_of_completed_dailies": 0,
                    "number_of_completed_quests": 0,
                    "list_of_active_dailies": [],
                    "list_of_active_quests": []
                }
                quests_collection.insert_one(quests_for_character)
                #Даем базовые квесты для игрока
                give_basic_quests_to_character(call.message.chat.id)

                reply_markup = types.InlineKeyboardMarkup()
                button1 = types.InlineKeyboardButton(text="🌐Страна Ветра", callback_data=f'fill_registration[2]_wind')
                button2 = types.InlineKeyboardButton(text="‍🌐Страна Воды", callback_data=f'fill_registration[2]_water')
                button3 = types.InlineKeyboardButton(text="🌐Страна Земли", callback_data=f'fill_registration[2]_earth')
                button4 = types.InlineKeyboardButton(text="🌐Страна Молнии", callback_data=f'fill_registration[2]_lightning')
                button5 = types.InlineKeyboardButton(text="🌐Страна Огня", callback_data=f'fill_registration[2]_fire')
                reply_markup.add(button1)
                reply_markup.add(button2)
                reply_markup.add(button3)
                reply_markup.add(button4)
                reply_markup.add(button5)
                
                bot.send_message(call.message.chat.id, f'Выберите страну. От ее выбора зависит какую деревню вы сможете выбрать. Выбор можно отменить до окончания регистрации персонажа.', reply_markup = reply_markup)
    if call.data.startswith('fill_registration[2]'):
        choosen_country = call.data.replace('fill_registration[2]_', '')
        
        characters_collection.update_one({"telegram_id": call.message.chat.id}, {"$set": {"country": choosen_country, "current_location": f"{choosen_country}_country"}})
        
        reply_markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton(text="🎲 Пусть судьба определит твою стихию", callback_data=f'fill_registration[3]_get_random_element')
        reply_markup.add(button1)
        
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, f'Отлично! Ты выбрал страну {choosen_country}\n\nТеперь нужно определить каким типом чакры будет обладать твой персонаж. Существует 5 базовых типов чакры:\nСтихия Ветра\nСтихия Воды\nСтихия Земли\nСтихия Молнии\nСтихия Огня\n\nТакже, существуют стихии улучшенного генома. Это особый тип, который можно будет получить в процессе игры.\n\nНажми кнопку ниже для определение твоей базовой стихии:', reply_markup = reply_markup)
    if call.data.startswith('fill_registration[3]'):
        bot.edit_message_text(call.message.text, call.message.chat.id, call.message.message_id)
        # Отправляем сообщение с броском кубика
        dice_message = bot.send_dice(call.message.chat.id)
        dice_value = dice_message.dice.value
        element = None
        
         # Определяем стихию в зависимости от значения кубика
        if dice_value == 1:
            element = "water"
            element_text = "💧 Вода"
        elif dice_value == 2:
            element = "earth"
            element_text = "🗿 Земля"
        elif dice_value == 3:
            element = "fire"
            element_text = "🔥 Огонь"
        elif dice_value == 4:
            element = "wind"
            element_text = "💨 Ветер"
        elif dice_value == 5:
            element = "lightning"
            element_text = "⚡️ Молния"
            
        
            
        elif dice_value == 6:
            # При выпадении значения 6
            
            reply_markup = types.InlineKeyboardMarkup()
            button1 = types.InlineKeyboardButton(text="💧 Вода", callback_data=f'fill_registration[3_1]_water')
            button2 = types.InlineKeyboardButton(text="🗿 Земля", callback_data=f'fill_registration[3_1]_earth')
            button3 = types.InlineKeyboardButton(text="🔥 Огонь", callback_data=f'fill_registration[3_1]_fire')
            button4 = types.InlineKeyboardButton(text="💨 Ветер", callback_data=f'fill_registration[3_1]_wind')
            button5 = types.InlineKeyboardButton(text="⚡️ Молния", callback_data=f'fill_registration[3_1]_lightning')
            reply_markup.add(button1)
            reply_markup.add(button2)
            reply_markup.add(button3)
            reply_markup.add(button4)
            reply_markup.add(button5)
            
            
            
            bot.send_message(call.message.chat.id, "Тебе выпало 6! Это позволяет выбрать стихию самостоятельно. Выбор нельзя отменить.", reply_markup=reply_markup)
        
        if element is not None:
            # Записываем выбранную стихию в базу данных
            characters_collection.update_one({"telegram_id": call.message.chat.id}, {"$set": {"element": element}})
            # Отправляем сообщение с выбранной стихией 
            reply_markup = types.InlineKeyboardMarkup()
            button1 = types.InlineKeyboardButton(text="Ниндзюцу", callback_data=f'fill_registration[4_1]_ninjutsu')
            button2 = types.InlineKeyboardButton(text="Тайдзюцу", callback_data=f'fill_registration[4_1]_taijutsu')
            button3 = types.InlineKeyboardButton(text="Гендзюцу", callback_data=f'fill_registration[4_1]_genjutsu')
            reply_markup.add(button1)
            reply_markup.add(button2)
            reply_markup.add(button3)
            

            bot.send_message(call.message.chat.id, f"Тебе выпало {dice_value}! Твоя стихия - {element_text}.{messages.REGISTRATION_CHOOSE_JUTSU_MESSAGE}", reply_markup=reply_markup)
        
    if call.data.startswith('fill_registration[3_1]'):    
        element = call.data.replace('fill_registration[3_1]_', '')
        # Записываем выбранную стихию в базу данных
        characters_collection.update_one({"telegram_id": call.message.chat.id}, {"$set": {"element": element}})
        # Отправляем сообщение с выбранной стихией
        reply_markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton(text="Ниндзюцу", callback_data=f'fill_registration[4_1]_ninjutsu')
        button2 = types.InlineKeyboardButton(text="Тайдзюцу", callback_data=f'fill_registration[4_1]_taijutsu')
        button3 = types.InlineKeyboardButton(text="Гендзюцу", callback_data=f'fill_registration[4_1]_genjutsu')
        reply_markup.add(button1)
        reply_markup.add(button2)
        reply_markup.add(button3)
        
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, f"Хороший выбор! Твоя стихия - {element}.{messages.REGISTRATION_CHOOSE_JUTSU_MESSAGE}", reply_markup=reply_markup)
    
    if call.data.startswith('fill_registration[4_1]'):  
        bot.delete_message(call.message.chat.id, call.message.message_id)
        jutsu = call.data.replace('fill_registration[4_1]_', '')

        reply_markup = types.InlineKeyboardMarkup()
        
        if jutsu == 'ninjutsu':
            button1 = types.InlineKeyboardButton(text="Да, подтвердить выбор", callback_data=f'fill_registration[4_2]_yes_ninjutsu')
            button2 = types.InlineKeyboardButton(text="Выбрать другое дзюцу", callback_data=f'fill_registration[4_2]_no')
            reply_markup.add(button1)
            reply_markup.add(button2)
            bot.send_message(call.message.chat.id, f"{messages.REGISTRATION_NINJUTSU_MESSAGE}\n\nВы уверены, что хотите выбрать этот тип дзюцу?", reply_markup=reply_markup)
        elif jutsu == 'genjutsu':
            button1 = types.InlineKeyboardButton(text="Да, подтвердить выбор", callback_data=f'fill_registration[4_2]_yes_genjutsu')
            button2 = types.InlineKeyboardButton(text="Выбрать другое дзюцу", callback_data=f'fill_registration[4_2]_no')
            reply_markup.add(button1)
            reply_markup.add(button2)
            bot.send_message(call.message.chat.id, f"{messages.REGISTRATION_GENJUTSU_MESSAGE}\n\nВы уверены, что хотите выбрать этот тип дзюцу?", reply_markup=reply_markup)
        elif jutsu == 'taijutsu':
            button1 = types.InlineKeyboardButton(text="Да, подтвердить выбор", callback_data=f'fill_registration[4_2]_yes_taijutsu')
            button2 = types.InlineKeyboardButton(text="Выбрать другое дзюцу", callback_data=f'fill_registration[4_2]_no')
            reply_markup.add(button1)
            reply_markup.add(button2)
            bot.send_message(call.message.chat.id, f"{messages.REGISTRATION_TAIJUTSU_MESSAGE}\n\nВы уверены, что хотите выбрать этот тип дзюцу?", reply_markup=reply_markup)
    if call.data.startswith('fill_registration[4_2]'):    
        confirm_or_not = call.data.replace('fill_registration[4_2]_', '')    
        if 'yes' in confirm_or_not:
            jutsu = confirm_or_not.replace('yes_', '')
            # Записываем выбранный тип дзюцу в базу данных
            characters_collection.update_one({"telegram_id": call.message.chat.id}, {"$set": {"basic_jutsu": jutsu}})
            
            reply_markup = types.InlineKeyboardMarkup()
            button1 = types.InlineKeyboardButton(text="Женский", callback_data=f'fill_registration[5_1]_woman')
            button2 = types.InlineKeyboardButton(text="Мужской", callback_data=f'fill_registration[5_1]_man')
            reply_markup.add(button1)
            reply_markup.add(button2)
            bot.edit_message_text(f"Отлично! Теперь твой базовый тип дзюцу - {jutsu}\n\nТеперь настало время выбрать пол для твоего персонажа:", call.message.chat.id, call.message.message_id, reply_markup = reply_markup)
        else:
            reply_markup = types.InlineKeyboardMarkup()
            button1 = types.InlineKeyboardButton(text="Ниндзюцу", callback_data=f'fill_registration[4_1]_ninjutsu')
            button2 = types.InlineKeyboardButton(text="Тайдзюцу", callback_data=f'fill_registration[4_1]_taijutsu')
            button3 = types.InlineKeyboardButton(text="Гендзюцу", callback_data=f'fill_registration[4_1]_genjutsu')
            reply_markup.add(button1)
            reply_markup.add(button2)
            reply_markup.add(button3)
            
            bot.edit_message_text(f"{messages.REGISTRATION_CHOOSE_JUTSU_MESSAGE}", call.message.chat.id, call.message.message_id, reply_markup = reply_markup)
    if call.data.startswith('fill_registration[5_1]'):
        gender = call.data.replace('fill_registration[5_1]_', '')    
        
        reply_markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton(text="Да, подтвердить выбор", callback_data=f'fill_registration[5_2]_yes_{gender}')
        button2 = types.InlineKeyboardButton(text="Выбрать другой пол", callback_data=f'fill_registration[5_2]_no')
        reply_markup.add(button1)
        reply_markup.add(button2)
        
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, f"Пол нельзя изменить в процессе игры. Вы уверены, что хотите выбрать этот пол?", reply_markup=reply_markup)
    if call.data.startswith('fill_registration[5_2]'):
        confirm_or_not = call.data.replace('fill_registration[5_2]_', '')    
        
        if 'yes' in confirm_or_not:
            #bot.delete_message(call.message.chat.id, call.message.message_id)
            gender = confirm_or_not.replace('yes_', '')
            # Записываем выбранный тип дзюцу в базу данных
            characters_collection.update_one({"telegram_id": call.message.chat.id}, {"$set": {"gender": gender}})
            msg = bot.send_message(call.message.chat.id, f"Последний вопрос! Имя вашего персонажа. Можно использовать как Имя Фамилия, так и никнеймы. Введите ваш ответ:")
            bot.register_next_step_handler(msg, register_choose_character_name_step)
        else:
            reply_markup = types.InlineKeyboardMarkup()
            button1 = types.InlineKeyboardButton(text="Женский", callback_data=f'fill_registration[5_1]_woman')
            button2 = types.InlineKeyboardButton(text="Мужской", callback_data=f'fill_registration[5_1]_man')
            reply_markup.add(button1)
            reply_markup.add(button2)
            
            bot.edit_message_text(f"Теперь настало время выбрать пол для твоего персонажа:", call.message.chat.id, call.message.message_id, reply_markup = reply_markup)


# Обработчик выбора имени персонажа | Финальный вопрос регистрации
def register_choose_character_name_step(message):
    # Записываем имя персонажа в базу данных
    characters_collection.update_one({"telegram_id": message.chat.id}, {"$set": {"name": message.text}})
    
    reply_markup = types.InlineKeyboardMarkup()
    button_1 = types.InlineKeyboardButton(text="📜 Мой персонаж", callback_data="show_my_character")
    reply_markup.add(button_1)
    
    bot.send_message(message.chat.id, f'Твое имя - {message.text}', reply_markup = reply_markup)
    pass














# Обработчик для вывода сообщения с информацией о персонаже пользователя "📜 Мой персонаж"
@bot.callback_query_handler(func=lambda call: call.data.startswith('show_my_character'))
def show_character(call):
    character = characters_collection.find_one({"telegram_id": call.message.chat.id})
    if not character:
        bot.send_message(call.message.chat.id, "К сожалению, я не нашел информацию о вашем персонаже.")
        return
        
    name = character['name']
    level = character['level']
    current_exp = character['current_exp']
    lvlup_exp = character['lvlup_exp']
    money = character['money']
    
    
    country = character['country']
    if country == 'fire':
        country = 'Страна Огня 🔥'
    elif country == 'wind':
        country = 'Страна Ветра 💨'
    elif country == 'water':
        country = 'Страна Воды 💦'
    elif country == 'sound':
        country = 'Cтрана Звука 🔊'
    elif country == 'earth':
        country = 'Страна Земли 🌳'
    elif country == 'lightning':
        country = 'Страна Молний ⚡️'

    
    gender = character['gender']
    if gender == 'woman':
        gender = 'женский'
    elif gender == 'man':
        gender = 'мужской'
        
    
    element = character['element']
    if element == 'fire':
        element = '🔥 Огонь'
    elif element == 'water':
        element = '💧 Вода'
    elif element == 'wind':
        element = '💨 Ветер'
    elif element == 'earth':
        element = '🌳 Земля'
    elif element == 'lightning':
        element = '⚡️ Молния'


    shinobi_rank = character['shinobi_rank']
    if shinobi_rank == 'NoneYet':
        shinobi_rank = 'Без ранга'
    elif shinobi_rank == 'genin':
        shinobi_rank = 'Генин'
    elif shinobi_rank == 'chuunin':
        shinobi_rank = 'Чуунин'
    elif shinobi_rank == 'jounin':
        shinobi_rank = 'Джоунин'
    

    basic_jutsu = character['basic_jutsu']
    if basic_jutsu == 'ninjutsu':
        basic_jutsu = '🌀 Ниндзюцу'
    elif basic_jutsu == 'taijutsu':
        basic_jutsu = '💪 Тайджутсу'
    elif basic_jutsu == 'genjutsu':
        basic_jutsu = '👁️ Гендзюцу'


    current_location = character['current_location']

    
    biography = character['biography']
    if biography == 'NoneYet':
        biography = '[пока отсутсвует]'
    
    
    text = f"📜 Имя: {name}\n🌐 {country}\n👥 Пол: {gender}\n✨ Стихия: {element}\n🏅 Уровень: {level}\n🥷 Ранг шиноби: {shinobi_rank}\n💥 Опыт: {current_exp} из {lvlup_exp}\n\n"
    text += f"💰 Деньги: {money} рьё\n\n"
    text += f"🥋 Базовая техника: {basic_jutsu}\n\n"
    text += f"📍🌎 Текущая локация: {current_location}\n\n"
    text += f"📝 Биография:\n{biography}"
    
    # Создаем инлайн-кнопку 
    reply_markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text="👀 Характеристики персонажа", callback_data="profile_look_characteristics")
    button2 = types.InlineKeyboardButton(text="🎒 Инвентарь", callback_data="profile_look_inventory")
    reply_markup.add(button1)
    reply_markup.add(button2)
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup = reply_markup)


# Обработчик для кнопки "👀 Посмотреть характеристики персонажа"
@bot.callback_query_handler(func=lambda call: call.data.startswith('profile_look_characteristics'))
def profile_look_characteristics(call):
    character = characters_collection.find_one({"telegram_id": call.message.chat.id})
    if not character:
        bot.send_message(call.message.chat.id, "К сожалению, я не нашел информацию о вашем персонаже.")
        return
    
    text = f'''📜 Имя: {character["name"]}
    
📊 Характеристики персонажа:
    ⚔️ Атака: {character["characteristics"][0]["atack"]}
    🛡️ Защита: {character["characteristics"][0]["defense"]}
    ❤️ Здоровье: {character["characteristics"][0]["health"]}
    💫 Чакра: {character["characteristics"][0]["chakra"]}
    🏃 Скорость: {character["characteristics"][0]["speed"]}
    🤸 Ловкость: {character["characteristics"][0]["dexterity"]}
    ⚡️ Крит шанс: {character["characteristics"][0]["сritical_chance"]}
    🍀 Удача: {character["characteristics"][0]["luck"]}'''
    
    
    # Создаем инлайн-клавиатуру
    reply_markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text="🔙 Вернуться назад", callback_data="show_my_character")
    reply_markup.add(button1)
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup = reply_markup)


# Обработчик для вывода сообщения с информацией о профиле
@bot.message_handler(regexp='👤 Профиль')
def show_profile(message):
    user = users_collection.find_one({"telegram_id": message.from_user.id})
    character = characters_collection.find_one({"telegram_id": message.from_user.id})
    if not user:
        bot.send_message(message.chat.id, "К сожалению, я не нашел ваш профиль.")
        return
    registration_date = user['registration_date'].strftime('%d.%m.%Y')

    #first_fandom = user['first_fandom']
    first_name = user['first_name']
    profile_text = f"👤 {first_name}\n🆔 {message.from_user.id}\n\n📅 Дата регистрации: {registration_date}\n"
    
    reply_markup = types.InlineKeyboardMarkup()
    button_1 = types.InlineKeyboardButton(text="📜 Мой персонаж", callback_data="show_my_character")
    reply_markup.add(button_1)
    
    bot.send_message(message.chat.id, profile_text, reply_markup = reply_markup)














# Обработчик для кнопки "🎒 Инвентарь"
@bot.callback_query_handler(func=lambda call: call.data.startswith('profile_look_inventory'))
def profile_look_inventory(call):
    character = characters_collection.find_one({"telegram_id": call.message.chat.id})
    if not character:
        bot.send_message(call.message.chat.id, "К сожалению, я не нашел информацию о вашем персонаже.")
        return

    text_to_send = '🎒 Твой инвентарь\n\n'
    for item in character["inventory"][0].keys():
        count = character["inventory"][0][item][0]["count"]
        item_id = character["inventory"][0][item][0]["id"]
        text_to_send += f'▫️ {item}: {count} шт.\n/look_item_{item_id}\n'


    bot.send_message(call.message.chat.id, text_to_send)


# Обработчик для кнопки "/look_item_"
@bot.message_handler(regexp='/look_item_')
def look_item_callback(message):
    item_id = message.text.split("_")[2]
    character = characters_collection.find_one({"telegram_id": message.chat.id})
    if not character:
        bot.send_message(message.chat.id, "К сожалению, я не нашел информацию о вашем персонаже.")
        return
    item = None
    for category in character["inventory"]:
        for item_key, item_value in category.items():
            check_id = str(item_value[0].get('id'))
            if check_id == item_id:
                item = item_value
                item_name = item_key
                break
    if not item:
        bot.send_message(message.chat.id, "К сожалению, я не нашел информации об этом предмете.")
        return
    item_description = item[0]["description"]
    item_count = item[0]["count"]
    text_to_send = f"🔍 Информация о предмете:\n\n<b>Название:</b> {item_name}\n<b>Описание:</b> {item_description}\n<b>Количество:</b> {item_count} шт."
    bot.send_message(message.chat.id, text_to_send, parse_mode="HTML")












# Обработчик для вывода сообщения с информацией о квестах персонажа
@bot.message_handler(regexp='🗺️ Квесты')
def show_quests(message):
    user = users_collection.find_one({"telegram_id": message.from_user.id})
    character = characters_collection.find_one({"telegram_id": message.from_user.id})
    if not user:
        bot.send_message(message.chat.id, "К сожалению, я не нашел ваш профиль.")
        return
    if not character:
        bot.send_message(message.chat.id, "К сожалению, я не нашел вашего персонажа.")
        return

    # Создаем инлайн-кнопки
    reply_markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text="📅 Ежедневные задания", callback_data="quests_look_[DAILYTASK]")
    button2 = types.InlineKeyboardButton(text="📝 Мои активные задания", callback_data="quests_look_[ACTIVETASK]")
    reply_markup.add(button1)
    reply_markup.add(button2)

    bot.send_message(message.chat.id, "Выберите нужный вариант:", reply_markup=reply_markup)


# обработчик для кнопки quests_look_[ACTIVETASK]
@bot.callback_query_handler(func=lambda call: call.data == 'quests_look_[ACTIVETASK]')
def quests_look_ACTIVETASK(call):
    user = users_collection.find_one({"telegram_id": call.message.chat.id})
    character = characters_collection.find_one({"telegram_id": call.message.chat.id})
    quests_player_info = quests_collection.find_one({"telegram_id": call.message.chat.id})
    if not user:
        bot.send_message(call.message.chat.id, "К сожалению, я не нашел ваш профиль.")
        return

    active_quests = quests_player_info['list_of_active_quests']
    if not active_quests:
        bot.send_message(call.message.chat.id, "У вас нет активных квестов.")
        return

    message = "Активные квесты:\n"
    quest_message = ''
    for quest in active_quests:
        quest_data = quests.base_quests[quest['name']]
        quest_message += f"🎯 {quest_data['name']}\n"
        quest_message += f"📜 Описание: {quest_data['description']}\n\n"
        quest_message += "Условия выполнения:\n"
        for condition, value in quest_data['conditions_of_execution'].items():
            emoji = "✅" if value else "❌"
            quest_message += f"- {emoji} {condition}\n"
        quest_message += "\nНаграды:\n"
        quest_message += f"- Опыт: {quest_data['rewards']['exp']} XP\n"
        quest_message += f"- Деньги: {quest_data['rewards']['money']} 💰\n"
        quest_message += "\n"
        try:
            if quest_data['rewards']['items']:
                quest_message += "- Предметы:\n"
                for item, description in quest_data['rewards']['items'].items():
                    quest_message += f"\t- {item}: {description}\n"
        except:
            pass
        quest_message += "\n\n"
    bot.send_message(call.message.chat.id, f"{message}  {quest_message}") 













# Обработчик для вывода сообщения с информацией о текущем местоположении и помогает передвигаться по карте
@bot.message_handler(regexp='🚶‍♂️ Перемещение персонажа')
def show_current_character_location(message):
    user = users_collection.find_one({"telegram_id": message.from_user.id})
    character = characters_collection.find_one({"telegram_id": message.from_user.id})
    if not user:
        bot.send_message(message.chat.id, "К сожалению, я не нашел ваш профиль.")
        return
    
    current_character_location = character["current_location"]
    

    reply_markup = types.InlineKeyboardMarkup()
    text_to_send = f'🗺️ Игровая карта\n\n📍🌎 Текущая локация: {current_character_location}\n\n'
    if current_character_location in ['fire', 'water', 'wind', 'earth', 'lightning']:
        text_to_send += f'🧑‍ Ваш персонаж находится в 🌎 {locations_map.base_countrys.get(current_character_location)["name"]}'
    elif current_character_location in locations_map.base_villages:
        text_to_send += f'🧑‍ Ваш персонаж находится в 🌎 {locations_map.base_villages.get(current_character_location)["name"]}'
    
    location_in_village_list = ["academy", "main_square", "shopping_street", "small_training_ground", "market"]
    if any(location in current_character_location for location in location_in_village_list):
        if "academy" in current_character_location:
            text_to_send += f'🧑‍ Ваш персонаж находится в Академии\n\n'
            text_to_send += messages.PLAYER_IN_ACADEMY_MESSAGE

            button_1 = types.InlineKeyboardButton(text=f'🎓 Вступить в академию', callback_data=f'join_academy')
            reply_markup.add(button_1)
        if "market" in current_character_location:
            text_to_send += f'🧑‍ Ваш персонаж находится в локации Рынок \n\n'
            text_to_send += messages.PLAYER_IN_MARKET_MESSAGE
        
        
        

        
    
    
    button_1 = types.InlineKeyboardButton(text="🚶‍♂️ Переместиться", callback_data="move_character")
    reply_markup.add(button_1)
    
    
    bot.send_message(message.chat.id, text_to_send, reply_markup = reply_markup)


# обработчик для кнопки move_character
@bot.callback_query_handler(func=lambda call: call.data == 'move_character')
def move_character_callback(call):
    user = users_collection.find_one({"telegram_id": call.message.chat.id})
    character = characters_collection.find_one({"telegram_id": call.message.chat.id})
    if not user:
        bot.send_message(call.message.chat.id, "К сожалению, я не нашел ваш профиль.")
        return

    current_character_location = character["current_location"]
    reply_markup = types.InlineKeyboardMarkup()

    text_to_send = f'📍🌎 Текущая локация: {current_character_location}\n\n'

    if current_character_location in locations_map.base_countrys:
        this_country = current_character_location.replace('_country', '')
        this_country_village = f'{this_country}_village'
        button_1 = types.InlineKeyboardButton(text=f'🚶‍♂️ Переместиться в {locations_map.base_villages.get(this_country_village)["name"]}', callback_data=f'move_character_to_{this_country_village}')
        reply_markup.add(button_1)

        for location_key, location_value in locations_map.base_countrys.items():
            if location_key == current_character_location:
                for location in location_value["locations"]:
                    button_1 = types.InlineKeyboardButton(text=f'🚶‍♂️ Переместиться в {location_value["locations"].get(location)}', callback_data=f'move_character_to_{location}')
                    reply_markup.add(button_1)

        text_to_send += f'Ты можешь пойти в {locations_map.base_villages.get(this_country_village)["name"]} или в другую локацию этой страны'

    elif current_character_location in locations_map.base_villages:
        for location_key, location_value in locations_map.base_villages.items():
            if location_key == current_character_location:
                for location in location_value["locations"]:
                    button_1 = types.InlineKeyboardButton(text=f'🚶‍♂️ Переместиться в {location_value["locations"].get(location)}', callback_data=f'move_character_to_{location}')
                    reply_markup.add(button_1)
        button_2 = types.InlineKeyboardButton(text=f'🚶‍♂️ Выйти из деревни', callback_data=f'move_character_to_current_country')
        reply_markup.add(button_2)

        text_to_send += f'Ты можешь пойти в локацию внутри Деревни или выйти из деревни (окажешься в стране)'

    location_in_country_list = ["big_training_ground", "daimyo_residence"]
    if any(location in current_character_location for location in location_in_country_list):
        button_1 = types.InlineKeyboardButton(text=f'🚶‍♂️ Выйти из локации', callback_data=f'move_character_to_current_country')
        reply_markup.add(button_1)

        text_to_send += f'Ты можешь выйти из локации (окажешься в стране)'

    location_in_village_list = ["academy", "main_square", "shopping_street", "small_training_ground", "market"]
    if any(location in current_character_location for location in location_in_village_list):
        button_1 = types.InlineKeyboardButton(text=f'🚶‍♂️ Переместиться в деревню', callback_data=f'move_character_to_current_village')
        button_2 = types.InlineKeyboardButton(text=f'🚶‍♂️ Выйти из деревни', callback_data=f'move_character_to_current_country')
        reply_markup.add(button_1)
        reply_markup.add(button_2)

        text_to_send += f'Ты можешь выйти из локации Деревни или выйти из Деревни (окажешься в стране)'
    
    bot.send_message(call.message.chat.id, text_to_send, reply_markup = reply_markup)

# обработчик для кнопки move_character_to
@bot.callback_query_handler(func=lambda call: call.data.startswith('move_character_to'))
def move_character_callback(call):
    user = users_collection.find_one({"telegram_id": call.message.chat.id})
    character = characters_collection.find_one({"telegram_id": call.message.chat.id})
    if not user:
        bot.send_message(call.message.chat.id, "К сожалению, я не нашел ваш профиль.")
        return

    current_character_location = character["current_location"]
    location_to_move = call.data.replace('move_character_to_', '')
    
    
    # Формируем текст сообщения
    text_to_send = f'Вы успешно переместились!\n\n🗺️ Игровая карта\n\n📍🌎 Текущая локация: {location_to_move}'

    if location_to_move == 'current_village':
        location_to_move = current_character_location.split('_')[0]
        location_to_move = f"{location_to_move}_village"
        # Обновляем позицию (локацию) персонажа
        characters_collection.update_one({"telegram_id": call.message.chat.id}, {"$set": {"current_location": location_to_move}})
    elif location_to_move == 'current_country':
        location_to_move = current_character_location.split('_')[0]
        location_to_move = f"{location_to_move}_country"
        # Обновляем позицию (локацию) персонажа
        characters_collection.update_one({"telegram_id": call.message.chat.id}, {"$set": {"current_location": location_to_move}})
    else:
        # Обновляем позицию (локацию) персонажа
        characters_collection.update_one({"telegram_id": call.message.chat.id}, {"$set": {"current_location": location_to_move}})
        
    reply_markup = types.InlineKeyboardMarkup()
    
    location_in_village_list = ["academy", "main_square", "shopping_street", "small_training_ground", "market"]
    if any(location in location_to_move for location in location_in_village_list):
        button_1 = types.InlineKeyboardButton(text="👀 Осмотреться", callback_data="look_current_location")
        reply_markup.add(button_1)
    
    button_1 = types.InlineKeyboardButton(text="🚶‍♂️ Переместиться", callback_data="move_character")
    reply_markup.add(button_1)

    bot.send_message(call.message.chat.id, text_to_send, reply_markup = reply_markup)
    

# обработчик для кнопки look_current_location
@bot.callback_query_handler(func=lambda call: call.data.startswith('look_current_location'))
def look_current_location_callback(call):
    user = users_collection.find_one({"telegram_id": call.message.chat.id})
    character = characters_collection.find_one({"telegram_id": call.message.chat.id})
    if not user:
        bot.send_message(call.message.chat.id, "К сожалению, я не нашел ваш профиль.")
        return

    current_character_location = character["current_location"]    
    
    reply_markup = types.InlineKeyboardMarkup()


    text_to_send = f'🗺️ Игровая карта\n\n📍🌎 Текущая локация: {current_character_location}\n\n'
    if current_character_location in ['fire', 'water', 'wind', 'earth', 'lightning']:
        text_to_send += f'🧑‍ Ваш персонаж находится в 🌎 {locations_map.base_countrys.get(current_character_location)["name"]}'
    elif current_character_location in locations_map.base_villages:
        text_to_send += f'🧑‍ Ваш персонаж находится в 🌎 {locations_map.base_villages.get(current_character_location)["name"]}'
    
    location_in_village_list = ["academy", "main_square", "shopping_street", "small_training_ground", "market"]
    if any(location in current_character_location for location in location_in_village_list):
        if "academy" in current_character_location:
            text_to_send += f'🧑‍ Ваш персонаж находится в Академии\n\n'
            text_to_send += messages.PLAYER_IN_ACADEMY_MESSAGE

            button_1 = types.InlineKeyboardButton(text=f'🎓 Вступить в академию', callback_data=f'join_academy')
            reply_markup.add(button_1)
        if "market" in current_character_location:
            text_to_send += f'🧑‍ Ваш персонаж находится в локации Рынок \n\n'
            text_to_send += messages.PLAYER_IN_MARKET_MESSAGE
        if "small_training_ground" in current_character_location:
            text_to_send += f'🧑‍ Ваш персонаж находится в локации Малая тренировочная площадь\n\n'
            text_to_send += messages.PLAYER_IN_SMALL_TRANING_GROUND_MESSAGE

    button_1 = types.InlineKeyboardButton(text="🚶‍♂️ Переместиться", callback_data="move_character")
    reply_markup.add(button_1)
    
    
    bot.send_message(call.message.chat.id, text_to_send, reply_markup = reply_markup)










# Обработчик для вывода сообщения с информацией о добавленных локациях
@bot.callback_query_handler(func=lambda call: call.data == 'info_show_current_locations')
def show_current_locations(call):
    try:
        user = users_collection.find_one({"telegram_id": call.message.chat.id})
        character = characters_collection.find_one({"telegram_id": call.message.chat.id})
        if not user:
            bot.send_message(call.message.chat.id, "К сожалению, я не нашел ваш профиль.")
            return
        
        reply_markup = types.InlineKeyboardMarkup()
        button_1 = types.InlineKeyboardButton(text="Страны 🌍", callback_data="show_current_locations[countrys]")
        button_2 = types.InlineKeyboardButton(text="Скрытые деревни 🏞️", callback_data="show_current_locations[villages]")
        reply_markup.add(button_1)
        reply_markup.add(button_2)
        
        bot.delete_message(call.message.chat.id, call.message.message_id)    
        bot.send_message(call.message.chat.id, f'Выберите нужный вариант:', reply_markup = reply_markup)
    except telebot.apihelper.ApiException as e:
        # Обработка ошибки
        if "message to delete not found" in str(e):
            print("Сообщение уже удалено.")
        else:
            print("Произошла ошибка:", e)

# обработчик для кнопки show_current_locations
@bot.callback_query_handler(func=lambda call: call.data.startswith('show_current_locations'))
def show_current_locations_callback(call):
    try:
        if call.data.startswith('show_current_locations[countrys]'):
            if call.data == 'show_current_locations[countrys]':
                reply_markup = types.InlineKeyboardMarkup()
                
                for country in locations_map.base_countrys:
                    button_1 = types.InlineKeyboardButton(text=f'🌍 {locations_map.base_countrys.get(country)["name"]}', callback_data=f"show_current_locations[countrys]_{country}")
                    reply_markup.add(button_1)
                
                bot.delete_message(call.message.chat.id, call.message.message_id)  
                bot.send_message(call.message.chat.id, f'Выберите нужный вариант:', reply_markup = reply_markup)
                pass
            
            for country in locations_map.base_countrys:
                if call.data == f'show_current_locations[countrys]_{country}':
                    current_country = locations_map.base_countrys.get(country)
                    current_village = current_country["village"]
                    current_country_name = current_country["name"]
                    current_daimyo = current_country["daimyo"]

                    country_element = country.replace('_country', '')
                    
                    bot.delete_message(call.message.chat.id, call.message.message_id)  
                    bot.send_message(call.message.chat.id, f'🏰 {current_country_name}\n👤 Даймё: {current_daimyo} 🗡️\n\n🏛️ Локации:\n    🏟️ {current_country["locations"][f"{country_element}_big_training_ground"]}\n    🏯 {current_country["locations"][f"{country_element}_daimyo_residence"]}')

        elif call.data.startswith('show_current_locations[villages]'):
            if call.data == 'show_current_locations[villages]':
                reply_markup = types.InlineKeyboardMarkup()
                for village in locations_map.base_villages:
                    village_name = locations_map.base_villages.get(village)["name"]
                        
                    button_1 = types.InlineKeyboardButton(text=f"🏡 {village_name}", callback_data=f"show_current_locations[villages]_{village}")
                    reply_markup.add(button_1)

                bot.delete_message(call.message.chat.id, call.message.message_id)  
                bot.send_message(call.message.chat.id, f'Выберите нужный вариант:', reply_markup = reply_markup)
                pass
            
            
            for village in locations_map.base_villages:
                if call.data == f'show_current_locations[villages]_{village}':
                    this_country = village.replace('_village', '')
                    current_village = locations_map.base_villages.get(village)
                    
                    bot.delete_message(call.message.chat.id, call.message.message_id)  
                    bot.send_message(call.message.chat.id, f'🌳 {current_village["name"]}\n👤 Каге: {current_village["kage"]} 🗡️\n\n🏛️ Локации:\n    🏫 {current_village["locations"][f"{this_country}_academy"]}\n    🏢 {current_village["locations"][f"{this_country}_main_square"]}\n    🛍️ {current_village["locations"][f"{this_country}_shopping_street"]}\n    🥊 {current_village["locations"][f"{this_country}_small_training_ground"]}\n    🗳️ {current_village["locations"][f"{this_country}_market"]}')
    except telebot.apihelper.ApiException as e:
        # Обработка ошибки
        if "message to delete not found" in str(e):
            print("Сообщение уже удалено.")
        else:
            print("Произошла ошибка:", e)














# Обработчик для вывода сообщения с информацией о добавленных техниках
@bot.callback_query_handler(func=lambda call: call.data == 'info_show_current_techniques')
def show_current_technique(call):
    try:
        user = users_collection.find_one({"telegram_id": call.message.chat.id})
        character = characters_collection.find_one({"telegram_id": call.message.chat.id})
        if not user:
            bot.send_message(call.message.chat.id, "К сожалению, я не нашел ваш профиль.")
            return

        techniques = techniques_collection.find()
        for current_technique in techniques:
            # Фильтрация типа чакры
            if 'any' in current_technique['elements']:
                current_elements = 'Любой тип чакры'
            
            
            # Фильтрация типа дзюцу
            if 'nin' in current_technique['jutsu_type']:
                jutsu_type = 'ниндзюцу'
            elif 'gen' in current_technique['jutsu_type']:
                jutsu_type = 'гендзюцу'
            elif 'tai' in current_technique['jutsu_type']:
                jutsu_type = 'тайдзюцу'
            
            # Фильтрация типа техники    
            current_type_list = ''
            for current_type in current_technique['type']:
                if current_type in technique_type.technique_type_list:
                    current_type_list += f'↳ {technique_type.technique_type_list[current_type]}\n'
            
            
            text_to_send = f"📜 Название: {current_technique['name']}\n🏅 Ранг: {current_technique['rank']}\n\n📝 {current_technique['description']}\n\n🥋 Тип дзюцу: {jutsu_type}\n✨ Стихия: {current_elements}\n\n💥 Тип техники\n{current_type_list}"
            
            
            
            if 'gif' in current_technique:
                bot.send_document(call.message.chat.id, current_technique['gif'], caption=text_to_send)
            elif 'jpeg' in current_technique:
                bot.send_photo(call.message.chat.id, current_technique['jpeg'], caption = text_to_send)
    except telebot.apihelper.ApiException as e:
        # Обработка ошибки
        if "message to delete not found" in str(e):
            print("Сообщение уже удалено.")
        else:
            print("Произошла ошибка:", e)






# Обработчик для кнопки "📄 Справка"
@bot.message_handler(regexp='📄 Справка')
def show_current_technique(message):
    user = users_collection.find_one({"telegram_id": message.from_user.id})
    character = characters_collection.find_one({"telegram_id": message.from_user.id})
    if not user:
        bot.send_message(message.chat.id, "К сожалению, я не нашел ваш профиль.")
        return

    reply_markup = types.InlineKeyboardMarkup()       
    button_1 = types.InlineKeyboardButton(text=f'🎮 Текущие игровые техники', callback_data=f"info_show_current_techniques")
    button_2 = types.InlineKeyboardButton(text=f'🗺️ Текущие игровые локации', callback_data=f"info_show_current_locations")
    reply_markup.add(button_1)
    reply_markup.add(button_2)
            
    bot.send_message(message.chat.id, f'Выберите нужный вариант:', reply_markup = reply_markup)
    pass





# settings 
@bot.message_handler(commands=['settings'])
def settings_handler(message):
    # Здесь можно определить, что делать при получении команды /settings
    pass
    
    
# help 
@bot.message_handler(commands=['help'])
def help_handler(message):
    bot.send_message(message.chat.id, messages.HELP_MESSAGE)
    pass



######################## переназначение Exception #############################
def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    bot.send_message(config.OWNER_ID, 'LINE {} "{}")\n\nТип ошибки: {}\n\nОшибка: {}'.format(lineno, line.strip(), exc_type, exc_obj))


#запуск бота
bot.polling()