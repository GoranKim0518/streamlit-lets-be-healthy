import streamlit as st
import json
import os
from datetime import datetime

# --- 1. 함수 정의 영역 ---

@st.cache_data
def load_quiz_data():
    with open('quizdata.json', 'r', encoding='utf-8') as f:
        return json.load(f)['questions']

def save_temp_progress(user_id, q_idx, responses):
    """퀴즈 진행 상황 중간 저장"""
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
    """임시 저장된 진행 상황 불러오기"""
    path = f'temp_users/{user_id}_temp.json'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def delete_temp_file(user_id):
    """임시 파일 삭제"""
    path = f'temp_users/{user_id}_temp.json'
    if os.path.exists(path):
        os.remove(path)

# save_raw_result
def save_raw_result(hash_val, responses):
    if not os.path.exists('users'): os.makedirs('users')
    path = f'users/{hash_val}.json'
    
    # 1. 기존 데이터 읽기
    history = json.load(open(path, 'r', encoding='utf-8')) if os.path.exists(path) else []
    
    # 2. 새로운 결과 추가
    history.append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
        "raw_responses": responses
    })
    
    # 3. 데이터가 2개보다 많으면 가장 오래된 것을 삭제 (항상 최신 2개 유지)
    if len(history) > 2:
        history = history[-2:]
        
    with open(path, 'w', encoding='utf-8') as f: 
        json.dump(history, f, ensure_ascii=False, indent=4)

# --- 2. 페이지 설정 및 접근 제어 ---

if not st.session_state.get("logged_in"):
    st.warning("이 페이지는 로그인 후 이용 가능합니다. 로그인 페이지로 이동하세요.")
    st.stop()

st.set_page_config(page_title="Be-Healthy 퀴즈", layout="centered")
st.sidebar.markdown("### 👤 제출자 정보")
st.sidebar.write("학번: 20XXXXXX")
st.sidebar.write("이름: 성민")

user_id = st.session_state.get("user_id")

# 새 검사 시작 버튼: 세션 초기화 + 임시 파일 삭제
if st.sidebar.button("🔄 새로운 검사 시작"):
    delete_temp_file(user_id)
    st.session_state.q_idx = 0
    st.session_state.temp_responses = {}
    st.rerun()

# --- 3. 퀴즈 상태 복구 로직 ---

questions = load_quiz_data()

# 세션에 인덱스가 없는 경우(페이지 처음 진입 시) 임시 저장본 확인
if 'q_idx' not in st.session_state:
    temp_data = load_temp_progress(user_id)
    if temp_data:
        st.session_state.q_idx = temp_data['q_idx']
        st.session_state.temp_responses = temp_data['temp_responses']
        st.sidebar.success("💡 이전 진행 상황을 불러왔습니다.")
    else:
        st.session_state.q_idx = 0
        st.session_state.temp_responses = {}

# --- 4. 퀴즈 UI ---

st.title("🏥 Be-Healthy 건강 체크")
st.write(f"안녕하세요 **{user_id}**님, 현재 상태를 솔직하게 답변해주세요.")

curr_idx = st.session_state.q_idx
progress_value = (curr_idx + 1) / len(questions)
st.progress(progress_value)
st.caption(f"전체 {len(questions)}문항 중 {curr_idx + 1}번째 진행 중")

q = questions[curr_idx]
st.markdown("---")
st.subheader(f"Q{curr_idx + 1}. {q['text']}")

# 기존 temp_responses에서 값을 가져옴 (기본값 "0")
current_val = str(st.session_state.temp_responses.get(str(q['id']), "0"))

if q['response_type'] == 'yesno':
    # 2지선다: 라디오 버튼
    options = ["0", "1"]
    labels = ["아니오", "네"]
    
    # 선택값 반영
    choice = st.radio(
        "선택하세요",
        options=options,
        format_func=lambda x: labels[int(x)],
        index=int(current_val),
        key=f"radio_{q['id']}"
    )
else:
    # 5지선다: 기존 슬라이더
    choice = str(st.select_slider(
        "정도를 선택하세요",
        options=["0", "1", "2", "3", "4"],
        value=current_val,
        format_func=lambda x: {"0":"전혀 아니다","1":"거의 아니다","2":"가끔","3":"자주","4":"항상"}[x],
        key=f"slider_{q['id']}"
    ))

# 세션에 즉시 반영
st.session_state.temp_responses[str(q['id'])] = choice

# 내비게이션 버튼
st.write("")
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if curr_idx > 0:
        if st.button("⬅️ 이전"):
            st.session_state.q_idx -= 1
            # 이전으로 갈 때도 현재 상태 저장
            save_temp_progress(user_id, st.session_state.q_idx, st.session_state.temp_responses)
            st.rerun()

with col3:
    if curr_idx < len(questions) - 1:
        if st.button("다음 ➡️"):
            st.session_state.q_idx += 1
            # 다음으로 갈 때 중간 저장 실행
            save_temp_progress(user_id, st.session_state.q_idx, st.session_state.temp_responses)
            st.rerun()
            
    if curr_idx == len(questions) - 1:
        if st.button("🎉 제출 및 분석"):
            # 최종 결과 저장
            save_raw_result(user_id, st.session_state.temp_responses)
            # 제출 완료 후 임시 파일 삭제
            delete_temp_file(user_id)
            
            st.success("데이터가 저장되었습니다!")
            # 상태 초기화
            st.session_state.q_idx = 0
            st.session_state.temp_responses = {}
            st.switch_page("pages/03dashboard.py")

st.markdown("---")
st.info("💡 중간에 브라우저를 닫거나 로그아웃해도 이어서 풀 수 있도록 저장됩니다.")