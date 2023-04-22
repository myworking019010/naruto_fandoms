from pymongo import MongoClient
import config
import bson

# Инициализируем клиент для работы с MongoDB
mongo_client = MongoClient(config.DB_URL)
db = mongo_client['narutofandom']
users_collection = db["users"]
characters_collection = db["characters"]
techniques_collection = db["techniques_list"]
quests_collection = db["quests"]
battle_collection = db["battle"]
mobs_collection = db["mobs"]





'''Метод для создания записи о бое и сохранения его в БД
В качестве аргумента принимает telegram_id пользователя,
который создал заявку на бой.

Возвращает battle_id'''

def create_battle_and_record_to_db(player_id):
    player_character = characters_collection.find_one({"telegram_id": player_id})
    try:
        player_last_battle_id = player_character["last_battle_id"]
    except:
        characters_collection.update_one({"telegram_id": player_id}, {"$set": {"last_battle_id": 'NoneYet'}})

    selected_characters = [
        {"team_name": f"Команда {player_character['name']}",
        "players": [{"player_id": player_id, "player_who_start_battle": "True"}]}
    ]

    # Сохраняем в БД запись о бое
    current_battle = {
        "list_of_opponents": selected_characters,
        "status": "waiting_for_opponents",
        "battle_field": [],
        "result": "NoneYet",
        "image": 'NoneYet'
        }
    current_battle = battle_collection.insert_one(current_battle)
    battle_id = current_battle.inserted_id

    characters_collection.update_one({"telegram_id": player_id}, {"$set": {"last_battle_id": battle_id}})

    return battle_id


'''Метод для добавления оппонента в созданный бой.
В качестве аргумента принимает telegram_id пользователя,
которого нужно добавить в бой и id бой.

Возвращает battle'''
def add_opponent_to_battle(opponent_id, battle_id):
    # Найдем битву в базе данных
    battle = battle_collection.find_one({"_id": bson.ObjectId(battle_id)})
    if not battle:
        # если битва не найдена, вернем None или бросим исключение
        return None
    
    # Создаем список соперников из битвы, если его еще нет
    if "list_of_opponents" not in battle:
        battle["list_of_opponents"] = []
    
    # Создаем нового игрока с заданным player_id
    new_opponent = {"player_id": int(opponent_id)}
    
    # Проверяем, что игрока еще нет в списке соперников
    for team in battle["list_of_opponents"]:
        for player in team["players"]:
            if player["player_id"] == opponent_id:
                # если игрок уже есть, то вернем битву без изменений
                return battle
    
    # Добавляем нового игрока в первую команду из списка
    for team in battle["list_of_opponents"]:
        if team["team_name"] == "Команда Соперников":
            team["players"].append(new_opponent)
            break
    else:
        # если команда не найдена, то создаем новую
        battle["list_of_opponents"].append({
            "team_name": "Команда Соперников",
            "players": [new_opponent]
        })
    
    # Сохраняем измененную битву в базе данных
    battle_collection.update_one(
        {"_id": bson.ObjectId(battle_id)},
        {"$set": {"list_of_opponents": battle["list_of_opponents"]}}
    )
    
    # возвращаем обновленную битву
    return battle




def delete_opponent_from_battle(opponent_id, battle_id):
    # Найдем битву в базе данных
    battle = battle_collection.find_one({"_id": bson.ObjectId(battle_id)})
    if not battle:
        # если битва не найдена, вернем None или бросим исключение
        return None
    
    # Проверяем, есть ли вообще список соперников в битве
    if "list_of_opponents" not in battle:
        return None
    
    # Удаляем игрока из списка соперников
    for team in battle["list_of_opponents"]:
        for player in team["players"]:
            if player["player_id"] == int(opponent_id):
                team["players"].remove(player)
                break
    
    # Сохраняем измененную битву в базе данных
    battle_collection.update_one(
        {"_id": bson.ObjectId(battle_id)},
        {"$set": {"list_of_opponents": battle["list_of_opponents"]}}
    )
    
    # возвращаем обновленную битву
    return battle
