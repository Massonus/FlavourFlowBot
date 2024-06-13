import dropbox.files
import dropbox.exceptions
import main
from dropbox import DropboxOAuth2FlowNoRedirect
import config
import database_owm as database


def dbx_init_token(message, photo_bytes, bot, values):
    auth_flow = DropboxOAuth2FlowNoRedirect(config.APP_KEY, config.APP_SECRET)

    authorize_url = auth_flow.start()
    bot.send_message(message.chat.id, "Sorry, access token is invalid. Follow next steps below")
    bot.send_message(message.chat.id, "1. Go to: " + authorize_url)
    bot.send_message(message.chat.id, "2. Click \"Allow\" (you might have to log in first).")
    bot.send_message(message.chat.id, "3. Copy the authorization code.")
    bot.send_message(message.chat.id, "Enter the authorization code here: ")
    bot.register_next_step_handler(message, after_init_token, bot, auth_flow, photo_bytes, values)


def after_init_token(message, bot, auth_flow, photo_bytes, values):
    auth_code = message.text.strip()

    try:
        oauth_result = auth_flow.finish(auth_code)
    except Exception as e:
        bot.send_message(message.chat.id, f'Error: {e}')
        return False

    database.AccessToken.update_token(oauth_result.access_token)

    bot.send_message(message.chat.id, "Successfully set up client! Send your image again")
    bot.register_next_step_handler(message, upload_file, photo_bytes, bot, values)


def get_dbx(message, bot, values, photo_bytes=None):
    try:
        token = database.AccessToken.get_token().value
        dbx = dropbox.Dropbox(token)
        dbx.users_get_current_account()
        return dbx
    except (dropbox.exceptions.AuthError, AttributeError):
        dbx_init_token(message, photo_bytes, bot, values)


def upload_file(message, photo_bytes, bot, values):
    dbx = get_dbx(message, bot, values, photo_bytes)
    bot.send_message(message.chat.id, "Don't do anything and wait an answer")
    try:
        item_id = database.Company.get_max_id() + 1 if values.get(
            'type').upper() == 'COMPANY' else database.Product.get_max_id() + 1
        path = "/FlowImages/" + values.get('type').upper() + "/" + values.get('type') + str(item_id) + ".jpg"
        dbx.files_upload(photo_bytes, path)
        url = dbx.sharing_create_shared_link_with_settings(path).url.replace("www.dropbox.com",
                                                                             "dl.dropboxusercontent.com")
        values.update({'image_link': url})
        main.add_item_with_dropbox_link(message, values)
    except AttributeError:
        print("Waiting...")


def delete_file(message, bot, values):
    path = "/FlowImages/" + values.get('type').upper() + "/" + values.get('type') + values.get('id') + ".jpg"

    dbx = get_dbx(message, bot, values)
    try:
        dbx.files_delete_v2(path)
    except dropbox.exceptions.ApiError as error:
        bot.send_message(message.chat.id, f'Something is wrong {error}')
