import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import io
import re

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 스타일 정의 (따뜻한 톤앤매너)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="동네별 인구 피라미드",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide"
)

st.markdown("""
    <style>
    .main {
        background-color: #faf9f6;
    }
    .stSelectbox label {
        font-weight: bold;
        color: #4a3b32;
    }
    </style>
""", unsafe_allow_html=True)

st.title("👨‍👩‍👧‍👦 우리 동네 인구 피라미드")
st.caption("전국 읍·면·동의 최신 연도 성별·연령별 인구 구조를 확인해 보세요.")

# -----------------------------------------------------------------------------
# 2. 데이터 불러오기 함수 (Git LFS Pointer 및 ZIP 압축 해제 안전 처리)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    raw_url = "https://raw.githubusercontent.com/kdoyun09/population/main/population_ts_yearly_gender.zip"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    res = requests.get(raw_url, headers=headers)
    content = res.content
    
    # Git LFS 포인터 파일인 경우 실제 파일 데이터를 가져옵니다.
    if b"version https://git-lfs.github.com" in content:
        text_content = content.decode("utf-8", errors="ignore")
        oid_match = re.search(r"oid sha256:([a-f0-9]+)", text_content)
        if oid_match:
            oid = oid_match.group(1)
            media_url = "https://media.githubusercontent.com/media/kdoyun09/population/main/population_ts_yearly_gender.zip"
            lfs_res = requests.get(media_url, headers=headers)
            if lfs_res.status_code == 200 and lfs_res.content.startswith(b"PK"):
                content = lfs_res.content
            else:
                lfs_download_url = f"https://github-cloud.s3.amazonaws.com/{oid}"
                lfs_res2 = requests.get(lfs_download_url, headers=headers)
                if lfs_res2.status_code == 200:
                    content = lfs_res2.content

    # 메모리 스트림을 이용하여 csv 로드
    df = pd.read_csv(io.BytesIO(content), compression="zip")
    
    # 가장 최신 연도 데이터만 추출
    max_year = int(df["연도"].max())
    latest_df = df[df["연도"] == max_year].copy()
    
    return latest_df, max_year

try:
    with st.spinner("인구 데이터를 불러오는 중입니다..."):
        df_latest, latest_year = load_data()
    st.sidebar.success(f"기준 연도: {latest_year}년 데이터 로드 완료")
except Exception as e:
    st.error(f"데이터 로드 오류: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 3. 사용자 선택 드롭다운 (시도 -> 시군구 -> 동)
# -----------------------------------------------------------------------------
st.subheader("📍 지역 선택")
col1, col2, col3 = st.columns(3)

with col1:
    sido_list = sorted(df_latest["시도"].dropna().unique())
    selected_sido = st.selectbox("시·도 선택", sido_list)

sigungu_filtered = df_latest[df_latest["시도"] == selected_sido]
sigungu_list = sorted(sigungu_filtered["시군구"].dropna().unique())

with col2:
    selected_sigungu = st.selectbox("시·군·구 선택", sigungu_list)

dong_filtered = sigungu_filtered[sigungu_filtered["시군구"] == selected_sigungu]
dong_list = sorted(dong_filtered["동"].dropna().unique())

with col3:
    selected_dong = st.selectbox("읍·면·동 선택", dong_list)

target_row = dong_filtered[dong_filtered["동"] == selected_dong]

if target_row.empty:
    st.warning("선택한 지역의 데이터가 없습니다.")
    st.stop()

target_data = target_row.iloc[0]

# -----------------------------------------------------------------------------
# 4. 나이 순서 정의 (0세부터 100세 이상까지) 및 남/여 인구 정리
# -----------------------------------------------------------------------------
age_categories = [f"{i}세" for i in range(101)]
age_categories[-1] = "100세 이상"

male_pop = []
female_pop
