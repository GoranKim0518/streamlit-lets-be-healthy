import streamlit as st
import json
import os
from datetime import datetime

st.set_page_config(page_title="Be-Healthy 퀴즈", layout="centered")

@st.cache_data
def load_quiz_data():
    with open('quizdata.json', 'r', encoding='utf-8') as f:
        return json.load(f)['questions']

def save_temp_progress(user_id, q_idx, responses):
    if not os.path.exists('temp_users'):
        os.makedirs('temp_users')
    temp_data = {
        "q_idx": q_idx,
        "temp_responses": responses,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(f'temp_users/{user_id}_temp.json', 'w', encoding='utf-8') as f:
        json.dump(temp_data, f, ensure_ascii=False, indent=4)

def load_temp_progress(user_id):
    path = f'temp_users/{user_id}_temp.json'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def delete_temp_file(user_id):
    path = f'temp_users/{user_id}_temp.json'
    if os.path.exists(path):
        os.remove(path)

def save_raw_result(hash_val, responses):
    if not os.path.exists('users'):
        os.makedirs('users')
    path = f'users/{hash_val}.json'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = []
    history.append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "raw_responses": responses
    })
    if len(history) > 2:
        history = history[-2:]
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

if not st.session_state.get("logged_in"):
    st.warning("이 페이지는 로그인 후 이용 가능합니다. 로그인 페이지로 이동하세요.")
    st.stop()

user_id = st.session_state.get("user_id")

questions = load_quiz_data()

if 'q_idx' not in st.session_state:
    temp_data = load_temp_progress(user_id)
    if temp_data:
        st.session_state.q_idx = temp_data['q_idx']
        st.session_state.temp_responses = temp_data['temp_responses']
        st.success("💡이전 진행 상황을 불러왔습니다.")
    else:
        st.session_state.q_idx = 0
        st.session_state.temp_responses = {}

st.title("🏥 Be-Healthy 건강 체크")
st.write(f"안녕하세요 **{user_id}**님, 현재 상태를 솔직하게 답변해주세요.")

curr_idx = st.session_state.q_idx
progress_value = (curr_idx + 1) / len(questions)
st.progress(progress_value)
st.caption(f"전체 {len(questions)}문항 중 {curr_idx + 1}번째 진행 중")

q = questions[curr_idx]
st.markdown("---")
st.subheader(f"Q{curr_idx + 1}. {q['text']}")

if q['response_type'] == 'yesno':
    options = ["1", "0"]
    labels = {"1": "네", "0": "아니오"}
    choice = st.radio(
        "선택하세요",
        options=options,
        format_func=lambda x: labels[x],
        index=0,
        key=f"radio_{q['id']}"
    )
else:
    choice = str(st.select_slider(
        "정도를 선택하세요",
        options=["0", "1", "2", "3", "4"],
        value="2",
        format_func=lambda x: {"0":"전혀 아니다","1":"거의 아니다","2":"가끔","3":"자주","4":"항상"}[x],
        key=f"slider_{q['id']}"
    ))

st.session_state.temp_responses[str(q['id'])] = choice

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if curr_idx > 0:
        if st.button("⬅️ 이전"):
            st.session_state.q_idx -= 1
            save_temp_progress(user_id, st.session_state.q_idx, st.session_state.temp_responses)
            st.rerun()

with col3:
    if curr_idx < len(questions) - 1:
        if st.button("다음 ➡️"):
            st.session_state.q_idx += 1
            save_temp_progress(user_id, st.session_state.q_idx, st.session_state.temp_responses)
            st.rerun()

    if curr_idx == len(questions) - 1:
        if st.button("📊 제출 및 분석"):
            save_raw_result(user_id, st.session_state.temp_responses)
            delete_temp_file(user_id)
            st.success("데이터가 저장되었습니다!")
            st.session_state.q_idx = 0
            st.session_state.temp_responses = {}
            st.switch_page("pages/03dashboard.py")