import streamlit as st
import json, os
import hashlib
import plotly.express as px
from pathlib import Path
from json import JSONDecodeError

st.set_page_config(page_title="Health Dashboard", layout="wide")

if not st.session_state.get("logged_in"):
    st.warning("이 페이지는 로그인 후 이용 가능합니다.")
    st.stop()

user_id = st.session_state["user_id"]
user_hash = hashlib.sha256(user_id.encode()).hexdigest()

st.title("🏥 건강관리 대시보드")
st.caption("※ 점수가 낮을수록 건강한 상태입니다.")

#quizdata.json은 앱 실행 중 변경되지 않기에 메모리에 유지
@st.cache_data(show_spinner=False)
def load_quiz_config(path="quizdata.json"):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        return cfg["questions"], {q["id"]: q for q in cfg["questions"]}, cfg["analysis_guide"]
    except (FileNotFoundError, JSONDecodeError) as e:
        st.error(f"질문을 불러올 수 없습니다: {e}")
        st.stop()

#mtime(수정시간)을 key로 사용하여 파일 변경시 자동으로 캐시 갱신
@st.cache_data(show_spinner=False)
def load_user_history(path, mtime):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, JSONDecodeError) as e:
        st.error(f"검사 기록을 읽지 못했습니다: {e}")
        st.stop()

questions, qmap, guide = load_quiz_config()
categories = guide["categories"]
user_path = Path(f"users/{user_hash}.json")

if not user_path.exists():
    st.info("📝 완료된 검사가 없습니다. 검사를 진행해주세요.")
    st.stop()

history = load_user_history(str(user_path), os.path.getmtime(user_path))
latest = history[-1]["raw_responses"]
prev = history[-2]["raw_responses"] if len(history) > 1 else None
is_first = (prev is None)

@st.cache_data(show_spinner=False)
def calculate_all_metrics(latest, prev, _qmap, _categories):
    #카테고리별 위험 점수 계산 및 정규화
    
    def compute_category_scores(responses):
        #응답 데이터로부터 카테고리별 가중치 적용 점수 계산
        weighted_scores = {}      # 카테고리별 가중치 적용 점수
        max_possible_scores = {}  # 카테고리별 최대 가능 점수
        
        for category, question_ids in _categories.items():
            category_weighted_sum = 0
            category_max_possible = 0
            
            for qid in question_ids:
                question = _qmap[qid]
                response_value = float(responses.get(str(qid), 0))
                
                # 문항 유형별 최댓값: yesno(0/1), likert(0~4)
                max_response = 1 if question["response_type"] == "yesno" else 4
                
                # 가중치 적용: 정신건강(2.5~3.0) > 활동량/수면(2.0) > 생활습관(1.5) > 식습관(1.0)
                category_weighted_sum += response_value * question["weight"]
                category_max_possible += max_response * question["weight"]
            
            weighted_scores[category] = category_weighted_sum
            max_possible_scores[category] = category_max_possible
        
        return weighted_scores, max_possible_scores

    # 현재 검사 점수 계산
    current_scores, max_possible = compute_category_scores(latest)
    total_max = sum(max_possible.values())
    
    # 전체 위험도 (0~100%)
    total_current_percent = sum(current_scores.values()) / total_max * 100
    
    # 카테고리별 정규화 (0~100%)
    normalized_current = {
        cat: current_scores[cat] / max_possible[cat] * 100 
        for cat in _categories
    }

    # 이전 검사 점수 계산 (있는 경우)
    total_prev_percent, normalized_prev = None, {}
    if prev:
        prev_scores, _ = compute_category_scores(prev)
        total_prev_percent = sum(prev_scores.values()) / total_max * 100
        normalized_prev = {
            cat: prev_scores[cat] / max_possible[cat] * 100 
            for cat in _categories
        }

    return total_current_percent, total_prev_percent, normalized_current, normalized_prev

total_curr, total_prev, norm_curr, norm_prev = calculate_all_metrics(latest, prev, qmap, categories)

#동일 데이터일 시 차트 새로 생성하기 방지
@st.cache_data(show_spinner=False)
def draw_bar_chart(norm_data):
    df = {"Category": list(norm_data.keys()), "Score": list(norm_data.values())}
    fig = px.bar(df, x="Score", y="Category", orientation="h", range_x=[0,100], text="Score",
                 color="Score", color_continuous_scale="RdYlGn_r", range_color=[0, 100])
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
    return fig

#동일 데이터일 시 차트 새로 생성하기 방지
@st.cache_data(show_spinner=False)
def draw_line_chart(norm_curr, norm_prev):
    df_line = []
    for cat in norm_curr.keys():
        df_line.append({"Category":cat, "Time":"이전", "Score":norm_prev[cat]})
        df_line.append({"Category":cat, "Time":"현재", "Score":norm_curr[cat]})
    fig = px.line(df_line, x="Category", y="Score", color="Time", markers=True)
    fig.update_layout(yaxis_range=[0,100], height=350)
    return fig

diff = (total_curr - total_prev) if total_prev is not None else 0

#점수 구간별 4단계 위험 등급 분류
def get_risk_info(score):
    if score <= 25: return "양호", "🟢"
    if score <= 50: return "주의", "🟡"
    if score <= 75: return "경계", "🟠"
    return "위험", "🔴"

def get_change_status(score_diff, is_first):
    STATUS_LABELS = {
        "baseline": "🆕 첫 측정",
        "improved": "✅ 개선",
        "stable":   "유지",
        "worsened": "⚠️ 악화",
    }
    if is_first:
        status_key = "baseline"
    elif score_diff <= -5:
        status_key = "improved"
    elif score_diff >= 5:
        status_key = "worsened"
    else:
        status_key = "stable"
    return STATUS_LABELS[status_key]

level, icon = get_risk_info(total_curr)
warning_triggered = (float(latest.get('14', 0)) >= 3)   #14번 문항에서 응답값 3 이상일 시 경고

with st.container():
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("현재 위험 점수", f"{total_curr:.1f}%",
              delta=f"{diff:.1f}%" if not is_first else None, delta_color="inverse")
    c2.metric("위험 등급", f"{icon} {level}")
    c3.metric("변화 상태", get_change_status(diff, is_first))
    c4.metric("위험 신호(14)", "🚨 감지" if warning_triggered else "✅ 정상")

st.markdown("---")

st.subheader("📊 카테고리별 위험 점수")
st.plotly_chart(draw_bar_chart(norm_curr), width="stretch", config={'displayModeBar': False})

if not is_first:
    st.subheader("📈 이전 대비 변화")

    #
    st.plotly_chart(draw_line_chart(norm_curr, norm_prev), width="stretch", config={'displayModeBar': False})

if warning_triggered:
    st.error("⚠️ 문항 14번에서 위험 응답이 감지되었습니다.")