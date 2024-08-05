import dropbox.exceptions
import dropbox.files
from aiogram import Bot
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from dropbox import DropboxOAuth2FlowNoRedirect

import application.config as config
import application.database_owm as database
import application.handlers.output_handler as output

router = Router()
bot = Bot(token=config.TG_TOKEN)


class Form(StatesGroup):
    after_init = State()


async def dbx_init_token(message: Message, photo_bytes: bytes, values: dict, state: FSMContext):
    auth_flow = DropboxOAuth2FlowNoRedirect(config.APP_KEY, config.APP_SECRET)

    authorize_url = auth_flow.start()
    await message.answer("Sorry, access token is invalid. Follow next steps below")
    await message.answer("1. Go to: " + authorize_url)
    await message.answer("2. Click \"Allow\" (you might have to log in first).")
    await message.answer("3. Copy the authorization code.")
    await message.answer("Enter the authorization code here:")
    await state.update_data(auth_flow=auth_flow, photo_bytes=photo_bytes, values=values)
    await state.set_state(Form.after_init)


@router.message(Form.after_init)
async def after_init_token(message: Message, state: FSMContext):
    await message.answer("Updating token...")
    data = await state.get_data()
    auth_flow = data['auth_flow']
    photo_bytes = data['photo_bytes']
    values = data.get('values')
    auth_code = message.text.strip()

    try:
        oauth_result = auth_flow.finish(auth_code)
    except Exception as e:
        await message.answer(f'Error: {e}')
        return

    await database.AccessToken.update_token(oauth_result.access_token)
    await message.answer("Successfully set up client!")

    if photo_bytes is None:
        await delete_file(message, state, values)
    else:
        await upload_file(message, photo_bytes, values, state)

    await state.clear()


async def get_dbx(message: Message, state: FSMContext, values, photo_bytes: bytes = None):
    try:
        token = database.AccessToken.get_token().value
        dbx = dropbox.Dropbox(token)
        dbx.users_get_current_account()
        return dbx
    except (dropbox.exceptions.AuthError, AttributeError):
        await dbx_init_token(message, photo_bytes, values, state)


async def upload_file(message: Message, photo_bytes: bytes, values: dict, state: FSMContext):
    dbx = await get_dbx(message, state, values, photo_bytes)
    try:
        dbx.users_get_current_account()
        await message.answer("Don't do anything and wait an answer")

        item_id = database.Company.get_max_id() + 1 if values.get(
            'type').upper() == 'COMPANY' else database.Product.get_max_id() + 1
        path = "/FlowImages/" + values.get('type').upper() + "/" + values.get('type') + str(item_id) + ".jpg"

        dbx.files_upload(photo_bytes, path)
        url = dbx.sharing_create_shared_link_with_settings(path).url.replace("www.dropbox.com",
                                                                             "dl.dropboxusercontent.com")
        values.update({'image_link': url})

        await output.add_item_with_dropbox_link(message, values)
    except (dropbox.exceptions.AuthError, AttributeError):
        print("Waiting...")
    except dropbox.exceptions.ApiError as error:
        await output.send_alarm(message.from_user.id, error)


async def delete_file(message: Message, state: FSMContext, values: dict):
    path = "/FlowImages/" + values.get('type').upper() + "/" + values.get('type') + values.get('id') + ".jpg"
    dbx = await get_dbx(message, state, values)

    try:
        dbx.files_delete_v2(path)
        if values.get('type').upper() == 'COMPANY':
            await database.Company.delete_directly(int(values.get('id')), message, state)
        else:
            await database.Product.delete_directly(int(values.get('id')), message)
    except AttributeError:
        print("Waiting oauth...")
    except dropbox.exceptions.ApiError as error:
        await message.answer(f'Something is wrong {error}')
        return False


def register_dropbox_factory(dp):
    dp.include_router(router)
