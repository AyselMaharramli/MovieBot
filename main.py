from typing import Dict, Any, Union, Optional
from movie_object import MovieResult
from telebot import types
from api import api_query
from html import escape
from const import BOT

USER_DATA: Dict[str, Dict[str, Any]] = dict()


def set_user_data(user_id: Union[int, str], data: str, value: Any):
    user_id = str(user_id)
    if user_id in USER_DATA:
        USER_DATA[user_id][data] = value
    else:
        USER_DATA[user_id] = {data: value}


def get_user_data(user_id: Union[int, str], data: str) -> Optional[Any]:
    user_id = str(user_id)
    if user_id in USER_DATA:
        return USER_DATA[user_id][data]
    else:
        return


def remove_markup(user_id: int):
    markup = types.ReplyKeyboardMarkup()
    markup.add(types.KeyboardButton(text='❌'))
    new_message = BOT.send_message(chat_id=user_id, text='❌', reply_markup=markup)
    BOT.delete_message(chat_id=user_id, message_id=new_message.message_id)


@BOT.message_handler(commands=['start'])
def start(message: Union[types.Message, types.CallbackQuery]):
    USER_DATA.pop(str(message.from_user.id), None)
    markup: types.InlineKeyboardMarkup = types.InlineKeyboardMarkup()
    for name in {'a movie', 'a series', 'an episode'}:
        markup.add(types.InlineKeyboardButton(text=f'Search for {name}',
                                              callback_data=f'search#{name.split(" ")[1]}'))
    BOT.send_message(chat_id=message.from_user.id, text='Welcome, start searching for movies', reply_markup=markup)


@BOT.message_handler(func=lambda m: m.text.startswith('⬅️'), content_types=['text'])
@BOT.callback_query_handler(func=lambda c: c.data == 'back')
def _(message: Union[types.Message, types.CallbackQuery]):
    menu: str = get_user_data(user_id=message.from_user.id, data='menu')
    if menu == 'search':
        set_user_data(user_id=message.from_user.id, data='menu', value=None)
        remove_markup(message.from_user.id)
        start(message)
    elif menu == 'search_results':
        set_user_data(user_id=message.from_user.id, data='menu', value='search')
        remove_markup(message.from_user.id)
        movie_type = get_user_data(user_id=message.from_user.id, data='search_type')
        message.data = f'search#{movie_type}'
        search(message)
    elif menu == 'single_result':
        set_user_data(user_id=message.from_user.id, data='menu', value='search_results')
        BOT.delete_message(chat_id=message.from_user.id, message_id=message.message.message_id)
        message.message.from_user = message.from_user
        message.message.text = get_user_data(user_id=message.from_user.id, data='search_value')
        search_results(message.message)

    if isinstance(message, types.CallbackQuery):
        try:
            BOT.delete_message(chat_id=message.from_user.id, message_id=message.message.message_id)
        except Exception:
            pass


@BOT.callback_query_handler(func=lambda call: call.data.startswith('search#'))
def search(call: types.CallbackQuery):
    try:
        BOT.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
    except:
        pass

    call_data: str = call.data.split('#')[1]

    set_user_data(user_id=call.from_user.id, data='search_type', value=call_data)
    set_user_data(user_id=call.from_user.id, data='menu', value='search')

    markup: types.ReplyKeyboardMarkup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(text='⬅️Back'))
    BOT.send_message(chat_id=call.from_user.id, text=f'Enter the {call_data} name', reply_markup=markup)


@BOT.message_handler(func=lambda m: get_user_data(user_id=m.from_user.id, data='menu') == 'search',
                     content_types=['text'])
@BOT.callback_query_handler(func=lambda call: call.data.startswith('search_for#'))
def search_results(message: Union[types.Message, types.CallbackQuery]):
    try:
        if isinstance(message, types.Message):
            r = api_query(name=message.text, result_type=get_user_data(user_id=message.from_user.id,
                                                                       data='search_type'))
            set_user_data(user_id=message.from_user.id, data='search_value', value=message.text)
        else:
            page: int = int(message.data.split('#')[1])
            # Callback query
            r = api_query(name=get_user_data(user_id=message.from_user.id, data='search_value'),
                          result_type=get_user_data(user_id=message.from_user.id, data='search_type'),
                          page=page)

        set_user_data(user_id=message.from_user.id, data='results', value=r)
        set_user_data(user_id=message.from_user.id, data='menu', value='search_results')
        markup: types.InlineKeyboardMarkup = types.InlineKeyboardMarkup()
        for item in r.movies:
            markup.add(types.InlineKeyboardButton(text=item.title, callback_data=f'movie#{item.imdb_id}'))
        if isinstance(message, types.CallbackQuery):
            page: int = int(message.data.split('#')[1])
        else:
            page: int = 1

        number_of_results: int = r.total
        back_b = types.InlineKeyboardButton(text='⬅️Prev', callback_data=f'search_for#{page - 1}')
        next_b = types.InlineKeyboardButton(text='➡️Next', callback_data=f'search_for#{page + 1}')

        if page > 1 and page * 10 < number_of_results:
            markup.row(back_b, next_b)
        elif page > 1:
            markup.add(back_b)
        else:
            markup.add(next_b)

        markup.add(types.InlineKeyboardButton(text='⬅️Back', callback_data='back'))
        if isinstance(message, types.CallbackQuery):
            BOT.edit_message_text(text=f'Pick a movie from the list', chat_id=message.from_user.id,
                                  message_id=message.message.message_id, reply_markup=markup)
        else:
            remove_markup(message.from_user.id)
            BOT.send_message(chat_id=message.from_user.id, text=f'Pick a movie from the list', reply_markup=markup)
    except RuntimeError as e:
        if isinstance(message, types.CallbackQuery):
            BOT.edit_message_text(text=f'Error: {e}', chat_id=message.from_user.id,
                                  message_id=message.message.message_id)
        else:
            BOT.send_message(chat_id=message.from_user.id, text=f'Error: {e}. Do /start')


@BOT.callback_query_handler(func=lambda call: call.data.startswith('movie#'))
def _(call: types.CallbackQuery):
    set_user_data(user_id=call.from_user.id, data='menu', value='single_result')
    movie_id: str = call.data.split('#')[1]
    movie_data: MovieResult = get_user_data(user_id=call.from_user.id, data='results')
    for item in movie_data.movies:
        if item.imdb_id == movie_id:
            text: str = f'<a href="{item.poster_url}">\u2060</a>Title: <b>{escape(item.title)}</b>\n' \
                        f'Release year: {item.year}\nIMDB ID: <code>{escape(item.imdb_id)}</code>'
            markup: types.InlineKeyboardMarkup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(text='⬅️Back', callback_data='back'))
            BOT.edit_message_text(chat_id=call.from_user.id, text=text, reply_markup=markup, parse_mode='HTML',
                                  message_id=call.message.message_id)
            break


if __name__ == '__main__':
    BOT.polling()
