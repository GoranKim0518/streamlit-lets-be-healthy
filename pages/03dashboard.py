import streamlit as st
import json, os
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Health Dashboard", layout="wide")

if not st.session_state.get("logged_in"):
    st.warning("로그인 후 이용 가능합니다.")
    st.stop()

user_id = st.session_state["user_id"]
st.title("🏥 건강관리 대시보드")
st.caption("※ 점수가 낮을수록 건강한 상태입니다.")

@st.cache_data(show_spinner=False)
def load_quiz_config(path="quizdata.json"):
    with open(path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    return cfg["questions"], {q["id"]: q for q in cfg["questions"]}, cfg["analysis_guide"]

@st.cache_data(show_spinner=False)
def load_user_history(path, mtime):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

questions, qmap, guide = load_quiz_config()
categories = guide["categories"]
user_path = Path(f"users/{user_id}.json")

if not user_path.exists():
    st.info("📝 완료된 검사가 없습니다. 퀴즈부터 완료해주세요.")
    st.stop()

history = load_user_history(str(user_path), os.path.getmtime(user_path))
latest = history[-1]["raw_responses"]
prev = history[-2]["raw_responses"] if len(history) > 1 else None
is_first = (prev is None)

@st.cache_data(show_spinner=False)
def calculate_all_metrics(latest, prev, _qmap, _categories):
    def compute(responses):
        raw = {}
        max_s = {}
        for cat, qids in _categories.items():
            s = 0
            m = 0
            for qid in qids:
                q = _qmap[qid]
                val = float(responses.get(str(qid), 0))
                cap = 1 if q["response_type"] == "yesno" else 4
                s += min(cap, max(0, val)) * q["weight"]
                m += cap * q["weight"]
            raw[cat] = s
            max_s[cat] = m
        return raw, max_s

    curr_raw, max_scores = compute(latest)
    total_max = sum(max_scores.values())
    total_curr = sum(curr_raw.values()) / total_max * 100
    norm_curr = {cat: curr_raw[cat]/max_scores[cat]*100 for cat in _categories}

    total_prev, norm_prev = None, {}
    if prev:
        prev_raw, _ = compute(prev)
        total_prev = sum(prev_raw.values()) / total_max * 100
        norm_prev = {cat: prev_raw[cat]/max_scores[cat]*100 for cat in _categories}

    return total_curr, total_prev, norm_curr, norm_prev

total_curr, total_prev, norm_curr, norm_prev = calculate_all_metrics(latest, prev, qmap, categories)

# cache_resource는 전역 단일 객체를 공유하므로 멀티 유저 환경에서
# 다른 유저의 차트가 반환될 수 있음 → 유저별 독립 캐시인 cache_data로 변경
@st.cache_data(show_spinner=False)
def draw_bar_chart(norm_data):
    df = {"Category": list(norm_data.keys()), "Score": list(norm_data.values())}
    fig = px.bar(df, x="Score", y="Category", orientation="h", range_x=[0,100], text="Score",
                 color="Score", color_continuous_scale="RdYlGn_r", range_color=[0, 100])
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
    return fig

# cache_resource는 전역 단일 객체를 공유하므로 멀티 유저 환경에서
# 다른 유저의 차트가 반환될 수 있음 → 유저별 독립 캐시인 cache_data로 변경
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
def get_risk_info(score):
    if score <= 25: return "양호","🟢"
    if score <= 50: return "주의","🟡"
    if score <= 75: return "경계","🟠"
    return "위험","🔴"
level, icon = get_risk_info(total_curr)
warning_triggered = (float(latest.get('14', 0)) >= 3)

with st.container():
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("현재 위험 점수", f"{total_curr:.1f}%",
              delta=f"{diff:.1f}%" if not is_first else None, delta_color="inverse")
    c2.metric("위험 등급", f"{icon} {level}")
    c3.metric("변화 상태", {
        "baseline":"🆕 첫 측정", "improved":"✅ 개선",
        "stable":"유지", "worsened":"⚠️ 악화"
    }["improved" if diff <= -5 else "worsened" if diff >= 5 else "baseline" if is_first else "stable"])
    c4.metric("위험 신호(14)", "🚨 감지" if warning_triggered else "✅ 정상")

st.markdown("---")

st.subheader("📊 카테고리별 위험 점수")
st.plotly_chart(draw_bar_chart(norm_curr), use_container_width=True, config={'displayModeBar': False})

if not is_first:
    st.subheader("📈 이전 대비 변화")
    st.plotly_chart(draw_line_chart(norm_curr, norm_prev), use_container_width=True, config={'displayModeBar': False})

if warning_triggered:
    st.error("⚠️ 문항 14번에서 위험 응답이 감지되었습니다.")