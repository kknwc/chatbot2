import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from dotenv import load_dotenv
import os

load_dotenv()

config = {
    "credentials": {
        "usernames": {
            "user1": {
                "name": "aldricc",
                "password": stauth.Hasher(["password"]).generate()[0]
            },
            "user2": {
                "name": "kkeidi",
                "password": stauth.Hasher(["password"]).generate()[0]
            }
        }
    },
    "cookie": {
        "name": "my_app_auth",
        "key": os.getenv("SECRET_KEY", "a_random_secret_key"),
        "expiry_days": 30
    },
    "preauthorized": ["user1"]
}

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)
