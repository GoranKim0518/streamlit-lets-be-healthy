import streamlit as st

# 레이아웃을 중앙 정렬로 고정
st.set_page_config(layout="centered")

st.title("👨‍⚕️ Be-Healthy | 2021321022 이성민")
st.markdown("## 여러분의 건강 상태를 체크하세요!")
st.markdown("""> Be-Healthy는 단순히 건강 상태를 체크하는 데에서만 끝나지 않습니다.  
> 피드백을 통해 지속적으로 건강 상태를 개선할 수 있어요💪""")
st.markdown("***")

st.markdown("## 사용방법")
st.markdown("1. 로그인 후 quiz 탭에서 검사를 시작합니다.")
st.markdown("2. 검사를 모두 마친 후 dashboard 탭에서 결과를 확인합니다.")
st.markdown("")

# session_state 초기화
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# 로그인되어 있지 않을 때만 로그인 버튼 표시
if not st.session_state.get("logged_in"):
    if st.button('로그인해서 건강 관리 시작하기'):
        st.switch_page("pages/01login.py")
else:
    uid = st.session_state.get('user_id')
    st.success(f"{uid}님 환영합니다!")