# region Imports
import asyncio
from aiogram import Bot, Dispatcher, filters, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from dotenv import load_dotenv
import os
from db import engine, Users, Products, Categories, Reviews, OrderItems, Orders, CartItems, Carts
from sqlalchemy.orm import sessionmaker
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from usermanager import *
from datetime import date
# endregion

# region Initializations
load_dotenv()
my_token = os.getenv('TOKEN')

dp = Dispatcher()

Session = sessionmaker(engine)
session = Session()

class Register(StatesGroup):
    waiting_for_name = State()
    waiting_for_surname = State()
    waiting_for_age = State()

class EditProfile(StatesGroup):
    waiting_for_new_name = State()
    waiting_for_new_surname = State()
    waiting_for_new_age = State()


# endregion

# region User Features
@dp.message(filters.Command('start'))
async def start(message: Message, state: FSMContext):
    await clean_bot_messages(message=message, state=state)
    
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Menu ⚙️'), KeyboardButton(text='Language 🌍')]
        ], resize_keyboard=True
    )
    
    await message.answer('Welcome to shop bot where you can buy staff', reply_markup=markup)

@dp.message(F.text == 'Cancel the process ❌')
async def cancel_process(message: Message, state: FSMContext):
    await clean_bot_messages(message=message, state=state)
    await state.clear()
    markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text='Menu ⚙️'), KeyboardButton(text='Language 🌍')]
            ], resize_keyboard=True
        )
    await message.answer('Process was caceled ✅', reply_markup=markup)

@dp.message(F.text == 'Menu ⚙️')
async def menu(message: Message, state: FSMContext):
    await clean_bot_messages(message=message, state=state)

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text = 'Register ✍️', callback_data='REGISTER')],
            [InlineKeyboardButton(text = 'Profile 👤', callback_data='PROFILE')],
            [InlineKeyboardButton(text = 'Edit Profile 📝', callback_data='EDIT_PROFILE')],
            [InlineKeyboardButton(text = 'View Products 👕', callback_data='VIEW_PRODUCT')],
            [InlineKeyboardButton(text = 'Order History 📖', callback_data='ORDER_HISTORY')],
            [InlineKeyboardButton(text = 'My Cart 🛒', callback_data='MY_CART')]
        ]
    )
    msg = await message.answer('Menu ⚙️', reply_markup=markup)
    await state.update_data(menu_msg_id = msg.message_id)

@dp.callback_query(F.data == 'REGISTER')
async def register(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state = state)
    
    user = session.query(Users).filter_by(tg_id = call.from_user.id).first()
    if user != None:
        call.message.answer('You are already registered ✅')
        return
    
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text = 'Cancel the process ❌')]
        ], resize_keyboard=True
    )
    await call.message.answer(text = 'Enter your name !', reply_markup=markup)
    await state.set_state(Register.waiting_for_name)

@dp.message(Register.waiting_for_name)
async def get_user_name(message: Message, state: FSMContext):
    await clean_bot_messages(message=message, state=state)

    if await name_validation(message.text):
        await state.update_data(name = message.text)
        await state.set_state(Register.waiting_for_surname)
        await message.answer('Enter your surname !')
    
    else:
        await message.answer('Please enter your name correctly !')

@dp.message(Register.waiting_for_surname)
async def get_user_surname(message: Message, state: FSMContext):
    await clean_bot_messages(message=message, state=state)

    if await surname_validation(message.text):
        await state.update_data(surname = message.text)
        await state.set_state(Register.waiting_for_age)
        await message.answer('Enter your age !')
    
    else:
        await message.answer('Please enter your surname correctly !')

@dp.message(Register.waiting_for_age)
async def get_user_age(message: Message, state: FSMContext):
    await clean_bot_messages(message=message, state=state)

    if await age_validation(message.text):
        age = int(message.text)
        data = await state.get_data()
        user = Users(
            tg_id = message.from_user.id,
            username = message.from_user.username,
            full_name = message.from_user.full_name,
            name = data['name'],
            surname = data['surname'],
            age = age
        )

        session.add(user)
        session.commit()
        markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text='Menu ⚙️'), KeyboardButton(text='Language 🌍')]
            ], resize_keyboard=True
        )
        await message.answer('You registered successfully ✅', reply_markup=markup)

    else:
        await message.answer('Please enter your age correctly !')

@dp.callback_query(F.data == 'PROFILE')
async def show_profile(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)
    
    user = session.query(Users).filter_by(tg_id = call.from_user.id).first()
    if user == None:
        await call.message.answer('Please register before being able to see your profile 🙂')
        return

    msg = await call.message.answer(
f'''
🆔: {user.tg_id}

👤Name: {user.name}

🎓Surname {user.surname}

📅Age {user.age}

💳Balance: {user.balance}

📅Registered: {user.created_at.date()}

'''
)   
    await state.update_data(profile_msg_id = msg.message_id)

@dp.callback_query(F.data == 'EDIT_PROFILE')
async def edit_profile(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    user = session.query(Users).filter_by(tg_id = call.from_user.id).first()
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f'👤Name: {user.name}', callback_data='EDIT_NAME')],
            [InlineKeyboardButton(text=f'🎓Surname {user.surname}', callback_data='EDIT_SURNAME')],
            [InlineKeyboardButton(text=f'📅Age {user.age}', callback_data='EDIT_AGE')]
        ]
    )

    msg = await call.message.answer('Edit Profile ✍️', reply_markup=markup)
    await state.update_data(editprofile_msg_id = msg.message_id)

@dp.callback_query(F.data == 'EDIT_NAME')
async def edit_name(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    await state.set_state(EditProfile.waiting_for_new_name)
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text = 'Cancel the process ❌')]
        ], resize_keyboard=True
    )
    await call.message.answer(text = 'Please enter your new name !', reply_markup=markup)

@dp.callback_query(F.data == 'EDIT_SURNAME')
async def edit_surname(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    await state.set_state(EditProfile.waiting_for_new_surname)
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text = 'Cancel the process ❌')]
        ], resize_keyboard=True
    )
    await call.message.answer(text = 'Please enter your new surname !', reply_markup=markup)

@dp.callback_query(F.data == 'EDIT_AGE')
async def edit_age(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    await state.set_state(EditProfile.waiting_for_new_age)
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text = 'Cancel the process ❌')]
        ], resize_keyboard=True
    )
    await call.message.answer(text = 'Please enter your new age !', reply_markup=markup)

@dp.message(EditProfile.waiting_for_new_name)
async def change_name(message: Message, state: FSMContext):
    await clean_bot_messages(message=message, state=state)

    if await name_validation(message.text):
        user = session.query(Users).filter_by(tg_id = message.from_user.id).first()
        user.name = message.text
        markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text='Menu ⚙️'), KeyboardButton(text='Language 🌍')]
            ], resize_keyboard=True
        )
        await message.answer(text = 'Your name was successfully edited ✅', reply_markup=markup)
        session.add(user)
        session.commit()
    
    else:
        await message.answer('Please enter your new name correctly !')

@dp.message(EditProfile.waiting_for_new_surname)
async def change_surname(message: Message, state: FSMContext):
    await clean_bot_messages(message=message, state=state)

    if await surname_validation(message.text):
        user = session.query(Users).filter_by(tg_id = message.from_user.id).first()
        user.surname = message.text
        markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text='Menu ⚙️'), KeyboardButton(text='Language 🌍')]
            ], resize_keyboard=True
        )
        await message.answer(text = 'Your surname was successfully edited ✅', reply_markup=markup)
        session.add(user)
        session.commit()
    
    else:
        await message.answer('Please enter your new surname correctly !')

@dp.message(EditProfile.waiting_for_new_age)
async def change_age(message: Message, state: FSMContext):
    await clean_bot_messages(message=message, state=state)

    if await age_validation(message.text):
        user = session.query(Users).filter_by(tg_id = message.from_user.id).first()
        user.age = int(message.text)
        markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text='Menu ⚙️'), KeyboardButton(text='Language 🌍')]
            ], resize_keyboard=True
        )
        await message.answer(text = 'Your age was successfully edited ✅', reply_markup=markup)
        session.add(user)
        session.commit()
    
    else:
        await message.answer('Please enter your new age correctly !')

@dp.callback_query(F.data == 'VIEW_PRODUCT')
async def show_categories(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    categories = session.query(Categories).order_by(Categories.title).limit(5).all()
    await state.update_data(page = 0)
    keyboard = [
        [InlineKeyboardButton(
            text=f'{category.title}',
            callback_data=f'CATEGORY_{category.id}'
        )]
        for category in categories
    ]

    '''
    keyboard.append(
        [InlineKeyboardButton(text='⬅️ Back', callback_data='BACK')]
    )
    '''

    keyboard.append(
        [InlineKeyboardButton(text='Next ➡️', callback_data='NEXT')]
    )

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    msg = await call.message.answer(
        text='Choose a category 🌃',
        reply_markup=markup
    )

    await state.update_data(view_categories = msg.message_id)

@dp.callback_query(F.data == 'NEXT')
async def next_category_page(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state = state)

    data = await state.get_data()
    page = data['page'] + 1
    await state.update_data(page = page)
    categories = session.query(Categories).order_by(Categories.title).offset(page * 5).limit(5).all()
    keyboard = [
        [InlineKeyboardButton(
            text=f'{category.title}',
            callback_data=f'CATEGORY_{category.id}'
        )]
        for category in categories
    ]

    keyboard.append(
        [InlineKeyboardButton(text='Back ⬅️', callback_data='BACK')]
    )

    keyboard.append(
        [InlineKeyboardButton(text='Next ➡️', callback_data='NEXT')]
    )

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    msg = await call.message.answer(
        text='Choose a category 🌃',
        reply_markup=markup
    )

    await state.update_data(view_categories = msg.message_id)

@dp.callback_query(F.data == 'BACK')
async def next_category_page(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state = state)

    data = await state.get_data()
    page = data['page'] - 1
    await state.update_data(page = page)
    categories = session.query(Categories).order_by(Categories.title).offset(page * 5).limit(5).all()
    keyboard = [
        [InlineKeyboardButton(
            text=f'{category.title}',
            callback_data=f'CATEGORY_{category.id}'
        )]
        for category in categories
    ]

    if page > 0:
        keyboard.append(
            [InlineKeyboardButton(text='Back ⬅️', callback_data='BACK')]
        )

    keyboard.append(
        [InlineKeyboardButton(text='Next ➡️', callback_data='NEXT')]
    )

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    msg = await call.message.answer(
        text='Choose a category 🌃',
        reply_markup=markup
    )

    await state.update_data(view_categories = msg.message_id)

async def clean_bot_messages(message: Message, state: FSMContext):
    data = await state.get_data()
    keys = ['menu_msg_id', 'profile_msg_id', 'editprofile_msg_id', 'view_categories']
    for key in keys:
        msg_id = data.get(key)
        if not msg_id:
            continue
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        except Exception as e:
            print(f"delete failed for {key}={msg_id}: {e}")
        await state.update_data(**{key: None})

# endregion






# region Main
async def main():
    bot = Bot(token=my_token)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

# endregion
