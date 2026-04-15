import streamlit as st

# 접근 제어: 로그인되어 있지 않으면 접근 차단
if not st.session_state.get("logged_in"):
	st.warning("이 페이지는 로그인 후 이용 가능합니다. 로그인 페이지로 이동하세요.")
	st.stop()

# TODO: 대시보드 로직 구현 - 사용자 통계 수집 -> 시각화(차트/테이블) 렌더링
