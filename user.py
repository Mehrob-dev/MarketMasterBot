# region Imports
from aiogram import Router, F
from aiogram import filters
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
    ReplyKeyboardMarkup
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import engine, Users, Products, Categories, Reviews, OrderItems, Orders, CartItems, Carts
from sqlalchemy.orm import sessionmaker
from usermanager import *
from datetime import date
from sqlalchemy import func, desc
# endregion

# region Initializations
user_router = Router()
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

class LeaveReview(StatesGroup):
    waiting_for_user_review_stars = State()
    waiting_for_user_review = State()

class Idle(StatesGroup):
    just_idle = State()

class AddToCart(StatesGroup):
    waiting_for_quantity = State()

# endregion

# region Features
@user_router.message(filters.Command('start'))
async def start(message: Message, state: FSMContext):
    await clean_bot_messages(message=message, state=state)
    
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Menu ⚙️'), KeyboardButton(text='Language 🌍')]
        ], resize_keyboard=True
    )
    
    await message.answer('Welcome to shop bot where you can buy staff', reply_markup=markup)

@user_router.message(F.text == 'Cancel the process ❌')
async def cancel_process(message: Message, state: FSMContext):
    await clean_bot_messages(message=message, state=state)
    await state.clear()
    markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text='Menu ⚙️'), KeyboardButton(text='Language 🌍')]
            ], resize_keyboard=True
        )
    await message.answer('Process was caceled ✅', reply_markup=markup)

@user_router.message(F.text == 'Menu ⚙️')
async def menu(message: Message, state: FSMContext):
    await clean_bot_messages(message=message, state=state)

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text = 'Register ✍️', callback_data='REGISTER')],
            [InlineKeyboardButton(text = 'Profile 👤', callback_data='PROFILE')],
            [InlineKeyboardButton(text = 'Edit Profile 📝', callback_data='EDIT_PROFILE')],
            [InlineKeyboardButton(text = 'Products 👕', callback_data='VIEW_CATEGORIES')],
            [InlineKeyboardButton(text = 'My Cart 🛒', callback_data='MY_CART')],
            [InlineKeyboardButton(text = 'Orders 📔', callback_data='ORDERS')],
            [InlineKeyboardButton(text = 'Order History 📖', callback_data='ORDERS_HISTORY')]
        ]
    )
    msg = await message.answer('Menu ⚙️', reply_markup=markup)
    await state.update_data(menu_msg_id = msg.message_id)

@user_router.callback_query(F.data == 'REGISTER')
async def register(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state = state)
    
    user = session.query(Users).filter_by(tg_id = call.from_user.id).first()
    if user != None:
        await call.message.answer(text = 'You are already registered ✅')
        return
    
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text = 'Cancel the process ❌')]
        ], resize_keyboard=True
    )
    await call.message.answer(text = 'Enter your name !', reply_markup=markup)
    await state.set_state(Register.waiting_for_name)

@user_router.message(Register.waiting_for_name)
async def get_user_name(message: Message, state: FSMContext):
    await clean_bot_messages(message=message, state=state)

    if await name_validation(message.text):
        await state.update_data(name = message.text)
        await state.set_state(Register.waiting_for_surname)
        await message.answer('Enter your surname !')
    
    else:
        await message.answer('Please enter your name correctly !')

@user_router.message(Register.waiting_for_surname)
async def get_user_surname(message: Message, state: FSMContext):
    await clean_bot_messages(message=message, state=state)

    if await surname_validation(message.text):
        await state.update_data(surname = message.text)
        await state.set_state(Register.waiting_for_age)
        await message.answer('Enter your age !')
    
    else:
        await message.answer('Please enter your surname correctly !')

@user_router.message(Register.waiting_for_age)
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

@user_router.callback_query(F.data == 'PROFILE')
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

@user_router.callback_query(F.data == 'EDIT_PROFILE')
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

@user_router.callback_query(F.data == 'EDIT_NAME')
async def edit_name(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    await state.set_state(EditProfile.waiting_for_new_name)
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text = 'Cancel the process ❌')]
        ], resize_keyboard=True
    )
    await call.message.answer(text = 'Please enter your new name !', reply_markup=markup)

@user_router.callback_query(F.data == 'EDIT_SURNAME')
async def edit_surname(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    await state.set_state(EditProfile.waiting_for_new_surname)
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text = 'Cancel the process ❌')]
        ], resize_keyboard=True
    )
    await call.message.answer(text = 'Please enter your new surname !', reply_markup=markup)

@user_router.callback_query(F.data == 'EDIT_AGE')
async def edit_age(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    await state.set_state(EditProfile.waiting_for_new_age)
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text = 'Cancel the process ❌')]
        ], resize_keyboard=True
    )
    await call.message.answer(text = 'Please enter your new age !', reply_markup=markup)

@user_router.message(EditProfile.waiting_for_new_name)
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

@user_router.message(EditProfile.waiting_for_new_surname)
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

@user_router.message(EditProfile.waiting_for_new_age)
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

@user_router.callback_query(F.data == 'VIEW_CATEGORIES')
async def show_categories(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)
    await state.clear()

    categories = session.query(Categories).order_by(Categories.title).limit(5).all()
    await state.update_data(page = 0, product_page = 1)
    keyboard = [
        [InlineKeyboardButton(
            text=f'{category.title}',
            callback_data=f'CATEGORY_{category.id}'
        )]
        for category in categories
    ]

    keyboard.append(
        [InlineKeyboardButton(text='Next ➡️', callback_data='NEXT')]
    )

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    msg = await call.message.answer(
        text='Choose a category 🌃',
        reply_markup=markup
    )

    await state.update_data(view_categories = msg.message_id)

@user_router.callback_query(F.data == 'NEXT')
async def next_category_page(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state = state)

    data = await state.get_data()
    page = data['page'] + 1
    await state.update_data(page = page)
    categories = session.query(Categories).order_by(Categories.title).offset(page * 5).limit(5).all()

    if len(categories):
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

    
    else:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='Back ⬅️', callback_data='BACK')]
            ]
        )

        msg = await call.message.answer(
            text='No other categories available ❌',
            reply_markup=markup
        )

    await state.update_data(view_categories = msg.message_id)

@user_router.callback_query(F.data == 'BACK')
async def previous_category_page(call: CallbackQuery, state: FSMContext):
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

@user_router.callback_query(F.data.startswith('CATEGORY_'))
async def show_products(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)
    
    data = await state.get_data()
    page = data.get('product_page', -1)
    if page == -1:
        await state.update_data(product_page = 1)
        page = 1

    ans = f'Products (page {page})'
    category_id = data.get('category_id', None)
    if category_id == None:
        category_id = int(call.data.split('_')[1])
        await state.update_data(category_id=category_id)
    
    order = data.get('order_by', 0)

    if order == 0:
        products = (
            session.query(Products)
            .filter_by(category_id=category_id)
            .order_by(Products.id)
            .offset((page - 1) * 5)
            .limit(5)
            .all()
        )

    elif order == 1:
        products = (
            session.query(Products)
            .filter_by(category_id=category_id)
            .order_by(Products.price)
            .offset((page - 1) * 5)
            .limit(5)
            .all()
        )

    else:
        products = (
            session.query(Products)
            .filter_by(category_id=category_id)
            .order_by(Products.avg_rating.desc())
            .offset((page - 1) * 5)
            .limit(5)
            .all()
        )
    
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text=f"{product.title} - {product.price} 💰 | ⭐ {product.avg_rating} ({product.reviews_count})",
                callback_data=f"PROD_{product.id}"
            )
        ]
        for product in products
    ]

    if len(products) and page > 1:
        inline_keyboard.append([
            InlineKeyboardButton(text='Sort by price 🏷', callback_data='SORT_PRICE'), InlineKeyboardButton(text='Sort by top-rated 🏆', callback_data='SORT_RATING')
        ])

        inline_keyboard.append([
            InlineKeyboardButton(text='Back ⬅️', callback_data='PREVIOUS_PRODUCTPAGE'),
            InlineKeyboardButton(text='Next ➡️', callback_data='NEXT_PRODUCTPAGE')
        ])

    else:

        if len(products):
            inline_keyboard.append([
                InlineKeyboardButton(text='Sort by price 🏷', callback_data='SORT_PRICE'), InlineKeyboardButton(text='Sort by top-rated 🏆', callback_data='SORT_RATING')
            ])

            inline_keyboard.append([
                InlineKeyboardButton(text='Next ➡️', callback_data='NEXT_PRODUCTPAGE')
            ])
        
        else:
            ans = 'No products are left ❌'
        
        if page > 1:
            inline_keyboard.append([
                InlineKeyboardButton(text='Back ⬅️', callback_data='PREVIOUS_PRODUCTPAGE')
            ])

    inline_keyboard.append([
        InlineKeyboardButton(text = 'Categories 🔙', callback_data='VIEW_CATEGORIES')
    ])


    markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    msg = await call.message.answer(text = ans, reply_markup=markup)
    await state.update_data(products_page = msg.message_id)

@user_router.callback_query(F.data == 'NEXT_PRODUCTPAGE')
async def next_product_page(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message = call.message, state = state)
    data = await state.get_data()
    page = data['product_page'] + 1
    category_id = data['category_id']
    ans = f'Products (Page {page})'
    await state.update_data(product_page=page)
    order = data.get('order_by', 0)
    offset = (page - 1) * 5
    if order == 0:
        products = (
            session.query(Products)
            .filter_by(category_id=category_id)
            .order_by(Products.id)
            .offset((page - 1) * 5)
            .limit(5)
            .all()
        )

    elif order == 1:
        products = (
            session.query(Products)
            .filter_by(category_id=category_id)
            .order_by(Products.price)
            .offset((page - 1) * 5)
            .limit(5)
            .all()
        )

    else:
        products = (
            session.query(Products)
            .filter_by(category_id=category_id)
            .order_by(Products.avg_rating.desc())
            .offset((page - 1) * 5)
            .limit(5)
            .all()
        )
    
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text=f"{product.title} - {product.price} 💰 | ⭐ {product.avg_rating} ({product.reviews_count})",
                callback_data=f"PROD_{product.id}"
            )
        ]
        for product in products
    ]

    if len(products) and page > 1:
        inline_keyboard.append([
            InlineKeyboardButton(text='Sort by price 🏷', callback_data='SORT_PRICE'), InlineKeyboardButton(text='Sort by top-rated 🏆', callback_data='SORT_RATING')
        ])

        inline_keyboard.append([
            InlineKeyboardButton(text='Back ⬅️', callback_data='PREVIOUS_PRODUCTPAGE'),
            InlineKeyboardButton(text='Next ➡️', callback_data='NEXT_PRODUCTPAGE')
        ])
    
    else:

        if len(products):
            inline_keyboard.append([
                InlineKeyboardButton(text='Sort by price 🏷', callback_data='SORT_PRICE'), InlineKeyboardButton(text='Sort by top-rated 🏆', callback_data='SORT_RATING')
            ])
            inline_keyboard.append([
                InlineKeyboardButton(text='Sort by price 🏷', callback_data='SORT_PRICE'), InlineKeyboardButton(text='Sort by top-rated 🏆', callback_data='SORT_RATING')
            ])
            
            inline_keyboard.append([
                InlineKeyboardButton(text='Next ➡️', callback_data='NEXT_PRODUCTPAGE')
            ])

        else:
            ans = 'No products are left ❌' 

        if page > 1:
            inline_keyboard.append([
                InlineKeyboardButton(text='Back ⬅️', callback_data='PREVIOUS_PRODUCTPAGE')
            ])

    inline_keyboard.append([
        InlineKeyboardButton(text = 'Categories 🔙', callback_data='VIEW_CATEGORIES')
    ])


    markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    msg = await call.message.answer(text=ans, reply_markup=markup)
    await state.update_data(products_page=msg.message_id)
    
@user_router.callback_query(F.data == 'PREVIOUS_PRODUCTPAGE')
async def previous_product_page(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message = call.message, state = state)
    data = await state.get_data()
    page = data['product_page'] - 1
    
    category_id = data['category_id']
    ans = f'Products (Page {page})'
    await state.update_data(product_page=page)
    order = data.get('order_by', 0)
    offset = (page - 1) * 5

    if order == 0:
        products = (
            session.query(Products)
            .filter_by(category_id=category_id)
            .order_by(Products.id)
            .offset((page - 1) * 5)
            .limit(5)
            .all()
        )

    elif order == 1:
        products = (
            session.query(Products)
            .filter_by(category_id=category_id)
            .order_by(Products.price)
            .offset((page - 1) * 5)
            .limit(5)
            .all()
        )

    else:
        products = (
            session.query(Products)
            .filter_by(category_id=category_id)
            .order_by(Products.avg_rating.desc())
            .offset((page - 1) * 5)
            .limit(5)
            .all()
        )
    
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text=f"{product.title} - {product.price} 💰 | ⭐ {product.avg_rating} ({product.reviews_count})",
                callback_data=f"PROD_{product.id}"
            )
        ]
        for product in products
    ]

    if len(products) and page > 1:
        inline_keyboard.append([
            InlineKeyboardButton(text='Sort by price 🏷', callback_data='SORT_PRICE'), InlineKeyboardButton(text='Sort by top-rated 🏆', callback_data='SORT_RATING')
        ])
        
        inline_keyboard.append([
            InlineKeyboardButton(text='Back ⬅️', callback_data='PREVIOUS_PRODUCTPAGE'),
            InlineKeyboardButton(text='Next ➡️', callback_data='NEXT_PRODUCTPAGE')
        ])

    else:
        if len(products):
            inline_keyboard.append([
                InlineKeyboardButton(text='Sort by price 🏷', callback_data='SORT_PRICE'), InlineKeyboardButton(text='Sort by top-rated 🏆', callback_data='SORT_RATING')
            ])

            inline_keyboard.append([
                InlineKeyboardButton(text='Next ➡️', callback_data='NEXT_PRODUCTPAGE')
            ])

        else:
            ans = 'No products are left ❌'

        if page > 1:
            inline_keyboard.append([
                InlineKeyboardButton(text='Back ⬅️', callback_data='PREVIOUS_PRODUCTPAGE')
            ])

    inline_keyboard.append([
        InlineKeyboardButton(text = 'Categories 🔙', callback_data='VIEW_CATEGORIES')
    ])


    markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    msg = await call.message.answer(text=ans, reply_markup=markup)
    await state.update_data(products_page=msg.message_id)

async def show_product_details(message, state: FSMContext, product_id: int, user_id):
    await clean_bot_messages(message=message, state=state)

    data = await state.get_data()
    category_id = data.get('category_id', None)

    product = session.get(Products, product_id)

    user = session.query(Users).filter_by(
        tg_id=user_id
    ).first()

    user_review_text = ""
    
    if user:
        review = session.query(Reviews).filter_by(
            user_id=user.id,
            product_id=product_id
        ).first()

        if review:
            stars_emoji = "⭐" * review.stars
            user_review_text = f"\n\n📝 Your Review: {stars_emoji}"
            if review.text:
                user_review_text += f"\n💬 {review.text}"

    caption = f""" 
🛍 {product.title} 

💰 Price: {product.price} 
📦 Stock: {product.stock}
🏆 Rating: {product.avg_rating}
{user_review_text}

📝 {product.description}
"""

    inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Add to Cart", callback_data=f"ADD_{product.id}")],
        [InlineKeyboardButton(text="✍ Leave Review", callback_data=f"LEAVE_REVIEW_{product_id}")],
        [InlineKeyboardButton(text="⭐ View Reviews", callback_data=f"REVIEWS_{product.id}")]
    ]
    

    if category_id != None:
        inline_keyboard.append(
            [InlineKeyboardButton(text="🔙 Back", callback_data=f"CATEGORY_{category_id}")]
        )
    
    else:
        inline_keyboard.append(
            [InlineKeyboardButton(text="🔙 Back", callback_data=f"MY_CART")]
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=inline_keyboard
    )

    if product.photo_file_id:
        msg = await message.answer_photo(
            photo=product.photo_file_id,
            caption=caption,
            reply_markup=keyboard
        )
    else:
        msg = await message.answer(
            text=caption,
            reply_markup=keyboard
        )

    await state.update_data(product_details=msg.message_id)

@user_router.callback_query(F.data.startswith('PROD_'))
async def product_detail(call: CallbackQuery, state: FSMContext):
    product_id = int(call.data.split("PROD_")[1])
    await state.set_state(Idle.just_idle)

    await show_product_details(call.message, state, product_id, call.from_user.id)

@user_router.callback_query(F.data == 'SORT_PRICE')
async def sort_price(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)
    await state.update_data(order_by = 1)
    await show_products(call, state)

@user_router.callback_query(F.data == 'SORT_RATING')
async def sort_rating(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)
    await state.update_data(order_by = 2)
    await show_products(call, state)

@user_router.callback_query(F.data.startswith("REVIEWS_"))
async def show_reviews(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    product_id = int(call.data.split("_")[1])

    product = session.query(Products).filter_by(id=product_id).first()

    reviews = (
        session.query(Reviews)
        .filter_by(product_id=product_id)
        .order_by(desc(Reviews.created_at))
        .limit(10)
        .all()
    )

    if not reviews:
        text = "No reviews yet for this product ⭐"
    else:
        text = f"🛍 Reviews for {product.title}\n\n"

        for review in reviews:
            user = session.query(Users).filter_by(id=review.user_id).first()

            stars_visual = "⭐" * review.stars

            text += (
                f"👤 {user.full_name}\n"
                f"{stars_visual} ({review.stars})\n"
                f"💬 {review.text}\n"
                f"──────────────\n"
            )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✍ Leave Review", callback_data=f"LEAVE_REVIEW_{product_id}")],
            [InlineKeyboardButton(text="🔙 Back to Product", callback_data=f"PROD_{product_id}")]
        ]
    )

    msg = await call.message.answer(text=text, reply_markup=keyboard)
    await state.update_data(reviews_message=msg.message_id)

@user_router.callback_query(F.data.startswith('LEAVE_REVIEW_'))
async def write_review(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    product_id = int(call.data.split('LEAVE_REVIEW_')[1])
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Back to product 🔙', callback_data=f'PROD_{product_id}')]
        ]
    )  
    msg = await call.message.answer(text='Leave your review as number from 1 to 5 (🌟)', reply_markup=markup)
    await state.update_data(product_to_review = product_id, review_request = msg.message_id)
    await state.set_state(LeaveReview.waiting_for_user_review_stars)

@user_router.message(LeaveReview.waiting_for_user_review_stars)
async def leave_review(message: Message, state: FSMContext):
    await clean_bot_messages(message=message, state=state)

    data = await state.get_data()
    product_id = data.get('product_to_review')

    if not await review_validation(message.text):
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text='Back to product 🔙',
                    callback_data=f'PROD_{product_id}'
                )]
            ]
        )
        msg = await message.answer(
            'Please enter a valid review 1 to 5',
            reply_markup=markup
        )
        await state.update_data(review_request=msg.message_id)
        return

    user = session.query(Users).filter_by(
        tg_id=message.from_user.id
    ).first()

    stars = int(message.text)

    existing_review = session.query(Reviews).filter_by(
        user_id=user.id,
        product_id=product_id
    ).first()

    if existing_review:
        existing_review.stars = stars
    else:
        new_review = Reviews(
            user_id=user.id,
            product_id=product_id,
            stars=stars
        )
        session.add(new_review)

    session.commit()

    avg_rating, reviews_count = (
        session.query(
            func.avg(Reviews.stars),
            func.count(Reviews.id)
        )
        .filter(Reviews.product_id == product_id)
        .first()
    )

    product = session.get(Products, product_id)
    product.avg_rating = round(avg_rating or 0, 2)
    product.reviews_count = reviews_count

    session.commit()

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='Back to product 🔙',
                callback_data=f'PROD_{product_id}'
            )]
        ]
    )

    msg = await message.answer(
        text='Star was updated! Now write your opinion about the product (optional)',
        reply_markup=markup
    )

    await state.update_data(review_request=msg.message_id)
    await state.set_state(LeaveReview.waiting_for_user_review)

@user_router.message(LeaveReview.waiting_for_user_review) 
async def leave_comment(message: Message, state: FSMContext): 
    await clean_bot_messages(message=message, state=state)

    data = await state.get_data() 
    product_id = data.get('product_to_review', None) 
    user = session.query(Users).filter_by(tg_id = message.from_user.id).first() 
    existing_review = session.query(Reviews).filter_by( user_id=user.id, product_id=product_id ).first() 
    
    if existing_review: 
        existing_review.text = message.text 
    
    else: 
        new_review = Reviews( user_id=user.id, product_id=product_id, text=message.text ) 
        session.add(new_review) 
        session.commit() 
    
    avg_rating, reviews_count = ( 
        session.query( func.avg(Reviews.stars), 
        func.count(Reviews.id) ) 
        .filter(Reviews.product_id == product_id) 
        .first() 
    )

    product = session.get(Products, product_id) 
    product.avg_rating = round(avg_rating or 0, 2) 
    product.reviews_count = reviews_count 
    session.commit() 
    
    await message.answer('Review was added successfully ✅')

    await state.set_state(Idle.just_idle)

    await show_product_details(message, state, product_id, message.from_user.id)

@user_router.callback_query(F.data.startswith('ADD_'))
async def get_quantity(call: CallbackQuery, state: FSMContext):

    product_id = int(call.data.split('_')[1])
    msg = await call.message.answer(
        'How many of this items you want to buy ?'
    )

    await state.update_data(product_to_buy = product_id, quantity_message_id=msg.message_id)
    await state.set_state(AddToCart.waiting_for_quantity)

@user_router.message(AddToCart.waiting_for_quantity)
async def add_to_cart(message: Message, state: FSMContext):

    data = await state.get_data()
    quantity_message_id = data.get('quantity_message_id')
    product_id = data.get('product_to_buy', 0)
    user = session.query(Users).filter_by(tg_id = message.from_user.id).first()
    cart = session.query(Carts).filter_by(user_id = user.id).first()
    product = session.query(Products).filter_by(id = product_id).first()
    
    try:
        qty = int(message.text)

        if qty > 0 and qty <= product.stock:
            if cart == None:
                cart = Carts(
                    user_id = user.id
                )

                cart_items = CartItems(
                    cart_id = cart.id,
                    product_id = product_id,
                    qty = int(message.text)
                )
                session.add(cart)
                session.add(cart_items)
                session.commit()
            
            else:
                cart_items = session.query(CartItems).filter_by(cart_id = cart.id, product_id = product_id).first()
                if cart_items == None:
                    cart_items = CartItems(
                        cart_id = cart.id,
                        product_id = product_id,
                        qty = qty
                    )
                
                else:
                    cart_items.qty = qty
                
                session.add(cart_items)
                session.commit()
            
            await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=quantity_message_id,
            text="Product was successfully added to your cart ✅"
        )

        elif qty <= 0:
            await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=quantity_message_id,
            text="Minimum item you can add to cart is 1"
        )

        else:
            await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=quantity_message_id,
            text="Sorry, currently we don't have that much stock for this product"
        )
    
    except Exception as e:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=quantity_message_id,
            text='Please enter a valid number'
        )
    
    finally:
        await message.delete()

async def render_cart(message, state: FSMContext, tg_user_id: int):
    data = await state.get_data()
    page = data.get("cart_page", 1)
    order = data.get("cart_order_by", 0)

    user = session.query(Users).filter_by(tg_id=tg_user_id).first()

    query = (
        session.query(Products, Carts.items.qty)
        .join(Carts, Carts.product_id == Products.id)
        .filter(Carts.user_id == user.id)
    )

    # Sorting
    if order == 0:
        query = query.order_by(Products.id)
    elif order == 1:
        query = query.order_by(Products.price)
    else:
        query = query.order_by(Products.avg_rating.desc())

    items = (
        query
        .offset((page - 1) * 5)
        .limit(5)
        .all()
    )

    if not items:
        await message.answer("🛒 Your cart is empty.")
        return

    text = f"🛒 Your Cart (Page {page})"

    keyboard = []

    for product, quantity in items:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{product.title}",
                callback_data=f"CARTPROD_{product.id}"
            )
        ])

    # Sorting buttons
    keyboard.append([
        InlineKeyboardButton(text="Sort by price 🏷", callback_data="CART_SORT_PRICE"),
        InlineKeyboardButton(text="Sort by rating 🏆", callback_data="CART_SORT_RATING"),
    ])

    # Pagination
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅ Back", callback_data="CART_PREV")
        )

    if len(items) == 5:
        nav_buttons.append(
            InlineKeyboardButton(text="Next ➡", callback_data="CART_NEXT")
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([
        InlineKeyboardButton(text="🔙 Main Menu", callback_data="MAIN_MENU")
    ])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    msg = await message.answer(text, reply_markup=markup)
    await state.update_data(cart_message_id=msg.message_id)

@user_router.callback_query(F.data == "MY_CART")
async def show_cart(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    data = await state.get_data()
    page = data.get('cart_page', -1)

    if page == -1:
        await state.update_data(cart_page=1)
        page = 1

    order = data.get('cart_order_by', 0)

    user = session.query(Users).filter_by(
        tg_id=call.from_user.id
    ).first()

    if not user:
        await call.message.answer("User not found ❌")
        return

    cart = session.query(Carts).filter_by(
        user_id=user.id,
        status='active'
    ).first()

    cart_items = session.query(CartItems).filter_by(
        cart_id=cart.id
    ).all()

    total_qty = sum(item.qty for item in cart_items)

    total_price = sum(
        item.qty * item.product.price
        for item in cart_items
    )

    ans = f"""🛒 Your Cart (page {page})

📦 Total Items: {total_qty}
💰 Total Price: {total_price}
"""

    if not cart:
        await call.message.answer("Your cart is empty ❌")
        return

    query = (
        session.query(Products)
        .join(CartItems, CartItems.product_id == Products.id)
        .filter(CartItems.cart_id == cart.id)
    )

    if order == 0:
        query = query.order_by(Products.id)

    elif order == 1:
        query = query.order_by(Products.price)

    else:
        query = query.order_by(Products.avg_rating.desc())

    products = (
        query
        .offset((page - 1) * 5)
        .limit(5)
        .all()
    )

    inline_keyboard = [
        [
            InlineKeyboardButton(
                text=f"{product.title} - {product.price} 💰 | ⭐ {product.avg_rating} ({product.reviews_count})",
                callback_data=f"CARTPROD_{product.id}"
            )
        ]
        for product in products
    ]

    if len(products) and page > 1:
        inline_keyboard.append([
            InlineKeyboardButton(text='Sort by price 🏷', callback_data='CART_SORT_PRICE'),
            InlineKeyboardButton(text='Sort by top-rated 🏆', callback_data='CART_SORT_RATING')
        ])

        inline_keyboard.append([
            InlineKeyboardButton(text='Back ⬅️', callback_data='CART_PREVIOUS_PAGE'),
            InlineKeyboardButton(text='Next ➡️', callback_data='CART_NEXT_PAGE')
        ])

    else:

        if len(products):
            inline_keyboard.append([
                InlineKeyboardButton(text='Sort by price 🏷', callback_data='CART_SORT_PRICE'),
                InlineKeyboardButton(text='Sort by top-rated 🏆', callback_data='CART_SORT_RATING')
            ])

            inline_keyboard.append([
                InlineKeyboardButton(text='Next ➡️', callback_data='CART_NEXT_PAGE')
            ])

        else:
            ans = 'Your cart is empty ❌'

        if page > 1:
            inline_keyboard.append([
                InlineKeyboardButton(text='Back ⬅️', callback_data='CART_PREVIOUS_PAGE')
            ])

    inline_keyboard.append([
        InlineKeyboardButton(text="🛍 Checkout", callback_data="CHECKOUT"),
        InlineKeyboardButton(text='🔙 Main Menu', callback_data='MAIN_MENU')
    ])

    markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    msg = await call.message.answer(text=ans, reply_markup=markup)
    await state.update_data(cart_message_id=msg.message_id)

@user_router.callback_query(F.data == 'MAIN_MENU')
async def menu(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text = 'Register ✍️', callback_data='REGISTER')],
            [InlineKeyboardButton(text = 'Profile 👤', callback_data='PROFILE')],
            [InlineKeyboardButton(text = 'Edit Profile 📝', callback_data='EDIT_PROFILE')],
            [InlineKeyboardButton(text = 'Products 👕', callback_data='VIEW_CATEGORIES')],
            [InlineKeyboardButton(text = 'My Cart 🛒', callback_data='MY_CART')],
            [InlineKeyboardButton(text = 'Orders 📔', callback_data='ORDERS')],
            [InlineKeyboardButton(text = 'Order History 📖', callback_data='ORDERS_HISTORY')]
        ]
    )
    msg = await call.message.answer('Menu ⚙️', reply_markup=markup)
    await state.update_data(menu_msg_id = msg.message_id)

@user_router.callback_query(F.data == 'CART_NEXT_PAGE')
async def cart_next_page(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('cart_page', 1) + 1
    await state.update_data(cart_page=page)

    ans = f'🛒 Your Cart (Page {page})'
    order = data.get('cart_order_by', 0)

    user = session.query(Users).filter_by(
        tg_id=call.from_user.id
    ).first()

    cart = session.query(Carts).filter_by(
        user_id=user.id,
        status='active'
    ).first()

    cart_items = session.query(CartItems).filter_by(
        cart_id=cart.id
    ).all()

    total_qty = sum(item.qty for item in cart_items)

    total_price = sum(
        item.qty * item.product.price
        for item in cart_items
    )

    ans = f"""🛒 Your Cart (page {page})

📦 Total Items: {total_qty}
💰 Total Price: {total_price}
"""
    

    query = (
        session.query(Products)
        .join(CartItems, CartItems.product_id == Products.id)
        .filter(CartItems.cart_id == cart.id)
    )

    if order == 0:
        query = query.order_by(Products.id)
    elif order == 1:
        query = query.order_by(Products.price)
    else:
        query = query.order_by(Products.avg_rating.desc())

    products = (
        query
        .offset((page - 1) * 5)
        .limit(5)
        .all()
    )

    inline_keyboard = [
        [
            InlineKeyboardButton(
                text=f"{product.title} - {product.price} 💰 | ⭐ {product.avg_rating} ({product.reviews_count})",
                callback_data=f"CARTPROD_{product.id}"
            )
        ]
        for product in products
    ]

    if len(products) and page > 1:
        inline_keyboard.append([
            InlineKeyboardButton(text='Sort by price 🏷', callback_data='CART_SORT_PRICE'),
            InlineKeyboardButton(text='Sort by top-rated 🏆', callback_data='CART_SORT_RATING')
        ])

        inline_keyboard.append([
            InlineKeyboardButton(text='Back ⬅️', callback_data='CART_PREVIOUS_PAGE'),
            InlineKeyboardButton(text='Next ➡️', callback_data='CART_NEXT_PAGE')
        ])
    else:
        if len(products):
            inline_keyboard.append([
                InlineKeyboardButton(text='Sort by price 🏷', callback_data='CART_SORT_PRICE'),
                InlineKeyboardButton(text='Sort by top-rated 🏆', callback_data='CART_SORT_RATING')
            ])

            inline_keyboard.append([
                InlineKeyboardButton(text='Next ➡️', callback_data='CART_NEXT_PAGE')
            ])
        else:
            ans = 'No products are left ❌'

        if page > 1:
            inline_keyboard.append([
                InlineKeyboardButton(text='Back ⬅️', callback_data='CART_PREVIOUS_PAGE')
            ])

    inline_keyboard.append([
        InlineKeyboardButton(text="🛍 Checkout", callback_data="CHECKOUT"),
        InlineKeyboardButton(text='🔙 Main Menu', callback_data='MAIN_MENU')
    ])

    markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    await call.message.edit_text(text=ans, reply_markup=markup)
    await state.update_data(cart_message_id=call.message.message_id)

@user_router.callback_query(F.data == 'CART_PREVIOUS_PAGE')
async def cart_previous_page(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('cart_page', 1) - 1
    await state.update_data(cart_page=page)

    ans = f'🛒 Your Cart (Page {page})'
    order = data.get('cart_order_by', 0)

    user = session.query(Users).filter_by(
        tg_id=call.from_user.id
    ).first()

    cart = session.query(Carts).filter_by(
        user_id=user.id,
        status='active'
    ).first()

    cart_items = session.query(CartItems).filter_by(
        cart_id=cart.id
    ).all()

    total_qty = sum(item.qty for item in cart_items)

    total_price = sum(
        item.qty * item.product.price
        for item in cart_items
    )

    ans = f"""🛒 Your Cart (page {page})

📦 Total Items: {total_qty}
💰 Total Price: {total_price}
"""

    query = (
        session.query(Products)
        .join(CartItems, CartItems.product_id == Products.id)
        .filter(CartItems.cart_id == cart.id)
    )

    if order == 0:
        query = query.order_by(Products.id)
    elif order == 1:
        query = query.order_by(Products.price)
    else:
        query = query.order_by(Products.avg_rating.desc())

    products = (
        query
        .offset((page - 1) * 5)
        .limit(5)
        .all()
    )

    inline_keyboard = [
        [
            InlineKeyboardButton(
                text=f"{product.title} - {product.price} 💰 | ⭐ {product.avg_rating} ({product.reviews_count})",
                callback_data=f"CARTPROD_{product.id}"
            )
        ]
        for product in products
    ]

    if len(products) and page > 1:
        inline_keyboard.append([
            InlineKeyboardButton(text='Sort by price 🏷', callback_data='CART_SORT_PRICE'),
            InlineKeyboardButton(text='Sort by top-rated 🏆', callback_data='CART_SORT_RATING')
        ])

        inline_keyboard.append([
            InlineKeyboardButton(text='Back ⬅️', callback_data='CART_PREVIOUS_PAGE'),
            InlineKeyboardButton(text='Next ➡️', callback_data='CART_NEXT_PAGE')
        ])
    else:
        if len(products):
            inline_keyboard.append([
                InlineKeyboardButton(text='Sort by price 🏷', callback_data='CART_SORT_PRICE'),
                InlineKeyboardButton(text='Sort by top-rated 🏆', callback_data='CART_SORT_RATING')
            ])

            inline_keyboard.append([
                InlineKeyboardButton(text='Next ➡️', callback_data='CART_NEXT_PAGE')
            ])
        else:
            ans = 'No products are left ❌'

        if page > 1:
            inline_keyboard.append([
                InlineKeyboardButton(text='Back ⬅️', callback_data='CART_PREVIOUS_PAGE')
            ])

    inline_keyboard.append([
        InlineKeyboardButton(text="🛍 Checkout", callback_data="CHECKOUT"),
        InlineKeyboardButton(text='🔙 Main Menu', callback_data='MAIN_MENU')
    ])

    markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    await call.message.edit_text(text=ans, reply_markup=markup)
    await state.update_data(cart_message_id=call.message.message_id)

@user_router.callback_query(F.data == 'CART_SORT_PRICE')
async def cart_sort_price(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)
    
    await state.update_data(
        cart_order_by=1,
        cart_page=1
    )

    await show_cart(call, state)

@user_router.callback_query(F.data == 'CART_SORT_RATING')
async def cart_sort_rating(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)
    
    await state.update_data(
        cart_order_by=2,
        cart_page=1
    )

    await show_cart(call, state)

@user_router.callback_query(F.data.startswith('CARTPROD_'))
async def cart_product_details(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    product_id = int(call.data.split('_')[1])

    user = session.query(Users).filter_by(
        tg_id=call.from_user.id
    ).first()

    if not user:
        await call.message.answer("User not found ❌")
        return

    cart = session.query(Carts).filter_by(
        user_id=user.id,
        status='active'
    ).first()

    if not cart:
        await call.message.answer("Cart not found ❌")
        return

    cart_item = session.query(CartItems).filter_by(
        cart_id=cart.id,
        product_id=product_id
    ).first()

    if not cart_item:
        await call.message.answer("Product not in cart ❌")
        return

    product = session.get(Products, product_id)

    caption = f"""
🛍 {product.title}

💰 Price: {product.price}
🏆 Rating: {product.avg_rating}
📦 Quantity in Cart: {cart_item.qty}

📝 {product.description}
"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Remove from Cart",
                    callback_data=f"REMOVE_CART_{product.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back to Cart",
                    callback_data="MY_CART"
                )
            ]
        ]
    )

    if product.photo_file_id:
        msg = await call.message.answer_photo(
            photo=product.photo_file_id,
            caption=caption,
            reply_markup=keyboard
        )
    else:
        msg = await call.message.answer(
            text=caption,
            reply_markup=keyboard
        )
    
    await state.update_data(cart_prod_details = msg.message_id)

@user_router.callback_query(F.data.startswith('REMOVE_CART_'))
async def remove_from_cart(call: CallbackQuery, state: FSMContext):
    product_id = int(call.data.split('_')[2])

    user = session.query(Users).filter_by(
        tg_id=call.from_user.id
    ).first()

    cart = session.query(Carts).filter_by(
        user_id=user.id,
        status='active'
    ).first()

    cart_item = session.query(CartItems).filter_by(
        cart_id=cart.id,
        product_id=product_id
    ).first()

    if cart_item:
        session.delete(cart_item)
        session.commit()

    await call.answer("Removed from cart ✅")

    await clean_bot_messages(message=call.message, state=state)
    await show_cart(call, state)

@user_router.callback_query(F.data == "CHECKOUT")
async def checkout(call: CallbackQuery, state: FSMContext):

    user = session.query(Users).filter_by(
        tg_id=call.from_user.id
    ).first()

    cart = session.query(Carts).filter_by(
        user_id=user.id,
        status='active'
    ).first()

    if not cart or not cart.items:
        await call.answer("Cart is empty ❌")
        return

    total_price = sum(
        item.qty * item.product.price
        for item in cart.items
    )

    order = Orders(
        user_id=user.id,
        total_price=total_price,
        status='pending'
    )

    session.add(order)
    session.commit()

    for item in cart.items:
        order_item = OrderItems(
            order_id=order.id,
            product_id=item.product_id,
            qty=item.qty,
            price_at_buy=item.product.price
        )
        session.add(order_item)

    session.query(CartItems).filter_by(cart_id=cart.id).delete()

    session.commit()

    await call.message.answer(
        f"✅ Order created!\n\n🧾 Order ID: {order.id}\n💰 Total: {total_price}"
    )

    await show_cart(call, state)

@user_router.callback_query(F.data == "ORDERS")
async def show_orders(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    await state.update_data(order_page=1)
    await render_pending_orders(call, state)

async def render_pending_orders(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get("order_page", 1)

    user = session.query(Users).filter_by(
        tg_id=call.from_user.id
    ).first()

    query = session.query(Orders).filter_by(
        user_id=user.id,
        status='pending'
    ).order_by(Orders.created_at.desc())

    total_orders = query.count()
    total_pages = (total_orders + 5 - 1) // 5

    orders = query.offset(
        (page - 1) * 5
    ).limit(5).all()

    if not orders:
        await call.message.answer("You have no pending orders 📦")
        return

    keyboard = []

    for order in orders:
        keyboard.append([
            InlineKeyboardButton(
                text=f"Order #{order.id} | {order.total_price}",
                callback_data=f"ORDER_{order.id}"
            )
        ])

    # Pagination buttons
    nav_row = []

    if page > 1:
        nav_row.append(
            InlineKeyboardButton(
                text="⬅ Back",
                callback_data="PENDING_PREV"
            )
        )

    if page < total_pages:
        nav_row.append(
            InlineKeyboardButton(
                text="Next ➡",
                callback_data="PENDING_NEXT"
            )
        )

    if nav_row:
        keyboard.append(nav_row)

    keyboard.append([
        InlineKeyboardButton(
            text="🔙 Back",
            callback_data="MAIN_MENU"
        )
    ])

    msg = await call.message.answer(
        f"📦 Pending Orders (Page {page}/{total_pages})",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

    await state.update_data(orders=msg.message_id)

@user_router.callback_query(F.data == "PENDING_NEXT")
async def pending_next(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get("order_page", 1) + 1

    await state.update_data(order_page=page)
    await clean_bot_messages(call.message, state)
    await render_pending_orders(call, state)

@user_router.callback_query(F.data == "PENDING_PREV")
async def pending_prev(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = max(1, data.get("order_page", 1) - 1)

    await state.update_data(order_page=page)
    await clean_bot_messages(call.message, state)
    await render_pending_orders(call, state)

@user_router.callback_query(F.data.startswith("CANCEL_"))
async def cancel_order(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(call.message, state)

    order_id = int(call.data.split("_")[1])

    order = session.get(Orders, order_id)

    if not order:
        await call.answer("Order not found")
        return

    if order.user.tg_id != call.from_user.id:
        await call.answer("Access denied")
        return

    if order.status != "pending":
        await call.answer("Only pending orders can be cancelled")
        return

    order.status = "cancelled"
    session.commit()

    await call.answer("Order cancelled ✅")

    await show_orders(call, state)

@user_router.callback_query(F.data == "ORDERS_HISTORY")
async def show_orders(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(call.message, state)

    await state.update_data(order_page=1)
    await render_order_history(call, state)

async def render_order_history(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get("order_page", 1)

    user = session.query(Users).filter_by(
        tg_id=call.from_user.id
    ).first()

    query = session.query(Orders).filter(
        Orders.user_id == user.id,
        Orders.status.in_(["paid", "cancelled"])
    ).order_by(Orders.created_at.desc())

    total_orders = query.count()
    total_pages = (total_orders + 5 - 1) // 5

    orders = query.offset(
        (page - 1) * 5
    ).limit(5).all()

    if not orders:
        await call.message.answer("No order history found 📦")
        return

    text = f"📜 Order History (Page {page}/{total_pages})\n\n"

    for order in orders:
        text += (
            f"🧾 ID: {order.id}\n"
            f"📌 Status: {order.status}\n"
            f"💰 Amount: {order.total_price}\n"
            f"🕒 Date: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"──────────────\n"
        )

    keyboard = []
    nav_row = []

    if page > 1:
        nav_row.append(
            InlineKeyboardButton(
                text="⬅ Back",
                callback_data="ORDERS_PREV"
            )
        )

    if page < total_pages:
        nav_row.append(
            InlineKeyboardButton(
                text="Next ➡",
                callback_data="ORDERS_NEXT"
            )
        )

    if nav_row:
        keyboard.append(nav_row)

    keyboard.append([
        InlineKeyboardButton(
            text="🔙 Main Menu",
            callback_data="MAIN_MENU"
        )
    ])

    msg = await call.message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

    await state.update_data(order_history = msg.message_id)

@user_router.callback_query(F.data == "ORDERS_NEXT")
async def orders_next(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get("order_page", 1) + 1

    await state.update_data(order_page=page)
    await clean_bot_messages(call.message, state)
    await render_order_history(call, state)

@user_router.callback_query(F.data == "ORDERS_PREV")
async def orders_prev(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = max(1, data.get("order_page", 1) - 1)

    await state.update_data(order_page=page)
    await clean_bot_messages(call.message, state)
    await render_order_history(call, state)

async def clean_bot_messages(message: Message, state: FSMContext):
    data = await state.get_data()
    keys = ['editing_msg', 'category_selection', 'edit_product_msg', 'product_managment', 'order_history', 'order_details', 'orders', 'cart_prod_details', 'cart_message_id', 'review_request', 'reviews_message', 'products_page', 'menu_msg_id', 'profile_msg_id', 'editprofile_msg_id', 'view_categories', 'product_details', 'category_selection', 'edit_product', 'reviews_message', 'menu', 'product_details', 'product_managment']
    
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

