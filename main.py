import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import urllib.request
import io

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 스타일 정의
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
# 2. 데이터 불러오기 함수 (Raw URL + User-Agent 헤더 적용)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # GitHub Raw 표준 URL
    url = "https://raw.githubusercontent.com/kdoyun09/population/main/population_ts_yearly_gender.zip"
    
    # 봇 차단 방지용 User-Agent 헤더 추가하여 바이너리 다운로드
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        zip_data = response.read()
    
    # BytesIO 메모리 스트림을 통해 판다스로 읽기
    df = pd.read_csv(io.BytesIO(zip_data), compression='zip')
    
    # 가장 최신 연도 데이터만 추출
    max_year = df['연도'].max()
    latest_df = df[df['연도'] == max_year].copy()
    
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
    sido_list = sorted(df_latest['시도'].dropna().unique())
    selected_sido = st.selectbox("시·도 선택", sido_list)

sigungu_filtered = df_latest[df_latest['시도'] == selected_sido]
sigungu_list = sorted(sigungu_filtered['시군구'].dropna().unique())

with col2:
    selected_sigungu = st.selectbox("시·군·구 선택", sigungu_list)

dong_filtered = sigungu_filtered[sigungu_filtered['시군구'] == selected_sigungu]
dong_list = sorted(dong_filtered['동'].dropna().unique())

with col3:
    selected_dong = st.selectbox("읍·면·동 선택", dong_list)

target_row = dong_filtered[dong_filtered['동'] == selected_dong]

if target_row.empty:
    st.warning("선택한 지역의 데이터가 없습니다.")
    st.stop()

target_data = target_row.iloc[0]

# -----------------------------------------------------------------------------
# 4. 나이 순서 정의 및 남/여 인구 데이터 정리
# -----------------------------------------------------------------------------
age_categories = [f"{i}세" for i in range(101)]
age_categories[-1] = "100세 이상"

male_pop = []
female_pop = []

for age in age_categories:
    m_col = f"남_{age}"
    f_col = f"여_{age}"
    
    m_val = target_data[m_col] if m_col in target_data else 0
    f_val = target_data[f_col] if f_col in target_data else 0
    
    male_pop.append(-m_val)
    female_pop.append(f_val)

# -----------------------------------------------------------------------------
# 5. Plotly 인구 피라미드 가로 막대 그래프 그리기
# -----------------------------------------------------------------------------
fig = go.Figure()

fig.add_trace(go.Bar(
    y=age_categories,
    x=male_pop,
    name='남성',
    orientation='h',
    marker=dict(color='#6c8ea4'),
    hovertemplate='<b>%{y}</b> 남성 인구: %{customdata:,}명<extra></extra>',
    customdata=[-val for val in male_pop]
))

fig.add_trace(go.Bar(
    y=age_categories,
    x=female_pop,
    name='여성',
    orientation='h',
    marker=dict(color='#e0896d'),
    hovertemplate='<b>%{y}</b> 여성 인구: %{x:,}명<extra></extra>'
))

max_val = max(max(abs(x) for x in male_pop), max(female_pop))
x_bound = max_val * 1.1 if max_val > 0 else 100

fig.update_layout(
    title=dict(
        text=f"<b>[{selected_sido} {selected_sigungu} {selected_dong}]</b> 인구 피라미드 ({latest_year}년)",
        font=dict(size=20, color="#4a3b32")
    ),
    barmode='relative',
    bargap=0.1,
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(245,243,238,0.5)',
    legend=dict(x=0.85, y=1.1, orientation="h", font=dict(size=13, color="#4a3b32")),
    xaxis=dict(
        title="인구수 (명)",
        range=[-x_bound, x_bound],
        tickvals=[-int(x_bound*0.8), -int(x_bound*0.4), 0, int(x_bound*0.4), int(x_bound*0.8)],
        ticktext=[f"{abs(int(x_bound*0.8)):,}", f"{abs(int(x_bound*0.4)):,}", "0", f"{int(x_bound*0.4):,}", f"{int(x_bound*0.8):,}"],
        gridcolor='#e0dcd3'
    ),
    yaxis=dict(
        title="연령",
        type='category',
        categoryorder='array',
        categoryarray=age_categories,
        dtick=10,
        gridcolor='#e0dcd3'
    ),
    height=750,
    margin=dict(l=60, r=60, t=80, b=50)
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# 6. 화면 출력 및 요약 통계
# -----------------------------------------------------------------------------
tot_male = sum(-val for val in male_pop)
tot_female = sum(female_pop)
tot_pop = tot_male + tot_female

m_col, f_col, t_col = st.columns(3)
m_col.metric("총 남성 인구", f"{tot_male:,} 명")
f_col.metric("총 여성 인구", f"{tot_female:,} 명")
t_col.metric("총 인구수", f"{tot_pop:,} 명")
