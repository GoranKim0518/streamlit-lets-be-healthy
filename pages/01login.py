import streamlit as st
import json
import os
import re

# [수정] 최상단에 배치하여 중앙 정렬 강제 설정
st.set_page_config(page_title="Be-Healthy 로그인", layout="centered")

# JSON DB 설정
DB_FILE = "users.json"
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

def load_users():
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_user(id, pw):
    users = load_users()
    if id in users:
        return False
    users[id] = pw
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)
    return True

# --- 유효성 검사 함수 ---
def validate_email(email):
    return "@" in email

def validate_password(password):
    if not isinstance(password, str) or password == "":
        return False, "비밀번호를 입력해주세요."

    length_ok = 8 <= len(password) <= 20
    upper_ok = any(char.isupper() for char in password)
    special_ok = bool(re.search(r'[^a-zA-Z0-9]', password))

    if length_ok and upper_ok and special_ok:
        return True, "통과"
    else:
        return False, "대문자, 특수문자가 하나 이상 포함된 8~20자의 패스워드를 생성해주세요."

# --- 세션 상태 초기화 ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "page" not in st.session_state:
    st.session_state["page"] = "login"
if "error_msg" not in st.session_state:
    st.session_state["error_msg"] = ""

# --- 화면 로직 ---

# 1. 로그인 후 화면
if st.session_state["logged_in"]:
    st.title("🔒 계정")
    st.write(f"**{st.session_state['user_id']}**님 환영합니다!")
    if st.button("로그아웃"):
        st.session_state["logged_in"] = False
        st.rerun()

# 2. 로그인 및 회원가입 화면
else:
    if st.session_state["page"] == "login":
        st.title("🔑 로그인")
        login_id = st.text_input("Email", placeholder="example@example.com", key="login_id")
        login_pw = st.text_input("Password", type="password", placeholder="비밀번호 입력", key="login_pw")
        
        # 버튼 배열 조정 (중앙 정렬 느낌을 위해 간격 조정)
        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("로그인", use_container_width=True):
                if login_id == "":
                    st.session_state["error_msg"] = "이메일을 입력해주세요."
                elif not validate_email(login_id):
                    st.session_state["error_msg"] = "올바른 이메일 형식이 아닙니다. ('@' 포함 필수)"
                elif login_pw == "":
                    st.session_state["error_msg"] = "비밀번호를 입력해주세요."
                else:
                    users = load_users()
                    if login_id in users and users[login_id] == login_pw:
                        st.session_state["logged_in"] = True
                        st.session_state["user_id"] = login_id
                        st.session_state["error_msg"] = ""
                        st.switch_page("pages/02quiz.py")
                    else:
                        st.session_state["error_msg"] = "이메일 또는 비밀번호가 일치하지 않습니다."
        
        with col2:
            if st.button("계정 생성", use_container_width=True):
                st.session_state["page"] = "signup"
                st.session_state["error_msg"] = ""
                st.rerun()

        if st.session_state["error_msg"]:
            st.error(st.session_state["error_msg"])

    elif st.session_state["page"] == "signup":
        st.title("📝 회원가입")
        new_id = st.text_input("Email", placeholder="example@example.com" , key="new_id")
        new_pw = st.text_input("Password", type="password", placeholder="대문자, 특수문자 포함 8~20자", key="new_pw")
        
        col_sub1, col_sub2 = st.columns([1, 1])
        
        with col_sub1:
            if st.button("가입하기", use_container_width=True):
                if new_id == "":
                    st.session_state["error_msg"] = "이메일을 입력해주세요."
                    st.rerun()
                elif not validate_email(new_id):
                    st.session_state["error_msg"] = "올바른 이메일 형식이 아닙니다. ('@' 포함 필수)"
                    st.rerun()
                else:
                    users = load_users()
                    if new_id in users:
                        st.session_state["error_msg"] = "이미 존재하는 이메일입니다."
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
            if st.button("취소", use_container_width=True):
                st.session_state["page"] = "login"
                st.session_state["error_msg"] = ""
                st.rerun()

        if st.session_state["error_msg"]:
            st.error(st.session_state["error_msg"])