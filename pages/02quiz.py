import streamlit as st

# 접근 제어: 로그인되어 있지 않으면 접근 차단
if not st.session_state.get("logged_in"):
	st.warning("이 페이지는 로그인 후 이용 가능합니다. 로그인 페이지로 이동하세요.")
	st.stop()

# TODO: 퀴즈 로직 구현 - 질문 불러오기 -> 사용자 입력 수집 -> 정답 비교 및 점수 계산
