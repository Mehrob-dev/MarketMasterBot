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
from admin_filter import IsAdmin
from user import clean_bot_messages
from adminmanager import *
# endregion

# region Initializations

admin_router = Router()
admin_router.message.filter(IsAdmin())
admin_router.callback_query.filter(IsAdmin())
Session = sessionmaker(engine)
session = Session()

class Idle(StatesGroup):
    just_idle = State()

class EditProduct(StatesGroup):
    waiting_for_new_category = State()
    waiting_for_new_title = State()
    waiting_for_new_description = State()
    waiting_for_new_price = State()
    waiting_for_new_stock = State()
    waiting_for_new_photo = State()


# endregion

# region Features

@admin_router.message(filters.Command('start'))
async def hello_admin(message: Message, state: FSMContext):
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Menu ⚙️'), KeyboardButton(text='Language 🌍')]
        ], resize_keyboard=True
    )

    await message.answer(text = 'Hello Admin !', reply_markup = markup)

@admin_router.message(F.text == 'Cancel editingll ❌')
async def cancel_process(message: Message, state: FSMContext):
    await clean_bot_messages(message=message, state=state)
    await state.clear()
    await message.answer('Process was caceled ✅')
    
@admin_router.message(F.text == "Menu ⚙️")
async def admin_menu(message: Message, state: FSMContext):
    await clean_bot_messages(message = message, state = state)

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Manage Products", callback_data="admin_products")],
            [InlineKeyboardButton(text="📊 Orders", callback_data="admin_orders")],
            [InlineKeyboardButton(text="👥 Users", callback_data="admin_users")]
        ]
    )

    msg = await message.answer("⚙️ Admin Panel", reply_markup=markup)
    await state.update_data(menu = msg.message_id)

@admin_router.callback_query(F.data == "admin_menu")
async def admin_menu(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message = call.message, state = state)
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Manage Products", callback_data="admin_products")],
            [InlineKeyboardButton(text="📊 Orders", callback_data="admin_orders")],
            [InlineKeyboardButton(text="👥 Users", callback_data="admin_users")]
        ]
    )

    msg = await call.message.answer("⚙️ Admin Panel", reply_markup=markup)
    await state.update_data(menu = msg.message_id)

@admin_router.callback_query(F.data == "admin_products")
async def admin_products_panel(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message = call.message, state = state)

    msg = await call.message.answer(
        "📦 Products Management",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📋 Show Products", callback_data="VIEW_CATEGORIES")],
                [InlineKeyboardButton(text="➕ Add Product", callback_data="admin_add_product")],
                [InlineKeyboardButton(text="🔙 Back", callback_data="admin_menu")]
            ]
        )
    )

    await state.update_data(product_managment = msg.message_id)

async def show_product_details(message, state: FSMContext, product_id: int, user_id):
    await clean_bot_messages(message=message, state=state)

    data = await state.get_data()
    category_id = data.get('category_id', None)

    product = session.get(Products, product_id)

    user = session.query(Users).filter_by(
        tg_id=user_id
    ).first()

    caption = f""" 
🛍 {product.title} 

💰 Price: {product.price} 
📦 Stock: {product.stock}
🏆 Rating: {product.avg_rating}

📝 {product.description}
"""

    inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Edit product", callback_data=f"admin_edit_product_{product.id}")],
        [InlineKeyboardButton(text="🗑 Remove product", callback_data=f"LEAVE_REVIEW_{product_id}")],
        [InlineKeyboardButton(text="⭐ View Reviews", callback_data=f"REVIEWS_{product.id}")]
    ]
    
    inline_keyboard.append(
        [InlineKeyboardButton(text="🔙 Back", callback_data=f"CATEGORY_{category_id}")]
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

@admin_router.callback_query(F.data.startswith('PROD_'))
async def product_detail(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message = call.message, state = state)
    product_id = int(call.data.split("PROD_")[1])
    await state.set_state(Idle.just_idle)

    await show_product_details(call.message, state, product_id, call.from_user.id)

@admin_router.callback_query(F.data.startswith("REVIEWS_"))
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
            [InlineKeyboardButton(text="🔙 Back to Product", callback_data=f"PROD_{product_id}")]
        ]
    )

    msg = await call.message.answer(text=text, reply_markup=keyboard)
    await state.update_data(reviews_message=msg.message_id)

@admin_router.callback_query(F.data.startswith('admin_edit_product_'))
async def edit_product(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    product_id = int(call.data.split('admin_edit_product_')[1])
    product = session.query(Products).filter_by(id=product_id).first()

    if not product:
        await call.answer("Product not found ❌", show_alert=True)
        return

    await state.update_data(product_to_edit=product.id)

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f'Category: {product.category.title}', callback_data='admin_edit_category')],
            [InlineKeyboardButton(text=f'Title: {product.title}', callback_data='admin_edit_title')],
            [InlineKeyboardButton(text=f'Description: {product.description}', callback_data='admin_edit_description')],
            [InlineKeyboardButton(text=f'Price: {product.price}', callback_data='admin_edit_price')],
            [InlineKeyboardButton(text=f'Stock: {product.stock}', callback_data='admin_edit_stock')],
            [InlineKeyboardButton(text='Photo', callback_data='admin_edit_photo')],
            [InlineKeyboardButton(text='⬅ Back to Product', callback_data=f'PROD_{product_id}')]
        ]
    )

    msg = await call.message.answer(
        text='Choose what you want to edit:',
        reply_markup=markup
    )

    await state.update_data(edit_product_msg = msg.message_id)

@admin_router.callback_query(F.data == 'admin_edit_category')
async def edit_category(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    await state.update_data(category_page=0)
    await show_category_selection(call.message, state)

async def show_category_selection(message: Message, state: FSMContext):
    await clean_bot_messages(message = message, state = state)

    data = await state.get_data()
    page = data.get('category_page', 0)

    categories = (
        session.query(Categories)
        .order_by(Categories.title)
        .offset(page * 5)
        .limit(5)
        .all()
    )

    keyboard = [
        [
            InlineKeyboardButton(
                text=category.title,
                callback_data=f'admin_set_category_{category.id}'
            )
        ]
        for category in categories
    ]

    navigation = []

    if page > 0:
        navigation.append(
            InlineKeyboardButton(text='⬅ Back', callback_data='admin_category_prev')
        )

    if len(categories) == 5:
        navigation.append(
            InlineKeyboardButton(text='Next ➡', callback_data='admin_category_next')
        )

    if navigation:
        keyboard.append(navigation)

    keyboard.append([
        InlineKeyboardButton(text='Cancel ❌', callback_data='admin_cancel_category_edit')
    ])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    msg = await message.answer(
        text=f'Select new category (Page {page + 1}):',
        reply_markup=markup
    )

    await state.update_data(category_selection = msg.message_id)

@admin_router.callback_query(F.data == 'admin_category_next')
async def next_category_page(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    data = await state.get_data()
    page = data.get('category_page', 0) + 1
    await state.update_data(category_page=page)

    await show_category_selection(call.message, state)

@admin_router.callback_query(F.data == 'admin_category_prev')
async def prev_category_page(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    data = await state.get_data()
    page = data.get('category_page', 0) - 1
    await state.update_data(category_page=page)

    await show_category_selection(call.message, state)

@admin_router.callback_query(F.data.startswith('admin_set_category_'))
async def set_new_category(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    category_id = int(call.data.split('_')[-1])

    data = await state.get_data()
    product_id = data.get('product_to_edit')

    if not product_id:
        await call.answer("Product not found ❌", show_alert=True)
        return

    product = session.get(Products, product_id)
    product.category_id = category_id
    session.commit()

    await call.message.answer("Category updated successfully ✅")

    fake_call = type('obj', (object,), {
        'message': call.message,
        'data': f'admin_edit_product_{product_id}'
    })

    await edit_product(fake_call, state)

@admin_router.callback_query(F.data == 'admin_cancel_category_edit')
async def cancel_category_edit(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    data = await state.get_data()
    product_id = data.get('product_to_edit')

    fake_call = type('obj', (object,), {
        'message': call.message,
        'data': f'admin_edit_product_{product_id}'
    })

    await edit_product(fake_call, state)

@admin_router.callback_query(F.data == "admin_edit_title")
async def admin_edit_title(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message = call.message, state = state)
    await call.answer()

    await state.set_state(EditProduct.waiting_for_new_title)
    data = await state.get_data()
    product_id = data.get("product_to_edit")

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text = 'Cancel editing ❌', callback_data=f'admin_edit_product_{product_id}')]
        ]
    )

    msg = await call.message.answer(
        "✏️ Please send new product title.\n\n"
        "Press cancel to stop.", reply_markup = markup
    )

    await state.update_data(editing_msg = msg.message_id)

@admin_router.message(EditProduct.waiting_for_new_title)
async def process_new_title(message: Message, state: FSMContext):
    await clean_bot_messages(message = message, state = state)
    data = await state.get_data()
    product_id = data.get("product_to_edit")
    product = session.query(Products).filter_by(id = product_id).first()
    new_title = message.text

    product.title = new_title
    session.commit()

    await message.answer("Title updated successfully ✅")

    await state.set_state(Idle.just_idle)
    await state.update_data(product_to_edit = product_id)

    fake_call = type('obj', (object,), {
        'message': message,
        'data': f'admin_edit_product_{product_id}'
    })

    await edit_product(fake_call, state)

@admin_router.callback_query(F.data == "admin_edit_description")
async def admin_edit_description(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message = call.message, state = state)
    await call.answer()

    await state.set_state(EditProduct.waiting_for_new_description)
    data = await state.get_data()
    product_id = data.get("product_to_edit")

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text = 'Cancel editing ❌', callback_data=f'admin_edit_product_{product_id}')]
        ]
    )

    msg = await call.message.answer(
        "📝 Please send new product description.\n\n"
        "Press cancel to stop.", reply_markup = markup
    )

    await state.update_data(editing_msg = msg.message_id)

@admin_router.message(EditProduct.waiting_for_new_description)
async def process_new_description(message: Message, state: FSMContext):
    await clean_bot_messages(message = message, state = state)
    data = await state.get_data()
    product_id = data.get("product_to_edit")
    product = session.query(Products).filter_by(id = product_id).first()
    new_description = message.text

    product.description = new_description
    session.commit()

    await message.answer("Description updated successfully ✅")

    await state.set_state(Idle.just_idle)
    await state.update_data(product_to_edit = product_id)

    fake_call = type('obj', (object,), {
        'message': message,
        'data': f'admin_edit_product_{product_id}'
    })

    await edit_product(fake_call, state)

@admin_router.callback_query(F.data == 'admin_edit_price')
async def admin_edit_price(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message = call.message, state = state)
    await call.answer()

    await state.set_state(EditProduct.waiting_for_new_price)
    data = await state.get_data()
    product_id = data.get("product_to_edit")

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text = 'Cancel editing ❌', callback_data=f'admin_edit_product_{product_id}')]
        ]
    )

    msg = await call.message.answer(
        "📝 Please send new product price.\n\n"
        "Press cancel to stop.", reply_markup = markup
    )

    await state.update_data(editing_msg = msg.message_id)

@admin_router.message(EditProduct.waiting_for_new_price)
async def process_new_price(message: Message, state: FSMContext):
    await clean_bot_messages(message = message, state = state)
    data = await state.get_data()
    product_id = data.get("product_to_edit")
    product = session.query(Products).filter_by(id = product_id).first()
    new_price = message.text

    if await price_validation(new_price):
        product.price = float(new_price)
        session.commit()

        await message.answer("Price updated successfully ✅")

        await state.set_state(Idle.just_idle)
        await state.update_data(product_to_edit = product_id)

        fake_call = type('obj', (object,), {
            'message': message,
            'data': f'admin_edit_product_{product_id}'
        })

        await edit_product(fake_call, state)
    
    else:
        await message.answer('Price must include only numbers, try again !')

@admin_router.callback_query(F.data == 'admin_edit_stock')
async def admin_edit_stock(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message = call.message, state = state)
    await call.answer()

    await state.set_state(EditProduct.waiting_for_new_stock)
    data = await state.get_data()
    product_id = data.get("product_to_edit")

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text = 'Cancel editing ❌', callback_data=f'admin_edit_product_{product_id}')]
        ]
    )

    msg = await call.message.answer(
        "📝 Please send new product stock.\n\n"
        "Press cancel to stop.", reply_markup = markup
    )

    await state.update_data(editing_msg = msg.message_id)

@admin_router.message(EditProduct.waiting_for_new_stock)
async def process_new_description(message: Message, state: FSMContext):
    await clean_bot_messages(message = message, state = state)
    data = await state.get_data()
    product_id = data.get("product_to_edit")
    product = session.query(Products).filter_by(id = product_id).first()
    new_stock = message.text

    if await stock_validation(new_stock):
        product.stock = int(new_stock)
        session.commit()

        await message.answer("Stock updated successfully ✅")

        await state.set_state(Idle.just_idle)
        await state.update_data(product_to_edit = product_id)

        fake_call = type('obj', (object,), {
            'message': message,
            'data': f'admin_edit_product_{product_id}'
        })

        await edit_product(fake_call, state)
    
    else:
        await message.answer('Stock must include only numbers, try again !')

@admin_router.callback_query(F.data == "admin_edit_photo")
async def admin_edit_photo(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message = call.message, state = state)
    await call.answer()

    await state.set_state(EditProduct.waiting_for_new_photo)
    data = await state.get_data()
    product_id = data.get("product_to_edit")

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text = 'Cancel editing ❌', callback_data=f'admin_edit_product_{product_id}')]
        ]
    )

    msg = await call.message.answer(
        "📷 Please send the new product photo.\n\n"
        "Press cancel to stop.", reply_markup = markup
    )

    await state.update_data(editing_msg = msg.message_id)

@admin_router.message(EditProduct.waiting_for_new_photo, F.photo)
async def process_new_photo(message: Message, state: FSMContext):
    await clean_bot_messages(message = message, state = state)
    data = await state.get_data()
    product_id = data.get("product_to_edit")
    product = session.query(Products).filter_by(id = product_id).first()
    new_file_id = message.photo[-1].file_id

    product.photo_file_id = new_file_id

    await message.answer("Photo updated successfully ✅")

    await state.set_state(Idle.just_idle)

    fake_call = type('obj', (object,), {
        'message': message,
        'data': f'admin_edit_product_{product_id}'
    })

    await edit_product(fake_call, state)

# endregion
