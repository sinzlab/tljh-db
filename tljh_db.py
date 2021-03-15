"""The littlest jupyterhub plugin for working with mysql databases."""
import configparser
import json
import os
from pwd import getpwnam

import pymysql
from tljh.hooks import hookimpl
from xkcdpass import xkcd_password as xp


@hookimpl
def tljh_new_user_create(username):
    config = read_config()
    password = generate_password(config)
    create_user(config, username, password)
    generate_datajoint_config(config, username, password)
    change_dj_config_file_permissions(username)


def read_config():
    config = configparser.ConfigParser()
    config.read("/srv/tljh-db.ini")
    return config


def generate_password(config):
    wordfile = xp.locate_wordfile()
    words = xp.generate_wordlist(wordfile)
    return xp.generate_xkcdpassword(
        words, numwords=config["DEFAULT"].get("NumWords", 6), delimiter=config["DEFAULT"].get("Delimiter", "-")
    )


def create_user(config, username, password):
    original_username = get_original_username(username)
    connection = pymysql.connect(
        host=config["DEFAULT"]["Host"], user=config["DEFAULT"]["User"], password=config["DEFAULT"]["Password"]
    )
    try:
        with connection.cursor() as cursor:
            sql_statements = [
                fr"CREATE USER '{original_username}'@'%' IDENTIFIED BY '{password}'",
                fr"GRANT ALL PRIVILEGES ON `{original_username}\_%`.* TO '{original_username}'@'%'",
            ]
            for sql in sql_statements:
                cursor.execute(sql)
            connection.commit()
    finally:
        connection.close()


def get_original_username(username):
    return username[8:]


def generate_datajoint_config(config, username, password):
    dj_config_data = {
        "database.host": config["DEFAULT"]["Host"],
        "database.password": password,
        "database.user": get_original_username(username),
        "database.port": config["DEFAULT"].get("Port", 3306),
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
    with open(get_dj_config_file_path(username), "w") as dj_config_file:
        json.dump(dj_config_data, dj_config_file, indent=True)


def get_dj_config_file_path(username):
    return os.path.join("/home", username, ".datajoint_config.json")


def change_dj_config_file_permissions(username):
    pw = getpwnam(username)
    os.chown(get_dj_config_file_path(username), pw.pw_uid, pw.pw_gid)
