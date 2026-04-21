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
    # 기본 입력값 확인
    if not isinstance(password, str) or password == "":
        return False, "비밀번호를 입력해주세요."

    # 각 조건 체크
    length_ok = 8 <= len(password) <= 20
    upper_ok = any(char.isupper() for char in password)
    special_ok = bool(re.search(r'[^a-zA-Z0-9]', password))

    # 모든 조건이 True인지 확인
    if length_ok and upper_ok and special_ok:
        return True, "통과"
    else:
        # 하나라도 만족하지 못하면 공통 메시지 반환
        return False, "대문자, 특수문자가 하나 이상 포함된 8~20자의 패스워드를 생성해주세요."

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
        login_id = st.text_input("Email", placeholder="example@example.com")
        login_pw = st.text_input("Password", type="password", placeholder="비밀번호 입력 (대문자, 특수문자 하나 이상 포함한 8~20자)")
        
        col1, col2 = st.columns([0.2, 1])

        with col1:
            if st.button("로그인", use_container_width=True):
                users = load_users()
                if login_id in users and users[login_id] == login_pw:
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = login_id
                    st.session_state["error_msg"] = "" # 성공 시 에러 초기화
                    # 로그인 성공 시 퀴즈 페이지로 이동
                    st.switch_page("pages/02quiz.py")
                else:
                    st.session_state["error_msg"] = "정보가 일치하지 않습니다."
        
        with col2:
            if st.button("계정 생성"):
                st.session_state["page"] = "signup"
                st.session_state["error_msg"] = "" # 페이지 이동 시 에러 초기화
                st.rerun()

        # 에러 메시지 출력
        if st.session_state["error_msg"]:
            st.error(st.session_state["error_msg"])

    elif st.session_state["page"] == "signup":
        st.title("📝 회원가입")
        new_id = st.text_input("Email", placeholder="example@example.com")
        new_pw = st.text_input("Password", type="password" , placeholder="비밀번호 입력 (대문자, 특수문자 하나 이상 포함한 8~20자)")
        
        col_sub1, col_sub2 = st.columns([0.2, 1])
        
        with col_sub1:
            if st.button("가입하기", use_container_width=True):
                # 1) 이메일 형식 검사
                if not validate_email(new_id):
                    st.session_state["error_msg"] = "올바른 이메일 형식이 아닙니다. ('@' 포함 필수)"
                    st.rerun()

                # 2) 이미 존재하는 이메일인지 우선 검사 (이 경우 비밀번호 검증보다 우선)
                users = load_users()
                if new_id in users:
                    st.session_state["error_msg"] = "이미 존재하는 이메일입니다."
                    st.rerun()

                # 3) 비밀번호 검증
                is_valid_pw, message = validate_password(new_pw)
                if not is_valid_pw:
                    st.session_state["error_msg"] = message
                    st.rerun()

                # 4) 사용자 저장
                if save_user(new_id, new_pw):
                    st.success("회원가입 성공!")
                    st.session_state["page"] = "login"
                    st.session_state["error_msg"] = ""
                    st.rerun()
        
        with col_sub2:
            if st.button("취소"):
                st.session_state["page"] = "login"
                st.session_state["error_msg"] = ""
                st.rerun()

        # 회원가입 에러 메시지 출력
        if st.session_state["error_msg"]:
            st.error(st.session_state["error_msg"])