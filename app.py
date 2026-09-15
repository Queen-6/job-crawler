import json
import os
import pandas as pd
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="해상풍력 채용 모니터링 대시보드",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_FILE = "jobs_data.json"

@st.cache_data(ttl=60)
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

jobs = load_data()
df = pd.DataFrame(jobs) if jobs else pd.DataFrame()

# 타이틀
st.title("🌊 해상풍력 & 하중해석 채용 모니터링")
st.caption("두산에너빌리티 · 한화오션 · 포스코인터내셔널 및 주요 채용 포털 실시간 수집")

if df.empty:
    st.warning("수집된 공고 데이터가 없습니다. collector.py를 먼저 실행해 주세요.")
    st.stop()

# 사이드바 필터링
st.sidebar.header("🔍 검색 및 필터")
keyword = st.sidebar.text_input("직무 / 기업명 / 기술스택 검색", placeholder="예: 하중, Bladed, 한화")

selected_sources = st.sidebar.multiselect(
    "수집 출처",
    options=df["source"].unique().tolist(),
    default=df["source"].unique().tolist()
)

# 데이터 필터링 적용
filtered_df = df[df["source"].isin(selected_sources)]

if keyword:
    query = keyword.lower()
    filtered_df = filtered_df[
        filtered_df["title"].str.lower().str.contains(query) |
        filtered_df["company"].str.lower().str.contains(query) |
        filtered_df["tech_stack"].str.lower().str.contains(query) |
        filtered_df["summary"].str.lower().str.contains(query)
    ]

# 상단 요약 메트릭
col1, col2, col3, col4 = st.columns(4)
col1.metric("총 수집 공고", f"{len(filtered_df)}건")
col2.metric("🎯 1순위 (하중해석)", f"{len(filtered_df[filtered_df['priority'].str.startswith('1순위')])}건")
col3.metric("🌬️ 2순위 (해상풍력)", f"{len(filtered_df[filtered_df['priority'].str.startswith('2순위')])}건")
col4.metric("🏢 3순위 (타깃기업)", f"{len(filtered_df[filtered_df['priority'].str.startswith('3순위')])}건")

st.divider()

# 우선순위별 탭 구성
tab_all, tab_p1, tab_p2, tab_p3 = st.tabs(["전체 보기", "🎯 1순위 (하중해석)", "🌬️ 2순위 (해상풍력)", "🏢 3순위 (타깃기업)"])

def render_job_cards(target_df):
    if target_df.empty:
        st.info("해당 조건의 공고가 없습니다.")
        return

    for _, row in target_df.iterrows():
        # 우선순위에 따른 배지 색상 구분
        badge_color = "red" if "1순위" in row['priority'] else ("orange" if "2순위" in row['priority'] else "blue")
        
        with st.container(border=True):
            sub_col1, sub_col2 = st.columns([4, 1])
            with sub_col1:
                st.markdown(f"### [{row['company']}] {row['title']}")
                st.markdown(f"**우선순위:** :{badge_color}[{row['priority']}] &nbsp;&nbsp;|&nbsp;&nbsp; **출처:** `{row['source']}` &nbsp;&nbsp;|&nbsp;&nbsp; **근무지:** {row['location']}")
                if row.get("summary"):
                    st.write(f"📝 {row['summary']}")
                if row.get("tech_stack"):
                    st.caption(f"🛠️ 관련 키워드: {row['tech_stack']}")
            with sub_col2:
                st.markdown(f"**마감일:** `{row['deadline']}`")
                st.link_button("공고 바로가기 ↗", row["url"], use_container_width=True)

with tab_all:
    render_job_cards(filtered_df)

with tab_p1:
    render_job_cards(filtered_df[filtered_df["priority"].str.startswith("1순위")])

with tab_p2:
    render_job_cards(filtered_df[filtered_df["priority"].str.startswith("2순위")])

with tab_p3:
    render_job_cards(filtered_df[filtered_df["priority"].str.startswith("3순위")])
