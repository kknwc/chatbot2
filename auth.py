import streamlit as st
import streamlit_authenticator as stauth
import os

hashed_passwords = stauth.Hasher(["aldricc2", "kkeidi6", "heng8"]).generate()

config = {
    "credentials": {
        "usernames": {
            "user1": {
                "name": "aldricc",
                "password": stauth.Hasher(["password"]).generate()[0]
            },
            "user2": {
                "name": "kkeidi",
                "password": stauth.Hasher(["password"]).generate()[1]
            }
             "user3": {
                "name": "heng",
                "password": stauth.Hasher(["password"]).generate()[2]
            }
        }
    },
    
    "cookie": {
        "name": "my_app_auth",
        "key": "a_random_secret_key",
        "expiry_days": 30
    },
    "preauthorized": ["user1"]
}
