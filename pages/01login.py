import streamlit as st
import json
import os
import re
import hashlib

st.set_page_config(page_title="Be-Healthy 로그인", layout="centered")

DB_FILE = "users.json"
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

ERROR_MESSAGES = {
    "empty_email": "이메일을 입력해주세요.",
    "invalid_email": "올바른 이메일 형식이 아닙니다. ('@' 포함 필수)",
    "empty_password": "비밀번호를 입력해주세요.",
    "login_failed": "이메일 또는 비밀번호가 일치하지 않습니다.",
    "duplicate_email": "이미 존재하는 이메일입니다.",
    "invalid_password": "대문자, 특수문자가 하나 이상 포함된 8~20자의 패스워드를 생성해주세요.",
}

# SHA-256 단방향 해싱
def hash_value(value):
    return hashlib.sha256(value.encode()).hexdigest()

def load_users():
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_user(user_id, pw):
    users = load_users()
    hashed_id = hash_value(user_id)
    if hashed_id in users:
        return False
    users[hashed_id] = hash_value(pw)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)
    return True

def validate_email(email):
    return "@" in email

# 대문자, 특수문자 1개 이상인 8~20자 패스워드
def validate_password(password):
    if not isinstance(password, str) or password == "":
        return False, ERROR_MESSAGES["empty_password"]

    has_valid_length = 8 <= len(password) <= 20
    has_uppercase = any(char.isupper() for char in password)
    has_special_char = bool(re.search(r'[^a-zA-Z0-9]', password))

    if has_valid_length and has_uppercase and has_special_char:
        return True, "통과"
    else:
        return False, ERROR_MESSAGES["invalid_password"]

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "page" not in st.session_state:
    st.session_state["page"] = "login"
if "error_msg" not in st.session_state:
    st.session_state["error_msg"] = ""

if st.session_state["logged_in"]:
    st.title("🔒 계정")
    st.write(f"**{st.session_state['user_id']}**님 환영합니다!")
    if st.button("로그아웃"):
        st.session_state["logged_in"] = False
        st.rerun()

else:
    if st.session_state["page"] == "login":
        st.title("🔑 로그인")
        login_id = st.text_input("Email", placeholder="example@example.com", key="login_id")
        login_pw = st.text_input("Password", type="password", placeholder="비밀번호 입력", key="login_pw")

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("로그인", width="stretch"):
                if login_id == "":
                    st.session_state["error_msg"] = ERROR_MESSAGES["empty_email"]
                elif not validate_email(login_id):
                    st.session_state["error_msg"] = ERROR_MESSAGES["invalid_email"]
                elif login_pw == "":
                    st.session_state["error_msg"] = ERROR_MESSAGES["empty_password"]
                else:
                    users = load_users()
                    hashed_id = hash_value(login_id)
                    hashed_pw = hash_value(login_pw)
                    if hashed_id in users and users[hashed_id] == hashed_pw:
                        st.session_state["logged_in"] = True
                        st.session_state["user_id"] = login_id
                        st.session_state["user_hash"] = hash_value(login_id)
                        st.session_state["error_msg"] = ""
                        st.switch_page("pages/02quiz.py")
                    else:
                        st.session_state["error_msg"] = ERROR_MESSAGES["login_failed"]

        with col2:
            if st.button("계정 생성", width="stretch"):
                st.session_state["page"] = "signup"
                st.session_state["error_msg"] = ""
                st.rerun()

        if st.session_state["error_msg"]:
            st.error(st.session_state["error_msg"])

    elif st.session_state["page"] == "signup":
        st.title("📝 회원가입")
        new_id = st.text_input("Email", placeholder="example@example.com", key="new_id")
        new_pw = st.text_input("Password", type="password", placeholder="대문자, 특수문자 포함 8~20자", key="new_pw")

        col_sub1, col_sub2 = st.columns([1, 1])

        with col_sub1:
            if st.button("가입하기", width="stretch"):
                if new_id == "":
                    st.session_state["error_msg"] = ERROR_MESSAGES["empty_email"]
                    st.rerun()
                elif not validate_email(new_id):
                    st.session_state["error_msg"] = ERROR_MESSAGES["invalid_email"]
                    st.rerun()
                else:
                    users = load_users()
                    if hash_value(new_id) in users:
                        st.session_state["error_msg"] = ERROR_MESSAGES["duplicate_email"]
                        st.rerun()
                    else:
                        is_valid_pw, message = validate_password(new_pw)
                        if not is_valid_pw:
                            st.session_state["error_msg"] = message
                            st.rerun()
                        else:
                            if save_user(new_id, new_pw):
                                st.success("회원가입 성공!")
                                st.session_state["page"] = "login"
                                st.session_state["error_msg"] = ""
                                st.rerun()

        with col_sub2:
            if st.button("취소", width="stretch"):
                st.session_state["page"] = "login"
                st.session_state["error_msg"] = ""
                st.rerun()

        if st.session_state["error_msg"]:
            st.error(st.session_state["error_msg"])