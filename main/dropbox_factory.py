import dropbox.files
import dropbox.exceptions
import pandas
import sqlalchemy
import main
from dropbox import DropboxOAuth2FlowNoRedirect
import config
from database_factory import PaginationData

engine = sqlalchemy.create_engine(
    f"postgresql+psycopg2://{config.postgres_username}:{config.postgres_test_password}@{config.postgres_test_host}:5432"
    f"/{config.postgres_test_database}")

# engine = sqlalchemy.create_engine(
#     f"postgresql+psycopg2://{config.postgres_username}:{config.postgres_password}@{config.postgres_host}:5432"
#     f"/{config.postgres_database}")


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

    sql = (f"UPDATE public.access_token "
           f"SET value='{oauth_result.access_token}' "
           f"WHERE id>0 ")

    db = PaginationData()
    db.cursor.execute(sql)
    db.conn.commit()

    bot.send_message(message.chat.id, "Successfully set up client! Send your image again")
    bot.register_next_step_handler(message, upload_file, photo_bytes, bot, values)


def get_dbx(message, bot, values, photo_bytes=None):
    token = pandas.read_sql('access_token', engine).at[0, "value"]

    try:
        dbx = dropbox.Dropbox(token)
        dbx.users_get_current_account()
        return dbx
    except dropbox.exceptions.AuthError:
        dbx_init_token(message, photo_bytes, bot, values)


def upload_file(message, photo_bytes, bot, values):
    dbx = get_dbx(message, bot, values, photo_bytes)
    try:
        data = pandas.read_sql(values.get('type').lower(), engine)
        path = "/FlowImages/" + values.get('type').upper() + "/" + values.get('type') + str(max(
            data['id'].values + 1)) + ".jpg"

        bot.send_message(message.chat.id, "Don't do anything and wait an answer")

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
