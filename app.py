import streamlit as st
import json
import os
import re

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
    if 8 < len(password) < 20:
        return False, "비밀번호는 8-20자로 설정해주세요."
    if not any(char.isupper() for char in password):
        return False, "비밀번호에 대문자가 최소 1개 이상 포함되어야 합니다."
    special_char_pattern = re.compile(r'[^a-zA-Z0-9]')
    if not special_char_pattern.search(password):
        return False, "비밀번호에 특수문자가 최소 1개 이상 포함되어야 합니다."
    return True, "통과"

# --- 세션 상태 초기화 ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "page" not in st.session_state:
    st.session_state["page"] = "login"
if "error_msg" not in st.session_state:
    st.session_state["error_msg"] = ""

# --- 화면 로직 ---

# 1. 로그인 후 대시보드
if st.session_state["logged_in"]:
    st.title("🏡 Dashboard")
    st.write(f"**{st.session_state['user_id']}**님 환영합니다!")
    if st.button("로그아웃"):
        st.session_state["logged_in"] = False
        st.rerun()

# 2. 로그인 및 회원가입 화면
else:
    if st.session_state["page"] == "login":
        st.title("🔑 로그인")
        login_id = st.text_input("Email (ID)", placeholder="example@example.com")
        login_pw = st.text_input("Password", type="password", placeholder="비밀번호 입력 (최소 영문 대문자, 특수문자 하나 이상 포함한 8~20자)")
        
        col1, col2 = st.columns([0.2, 1])

        with col1:
            if st.button("로그인", use_container_width=True):
                users = load_users()
                if login_id in users and users[login_id] == login_pw:
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = login_id
                    st.session_state["error_msg"] = "" # 성공 시 에러 초기화
                    st.rerun()
                else:
                    st.session_state["error_msg"] = "정보가 일치하지 않습니다."
        
        with col2:
            if st.button("계정 생성"):
                st.session_state["page"] = "signup"
                st.session_state["error_msg"] = "" # 페이지 이동 시 에러 초기화
                st.rerun()

        # 에러 메시지를 컬럼 외부(전체 너비)에서 출력
        if st.session_state["error_msg"]:
            st.error(st.session_state["error_msg"])

    elif st.session_state["page"] == "signup":
        st.title("📝 회원가입")
        new_id = st.text_input("Email (ID)", placeholder="example@example.com")
        new_pw = st.text_input("Password", type="password" , placeholder="비밀번호 입력 (최소 영문 대문자, 특수문자 하나 이상 포함한 8~20자)")
        
        col_sub1, col_sub2 = st.columns([0.2, 1])
        
        with col_sub1:
            if st.button("가입하기", use_container_width=True):
                if not validate_email(new_id):
                    st.session_state["error_msg"] = "올바른 이메일 형식이 아닙니다. ('@' 포함 필수)"
                else:
                    is_valid_pw, message = validate_password(new_pw)
                    if not is_valid_pw:
                        st.session_state["error_msg"] = message
                    else:
                        if save_user(new_id, new_pw):
                            st.success("회원가입 성공!")
                            st.session_state["page"] = "login"
                            st.session_state["error_msg"] = ""
                            st.rerun()
                        else:
                            st.session_state["error_msg"] = "이미 존재하는 이메일입니다."
        
        with col_sub2:
            if st.button("취소"):
                st.session_state["page"] = "login"
                st.session_state["error_msg"] = ""
                st.rerun()

        # 회원가입 에러 메시지도 전체 너비로 출력
        if st.session_state["error_msg"]:
            st.error(st.session_state["error_msg"])