import pickle
from pathlib import Path

import streamlit_authenticator as stauth

names = ["Aldric", "Keidi", "Mr Heng"]
usernames = ["aldricc", "kkeidi", "Mheng"]
passwords = ["aldricc2", "kkeidi6", "Mheng8"]

hashed_passwords = stauth.Hasher(passwords).generate()

file_path = Path(__file__).parent / "hashed_pw.pkl"
with file_path.open("wb") as file:
    pickle.dump(hashed_passwords, file)
