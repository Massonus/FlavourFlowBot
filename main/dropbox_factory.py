import dropbox.files
import dropbox.exceptions
import pandas
import sqlalchemy
import main
from dropbox import DropboxOAuth2FlowNoRedirect
from config import APP_KEY, APP_SECRET, postgres_username, postgres_password

engine = sqlalchemy.create_engine(f"postgresql+psycopg2://{postgres_username}:{postgres_password}@localhost:5432/Test")


def dbx_init_token(message, photo_bytes, bot, values):
    auth_flow = DropboxOAuth2FlowNoRedirect(APP_KEY, APP_SECRET)

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

    data = pandas.read_sql('access_token', engine)
    index = data[data['id'] == 1].index
    data.loc[index, 'token'] = oauth_result.access_token
    data.to_sql('access_token', engine, if_exists='replace', index=False, index_label='id')

    bot.send_message(message.chat.id, "Successfully set up client! Send your image again")
    bot.register_next_step_handler(message, upload_file, photo_bytes, bot, values)


def get_dbx(message, photo_bytes, bot, values):
    token = pandas.read_sql('access_token', engine).at[0, "token"]

    try:
        dbx = dropbox.Dropbox(token)
        dbx.users_get_current_account()
        return dbx
    except dropbox.exceptions.AuthError:
        dbx_init_token(message, photo_bytes, bot, values)


def upload_file(message, photo_bytes, bot, values):
    dbx = get_dbx(message, photo_bytes, bot, values)
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
