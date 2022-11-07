import time

import requests
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import users
from create_bot import bot

main_kb = InlineKeyboardMarkup() \
    .add(InlineKeyboardButton(text="Рассчёт количества отзывов", callback_data="Рассчёт количества отзывов")) \
    .add(InlineKeyboardButton(text="Все данные по товару", callback_data="Все данные по товару")) \
    .add(InlineKeyboardButton(text="Все данные по продавцу", callback_data="Все данные по продавцу")) \
    .add(InlineKeyboardButton(text="Поиск товара по ключу", callback_data="Поиск товара по ключу")) \
    .add(InlineKeyboardButton(text="Ввести промокод", callback_data="Ввести промокод"))

admin_kb = InlineKeyboardMarkup() \
    .add(InlineKeyboardButton(text="Создать промокод", callback_data="Создать промокод")) \
    .add(InlineKeyboardButton(text="Меню пользователя", callback_data="Главное меню"))


class GetId(StatesGroup):
    id = State()


class GetIdForData(StatesGroup):
    id = State()


class GetBrandForData(StatesGroup):
    id = State()


class GetDataForPos(StatesGroup):
    id = State()
    query = State()
    pos = State()


class GetDataForPromo(StatesGroup):
    promo = State()


async def command_start(message: types.Message):
    await users.add_new_member(message.from_user.id)
    await bot.send_message(message.from_user.id,
                           text="Добро пожаловать в поисковую систему White Eye\n\nСервис является инструментом по поиску информации о товарах и продавцах на маркетплейсе Willdberies\n\nСервис работает в режиме реального времени, и он абсолютно бесплатный.",
                           reply_markup=main_kb)


async def new_command_start(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback_query.message.edit_text(text="Главное меню", reply_markup=main_kb)


def get_info(id):
    r = requests.get(f'''https://wbx-content-v2.wbstatic.net/ru/{id}.json''')
    request_result = r.json()
    return request_result['imt_name'], request_result['selling']['brand_name'], request_result['imt_id']


def get_stats(id, imt_id):
    options = Options()
    options.add_argument('headless')
    options.add_argument('window-size=1920x935')

    global driver
    driver = webdriver.Chrome(options=options, executable_path="chromedriver.exe")

    driver.get(f"https://www.wildberries.ru/catalog/{id}/feedbacks?imtId={imt_id}")
    time.sleep(5)
    big_stat = driver.find_element(by=By.CLASS_NAME, value="rating-product__numb")
    if float(big_stat.text) >= 4.46:
        return [1000, 0, 0, 0, 0]

    elif float(big_stat.text) < 4.45:
        while True:
            stats = driver.find_elements(by=By.CLASS_NAME, value="rating-product__review")
            a = []
            i = 1
            while True:
                try:
                    stat = stats[i].text
                    stat = stat.replace("отзыва", "")
                    stat = stat.replace("отзывов", "")
                    stat = stat.replace("отзыв", "")
                    stat = stat.replace(" ", '')
                    a.append(stat)
                    i += 1
                except:
                    break
            driver.quit()
            return a


async def start_search(callback_query: types.callback_query):
    await callback_query.message.edit_text(text="Введите ID товара для расчета необходимого количества отзывов", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(text="Отмена", callback_data="Главное меню")))
    await GetId.id.set()


async def end_search(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["id"] = message.text
    await bot.send_message(message.from_user.id, text="Ожидайте результат операции...")

    item_name, item_brand_name, imt_item_id = get_info(data["id"])

    try:
        feedback = get_stats(data["id"], imt_item_id)
    except:
        await bot.send_message(message.from_user.id, text=f"Произошла ошибка при получении данных со страницы товара, повторите попытку", reply_markup=main_kb)
        await state.finish()
        driver.quit()
        return 0

    if feedback == []:
        await bot.send_message(message.from_user.id, text=f"Произошла ошибка при получении данных со страницы товара, повторите попытку", reply_markup=main_kb)
        await state.finish()
        driver.quit()
        return 0

    score = 5
    middle_value = 0
    all_feedbacks = 0
    len_feedbacks = len(feedback)
    for i in range(len_feedbacks):
        middle_value += int(feedback[i]) * score
        all_feedbacks += int(feedback[i])
        score -= 1
    new_middle_value = middle_value
    new_middle_value /= all_feedbacks  # Среднее дначение

    try:
        r = requests.get(f"https://card.wb.ru/cards/detail?spp=0&regions=68,64,83,4,38,80,33,70,82,86,75,30,69,22,66,31,48,1,40,71&pricemarginCoeff=1.0&reg=0&appType=1&emp=0&locale=ru&lang=ru&curr=rub&couponsGeo=12,3,18,15,21&dest=-1029256,-102269,-1278703,-1255563&nm={data['id']}")
        request = r.json()
    except:
        await bot.send_message(message.from_user.id, text=f"Не удалось получить информация по товару попробуйте еще раз", reply_markup=main_kb)
        await state.finish()
        return 0

    price = (request['data']['products'][0]['priceU']) / 100
    counter = 0

    if new_middle_value < 4.45:
        stop = ''
        while stop != "stop":
            while True:
                middle_value += 5
                all_feedbacks += 1
                counter += 1
                if (middle_value / all_feedbacks) > 4.45:
                    stop = "stop"
                    break
        await bot.send_message(message.from_user.id, text=f"Товар: {item_name}\nИмя бренда: {item_brand_name}\nАртикул: {data['id']}\nЦена: {int(price)}₽\n\nТекущий рейтинг: {round(new_middle_value, 1)}\nДля достижения нужного рейтинга необходимо {counter} отзывов", reply_markup=main_kb)
        await state.finish()
    else:
        await bot.send_message(message.from_user.id, text=f"Товар: {item_name}\nИмя бренда: {item_brand_name}\nАртикул: {data['id']}\nЦена: {int(price)}₽\n\nТекущий рейтинг: {round(new_middle_value, 1)}", reply_markup=main_kb)
        await state.finish()


async def get_info_by_id_1(callback_query: types.callback_query):
    await callback_query.message.edit_text(text="Введите ID товара для получения всей доступной информации", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(text="Отмена", callback_data="Главное меню")))
    await GetIdForData.id.set()


async def get_info_by_id_2(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["id"] = message.text
        response = requests.get(f'https://wbx-content-v2.wbstatic.net/ru/{data["id"]}.json')
        price_response = requests.get(f'https://card.wb.ru/cards/detail?spp=0&regions=68,64,83,4,38,80,33,70,82,86,30,69,22,66,31,40,1,48&pricemarginCoeff=1.0&reg=0&appType=1&emp=0&locale=ru&lang=ru&curr=rub&couponsGeo=12,7,3,6,5,18,21&dest=-1216601,-337422,-1114902,-1198055&nm={data["id"]}')
    data = response.json()
    price = int((price_response.json()['data']['products'][0]['salePriceU']) / 100)

    options = "*Дополнительная информация:*\n"
    for i in range(len(data['options'])):
        options += f'''\t\t{i + 1}. {data['options'][i]['name']} {data['options'][i]['value']}\n'''

    text = f'''*Наименование:* {data['imt_name']}\n\n*Цена:* {price} руб.\n\n*Категория:* {data['subj_root_name']}\n\n*Описание:* {data['description']}\n\n{options}'''

    await bot.send_message(message.from_user.id, text=text, reply_markup=main_kb, parse_mode="Markdown")
    await state.finish()


async def get_info_by_brand_1(callback_query: types.callback_query):
    await callback_query.message.edit_text(text="Введите ID товара продавца для получения всей доступной информации", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(text="Отмена", callback_data="Главное меню")))
    await GetBrandForData.id.set()


async def get_info_by_brand_2(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["id"] = message.text
        response = requests.get(f'https://wbx-content-v2.wbstatic.net/sellers/{data["id"]}.json')

        data = response.json()

    cookies = {
        'fbb_s': '1',
        'fbb_u': '1661478962',
        '_ym_uid': '1661478961876076595',
        '_ym_d': '1661478961',
        '_ym_visorc': 'b',
        '_ym_isad': '2',
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'X-KL-Ajax-Request': 'Ajax_Request',
        'Connection': 'keep-alive',
        'Referer': 'https://www.rusprofile.ru/',
        # Requests sorts cookies= alphabetically
        # 'Cookie': 'fbb_s=1; fbb_u=1661478962; _ym_uid=1661478961876076595; _ym_d=1661478961; _ym_visorc=b; _ym_isad=2',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        # Requests doesn't support trailers
        # 'TE': 'trailers',
    }
    params = {
        'query': f'''{data['inn']}''',
        'action': 'search',
        'cacheKey': '0.9686766658449064',
    }
    response = requests.get('https://www.rusprofile.ru/ajax.php', params=params, cookies=cookies, headers=headers)
    print(response.json())
    try:
        raw_name = response.json()['ul'][0]['raw_name']
        raw_ogrn = response.json()['ul'][0]['raw_ogrn']
        address = response.json()['ul'][0]['address']
        ceo_type = response.json()['ul'][0]['ceo_type']
        ceo_name = response.json()['ul'][0]['ceo_name']
        okved_descr = response.json()['ul'][0]['okved_descr']
        authorized_capital = response.json()['ul'][0]['authorized_capital']
        reg_date = response.json()['ul'][0]['reg_date']

        text = f'''Наименование: {data['supplierName']}\nИНН: {data['inn']}\nМарка: {data['trademark']}'''
        add_text = f'''\n\nНазвание организации: {raw_name}\nОГРН: {raw_ogrn}\nАдрес: {address}\n{ceo_type}: {ceo_name}\nОписание: {okved_descr}\nКапитал: {authorized_capital}\nДата регистрации: {reg_date}'''
        text += add_text

    except:
        raw_name = response.json()['ip'][0]['raw_name']
        raw_ogrnip = response.json()['ip'][0]['raw_ogrnip']
        address = response.json()['ip'][0]['region_name']
        okved_descr = response.json()['ip'][0]['okved_descr']
        reg_date = response.json()['ip'][0]['reg_date']

        text = f'''Наименование: {data['supplierName']}\nИНН: {data['inn']}\nМарка: {data['trademark']}'''
        add_text = f'''\n\nНазвание организации: {raw_name}\nОГРНИП: {raw_ogrnip}\nРегион: {address}\nОписание: {okved_descr}\nДата регистрации: {reg_date}'''
        text += add_text
    
    await bot.send_message(message.from_user.id, text=text, reply_markup=main_kb, parse_mode="Markdown")

    # try:
    #     if (int(time.time()) - int(await users.check_time(message.from_user.id))) < 60:
    #         await bot.send_message(message.from_user.id, text=text, reply_markup=main_kb, parse_mode="Markdown")
    #     else:
    #         text = f'''Наименование: {data['supplierName']}\nИНН: {data['inn']}\nМарка: {data['trademark']}'''
    #         await bot.send_message(message.from_user.id, text=text, reply_markup=main_kb, parse_mode="Markdown")
    # except:
    #     text = f'''Наименование: {data['supplierName']}\nИНН: {data['inn']}\nМарка: {data['trademark']}'''
    #     await bot.send_message(message.from_user.id, text=text, reply_markup=main_kb, parse_mode="Markdown")

    await state.finish()


async def get_pos_by_id_1(callback_query: types.callback_query):
    await callback_query.message.edit_text(text="Введите ID товара для получения № в топе по ключевому запросу", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(text="Отмена", callback_data="Главное меню")))
    await GetDataForPos.id.set()


async def get_pos_by_id_2(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["id"] = message.text
    await bot.send_message(message.from_user.id, text="Введите ключевой запрос", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(text="Отмена", callback_data="Главное меню")))
    await GetDataForPos.query.set()


async def get_pos_by_id_3(message: types.Message, state: FSMContext):
    await bot.send_message(message.from_user.id, text="Ожидайте завершение операции...")

    async with state.proxy() as data:
        data["query"] = message.text
        item_id = data["id"]
        query = data["query"]
        try:
            page = 1
            while True:
                url = f"https://search.wb.ru/exactmatch/ru/common/v4/search?appType=1&couponsGeo=12,7,3,6,5,18,21&curr=rub&dest=-1216601,-337422,-1114902,-1198055&emp=0&lang=ru&locale=ru&page={page}&pricemarginCoeff=1.0&query={query}&reg=0&regions=68,64,83,4,38,80,33,70,82,86,30,69,22,66,31,40,1,48&resultset=catalog&sort=popular&spp=0&suppressSpellcheck=false"
                response = requests.get(url=url)
                ids = response.json()
                ids = ids['data']['products']
                for i in range(len(ids)):
                    if item_id == str(ids[i]['id']):
                        data['pos'] = i + 1 + (page - 1) * 100
                        break
                page += 1

        except:
            try:
                if data['pos'] > 0:
                    await bot.send_message(message.from_user.id, f"Товар {data['id']} занимает *{data['pos']}* место по ключевому запросу {data['query']}", reply_markup=main_kb, parse_mode="Markdown")
            except:
                await bot.send_message(message.from_user.id, f"Товар {data['id']} не найден по ключевому запросу {data['query']}", reply_markup=main_kb)

        finally:
            await state.finish()


async def promo_1(callback_query: types.callback_query):
    await callback_query.message.edit_text(text="Введите промокод", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(text="Отмена", callback_data="Главное меню")))
    await GetDataForPromo.promo.set()


async def promo_2(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["promo"] = message.text
    if int(await users.use_promo(message.from_user.id, data["promo"])) == 0:
        await bot.send_message(message.from_user.id, text="Промокода не существует", reply_markup=main_kb)
    else:
        await bot.send_message(message.from_user.id, text="Промокод применен", reply_markup=main_kb)

    await state.finish()


async def admin_start(message: types.Message):
    if message.from_user.id == 1:
        await bot.send_message(message.from_user.id,
                               text="Добро пожаловать в панель администратора.",
                               reply_markup=admin_kb)
    else:
        pass


async def add_promo(callback_query: types.callback_query):
    import random

    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
    password = ''
    for i in range(8):
        password += random.choice(chars)
    await users.add_new_promo(password)

    await callback_query.message.edit_text(text=f"Промокод {password} создан", reply_markup=admin_kb)


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(command_start, commands=['start'])
    dp.register_message_handler(admin_start, commands=['admin'])

    dp.register_callback_query_handler(new_command_start, lambda c: c.data == "Главное меню", state="*")

    dp.register_callback_query_handler(start_search, lambda c: c.data == "Рассчёт количества отзывов")
    dp.register_message_handler(end_search, state=GetId.id)

    dp.register_callback_query_handler(get_info_by_id_1, lambda c: c.data == "Все данные по товару")
    dp.register_message_handler(get_info_by_id_2, state=GetIdForData.id)

    dp.register_callback_query_handler(get_info_by_brand_1, lambda c: c.data == "Все данные по продавцу")
    dp.register_message_handler(get_info_by_brand_2, state=GetBrandForData.id)

    dp.register_callback_query_handler(get_pos_by_id_1, lambda c: c.data == "Поиск товара по ключу")
    dp.register_message_handler(get_pos_by_id_2, state=GetDataForPos.id)
    dp.register_message_handler(get_pos_by_id_3, state=GetDataForPos.query)

    dp.register_callback_query_handler(promo_1, lambda c: c.data == "Ввести промокод")
    dp.register_message_handler(promo_2, state=GetDataForPromo.promo)

    dp.register_callback_query_handler(add_promo, lambda c: c.data == "Создать промокод")
