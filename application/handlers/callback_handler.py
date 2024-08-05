from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (CallbackQuery)
from aiogram.utils.keyboard import InlineKeyboardBuilder

import application.database_owm as database
import application.handlers.input_handler as input_handler
import application.handlers.output_handler as output
from application.handlers.display_handler import main_menu, products_catalog, companies_catalog

Form = input_handler.Form

router = Router()


@router.callback_query(lambda call: True)
async def process_callback(callback_query: CallbackQuery, state: FSMContext):
    data = callback_query.data
    user_id = callback_query.from_user.id
    message = callback_query.message

    match data:
        case _ if "answer" in data:
            await output.answer_message(callback_query, state)

        case _ if "ignore" in data:
            await output.ignore_message(callback_query)

        case _ if "companies" in data:
            if "initial" in data:
                await companies_catalog(callback_query, True)
            else:
                await companies_catalog(callback_query)

        case _ if "products" in data:
            if "initial" in data:
                await products_catalog(callback_query, True)
            else:
                await products_catalog(callback_query)

        case _ if "add-basket" in data:
            product_id = int(data.split('-')[0])
            message_text = await database.BasketObject.add_new(product_id, user_id)
            await message.answer(message_text)

        case _ if "add-wish" in data:
            product_id = int(data.split('-')[0])
            message_text = await database.WishObject.add_new(product_id, user_id)
            await message.answer(message_text)

        case "profile":
            await output.print_profile_info(callback_query.message, callback_query.from_user.id)

        case "orders":
            await output.print_orders_info(callback_query.message, callback_query.from_user.id)

        case "main menu":
            await message.delete()
            await main_menu(callback_query.message, callback_query.from_user.id)

        case "login":
            await message.delete()
            await state.set_state(Form.enter_login_password)
            await message.answer('Enter your username from Flavour Flow site')

        case "register":
            await message.delete()
            await state.set_state(Form.enter_email)
            await message.answer('Enter your username')

        case "help":
            if not database.PendingUser.is_pending(user_id):
                await message.answer('Enter your question')
                await state.set_state(Form.question)
            else:
                await message.answer('You have already sent a message, please wait an answer')

        case _ if "add product" in data:
            company_id = int(data.split('-')[0])
            await message.delete()
            markup = InlineKeyboardBuilder()
            markup.button(text='MEAL', callback_data=f'{company_id}-meal')
            markup.button(text='DRINK', callback_data=f'{company_id}-drink')
            markup.adjust(1, 1)
            await message.answer('Choose product category', reply_markup=markup.as_markup())

        case _ if "add company" in data:
            await message.delete()
            await output.image_question(callback_query.message)

        case _ if "meal" in data:
            company_id = int(data.split('-')[0])
            await message.delete()
            await output.image_question(callback_query.message, "MEAL", company_id)

        case _ if "drink" in data:
            company_id = int(data.split('-')[0])
            await message.delete()
            await output.image_question(callback_query.message, "DRINK", company_id)

        case _ if "dropbox" in data:
            try:
                product_category = data.split('-')[0]
                company_id = int(data.split('-')[1])
                values = {'type': 'PRODUCT', 'product_category': product_category, 'image_way': 'DROPBOX',
                          'company_id': company_id}
                await state.update_data(values=values)
                await state.set_state(Form.product_title)
                await input_handler.enter_product_title(callback_query.message, state)
            except ValueError:
                await output.choose_kitchen_category(callback_query.message, 'DROPBOX')

        case _ if "link" in data:
            try:
                company_id = int(data.split('-')[1])
                product_category = data.split('-')[0]
                values = {'type': 'PRODUCT', 'product_category': product_category, 'image_way': 'LINK',
                          'company_id': company_id}
                await state.update_data(values=values)
                await state.set_state(Form.product_title)
                await input_handler.enter_product_title(callback_query.message, state)
            except ValueError:
                await output.choose_kitchen_category(callback_query.message, 'LINK')

        case _ if "category" in data:
            category_id = int(data.split('-')[0])
            image_way = data.split('-')[1]
            await output.choose_company_country(callback_query.message, category_id, image_way)

        case _ if "country" in data:
            category_id = int(data.split('-')[0])
            country_id = int(data.split('-')[1])
            image_way = data.split('-')[2]
            await state.set_state(Form.company_title)
            await input_handler.enter_company_title(callback_query.message, category_id, country_id, image_way, state)

        case _ if "delete-product" in data:
            product_id = int(data.split('-')[0])
            await output.confirm_delete_product(callback_query.message, product_id)

        case _ if "delete-company" in data:
            company_id = int(data.split('-')[0])
            await output.confirm_delete_company(callback_query.message, company_id)

        case _ if "conf-del-prod" in data:
            product_id = int(data.split('-')[0])
            await output.delete_product(callback_query.message, state, product_id)

        case _ if "conf-del-comp" in data:
            company_id = int(data.split('-')[0])
            await output.delete_company(callback_query.message, state, company_id)

        case _ if "deny-delete" in data:
            await message.delete()
            await main_menu(callback_query.message, callback_query.from_user.id)


def register_callback_handlers(dp):
    dp.include_router(router)
