import dropbox.files
import dropbox.exceptions
import pandas
import sqlalchemy
from dropbox import DropboxOAuth2FlowNoRedirect
from config import APP_KEY, APP_SECRET, postgres_username, postgres_password

engine = sqlalchemy.create_engine(f"postgresql+psycopg2://{postgres_username}:{postgres_password}@localhost:5432/Test")


def dbx_init_token():
    auth_flow = DropboxOAuth2FlowNoRedirect(APP_KEY, APP_SECRET)

    authorize_url = auth_flow.start()
    print("1. Go to: " + authorize_url)
    print("2. Click \"Allow\" (you might have to log in first).")
    print("3. Copy the authorization code.")
    auth_code = input("Enter the authorization code here: ").strip()

    try:
        oauth_result = auth_flow.finish(auth_code)
    except Exception as e:
        print('Error: %s' % (e,))
        exit(1)

    data = pandas.read_sql('access_token', engine)
    index = data[data['id'] == 1].index
    data.loc[index, 'token'] = oauth_result.access_token
    data.to_sql('access_token', engine, if_exists='replace', index=False, index_label='id')
    with dropbox.Dropbox(oauth2_access_token=oauth_result.access_token) as dbx:
        dbx.users_get_current_account()
        print("Successfully set up client!")
        return dbx


def get_dbx():
    token = pandas.read_sql('access_token', engine).at[0, "token"]

    try:
        dbx = dropbox.Dropbox(token)
        dbx.users_get_current_account()
    except dropbox.exceptions.AuthError as e:
        return dbx_init_token()
    else:
        return dbx


def upload_file(photo_bytes):
    dbx = get_dbx()
    dbx.files_upload(photo_bytes, "/test.jpg")
