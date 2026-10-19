import streamlit as st
import pandas as pd
import plotly.graph_objects as go

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
# 2. 데이터 불러오기 함수 (GitHub Raw URL에서 CSV 직접 로드)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/kdoyun09/population/main/population_ts_yearly_gender.csv"
    df = pd.read_csv(url)
    max_year = int(df['연도'].max())
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
# 4. 나이 순서 정의 (0세부터 100세 이상까지) 및 데이터 수집/지표 계산
# -----------------------------------------------------------------------------
age_categories = [f"{i}세" for i in range(101)]
age_categories[-1] = "100세 이상"

male_pop = []
female_pop = []
total_pop_by_age = []

total_pop = 0.0
weighted_age_sum = 0.0
elderly_pop = 0.0  # 65세 이상
youth_pop = 0.0    # 0~14세

for idx, age in enumerate(age_categories):
    m_col = f"남_{age}"
    f_col = f"여_{age}"
    
    m_val = float(target_data[m_col]) if m_col in target_data and pd.notnull(target_data[m_col]) else 0.0
    f_val = float(target_data[f_col]) if f_col in target_data and pd.notnull(target_data[f_col]) else 0.0
    
    male_pop.append(-m_val)
    female_pop.append(f_val)
    
    age_total = m_val + f_val
    total_pop_by_age.append(age_total)
    
    total_pop += age_total
    weighted_age_sum += age_total * idx  # 나이(idx) x 인구수
    
    if idx >= 65:
        elderly_pop += age_total
    if idx <= 14:
        youth_pop += age_total

# 지표 계산
avg_age = (weighted_age_sum / total_pop) if total_pop > 0 else 0.0
aging_rate = (elderly_pop / total_pop * 100) if total_pop > 0 else 0.0
youth_rate = (youth_pop / total_pop * 100) if total_pop > 0 else 0.0

# -----------------------------------------------------------------------------
# 5. 그래프 상단 지표 카드 3개 배치
# -----------------------------------------------------------------------------
st.markdown("---")
m_col1, m_col2, m_col3 = st.columns(3)

# 1) 총인구
m_col1.metric("👥 총인구", f"{int(total_pop):,} 명")

# 2) 평균연령
m_col2.metric("🎂 평균연령", f"{avg_age:.1f} 세")

# 3) 고령화율 (20% 초과 시 주의 경고 표기)
aging_label = "👵 고령화율 (65세+)"
if aging_rate >= 20.0:
    m_col3.metric(aging_label, f"{aging_rate:.1f} %", delta="🚨 초고령사회 (20% 이상)", delta_color="inverse")
else:
    m_col3.metric(aging_label, f"{aging_rate:.1f} %")

# -----------------------------------------------------------------------------
# 6. Plotly 인구 피라미드 가로 막대 그래프 그리기
# -----------------------------------------------------------------------------
fig = go.Figure()

# 남자 막대 (음수)
fig.add_trace(go.Bar(
    y=age_categories,
    x=male_pop,
    name='남성',
    orientation='h',
    marker=dict(color='#6c8ea4'),
    hovertemplate='<b>%{y}</b> 남성 인구: %{customdata:,}명<extra></extra>',
    customdata=[-int(val) for val in male_pop]
))

# 여자 막대 (양수)
fig.add_trace(go.Bar(
    y=age_categories,
    x=female_pop,
    name='여성',
    orientation='h',
    marker=dict(color='#e0896d'),
    hovertemplate='<b>%{y}</b> 여성 인구: %{x:,}명<extra></extra>'
))

max_val
