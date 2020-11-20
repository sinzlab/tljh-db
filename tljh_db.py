import os
import json

import pymysql
from xkcdpass import xkcd_password as xp

from tljh.hooks import hookimpl


@hookimpl
def tljh_new_user_create(username):
    password = generate_password()
    create_user(username, password)
    generate_datajoint_config(username, password)


def generate_password():
    wordfile = xp.locate_wordfile()
    words = xp.generate_wordlist(wordfile)
    return xp.generate_xkcdpassword(
        words, numwords=os.environ.get("TLJH_DB_NUMWORDS", 6), delimiter=os.environ.get("TLJH_DB_DELIMITER", "-")
    )


def create_user(username, password):
    connection = pymysql.connect(
        host=os.environ["TLJH_DB_HOST"], user=os.environ["TLJH_DB_USER"], password=os.environ["TLJH_DB_PASSWORD"]
    )
    try:
        with connection.cursor() as cursor:
            sql_statements = [
                fr"CREATE USER '{username}'@'%' IDENTIFIED BY '{password}'",
                fr"GRANT ALL PRIVILEGES ON `{username}\_%`.* TO '{username}'@'%'",
            ]
            for sql in sql_statements:
                cursor.execute(sql)
            connection.commit()
    finally:
        connection.close()


def generate_datajoint_config(username, password):
    dj_config_data = {
        "database.host": os.environ["TLJH_DB_HOST"],
        "database.password": password,
        "database.user": username,
        "database.port": os.environ.get("TLJH_DB_PORT", 3306),
        "database.reconnect": True,
        "connection.init_function": None,
        "connection.charset": "",
        "loglevel": "INFO",
        "safemode": True,
        "fetch_format": "array",
        "display.limit": 12,
        "display.width": 14,
        "display.show_tuple_count": True,
        "database.use_tls": None,
        "enable_python_native_blobs": False,
    }
    with open(os.path.join("/home", "jupyter-" + username, "dj_local_conf.json"), "w") as dj_config_file:
        json.dump(dj_config_data, dj_config_file, indent=True)
