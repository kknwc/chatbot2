import streamlit as st
import streamlit_authenticator as stauth
import os


config = {
    "credentials": {
        "usernames": {
            "user1": {
                "name": "aldricc",
                "password": "$2b$12$OucZZizy9c7Pbl3T0X5jUejiOoBOgj0lejEphO9BvghtENn1J2D5i"
            },
            "user2": {
                "name": "kkeidi",
                "password": "$2b$12$SpL6GpcyKRFiHcuJmmS.0eEUrBgr0GpUQbp5Ld7J414W2dV74y/1G"
            },
             "user3": {
                "name": "heng",
                "password": "$2b$12$cZaj/ph97W9HIOI66DXrCuasN7oGDN54R32fP9yOyU6u4FCVi21aO"
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
