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

# 커스텀 CSS (따뜻한 배경 느낌 및 폰트 설정)
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
# 2. 데이터 불러오기 함수 (캐싱 적용으로 속도 향상)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # github raw URL 사용 (zip 파일 직접 판다스로 읽기)
    url = "https://raw.githubusercontent.com/kdoyun09/population/main/population_ts_yearly_gender.zip"
    df = pd.read_csv(url, compression='zip')
    
    # 가장 최신 연도 데이터만 추출
    max_year = df['연도'].max()
    latest_df = df[df['연도'] == max_year].copy()
    
    return latest_df, max_year

try:
    with st.spinner("인구 데이터를 불러오는 중입니다..."):
        df_latest, latest_year = load_data()
    st.sidebar.success(f"기준 연도: {latest_year}년 데이터 로드 완료")
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 3. 사용자 선택 드롭다운 (시도 -> 시군구 -> 동)
# -----------------------------------------------------------------------------
st.subheader("📍 지역 선택")
col1, col2, col3 = st.columns(3)

with col1:
    sido_list = sorted(df_latest['시도'].dropna().unique())
    selected_sido = st.selectbox("시·도 선택", sido_list)

# 선택된 시도에 맞는 시군구 목록 필터링
sigungu_filtered = df_latest[df_latest['시도'] == selected_sido]
sigungu_list = sorted(sigungu_filtered['시군구'].dropna().unique())

with col2:
    selected_sigungu = st.selectbox("시·군·구 선택", sigungu_list)

# 선택된 시군구에 맞는 동 목록 필터링
dong_filtered = sigungu_filtered[sigungu_filtered['시군구'] == selected_sigungu]
dong_list = sorted(dong_filtered['동'].dropna().unique())

with col3:
    selected_dong = st.selectbox("읍·면·동 선택", dong_list)

# 최종 선택된 1개 행 추출
target_row = dong_filtered[dong_filtered['동'] == selected_dong]

if target_row.empty:
    st.warning("선택한 지역의 데이터가 없습니다.")
    st.stop()

target_data = target_row.iloc[0]

# -----------------------------------------------------------------------------
# 4. 나이 순서 정의 및 남/여 인구 데이터 정리
# -----------------------------------------------------------------------------
# 0세부터 100세 이상까지 연령대 라벨 리스트 생성
age_categories = [f"{i}세" for i in range(101)]
age_categories[-1] = "100세 이상"  # 마지막 항목 수정

male_pop = []
female_pop = []

# 열 이름에 맞춰 데이터 추출 (남자는 피라미드 좌측 배치를 위해 음수로 변환)
for age in age_categories:
    m_col = f"남_{age}"
    f_col = f"여_{age}"
    
    m_val = target_data[m_col] if m_col in target_data else 0
    f_val = target_data[f_col] if f_col in target_data else 0
    
    male_pop.append(-m_val)  # 음수
    female_pop.append(f_val) # 양수

# -----------------------------------------------------------------------------
# 5. Plotly 인구 피라미드 가로 막대 그래프 그리기
# -----------------------------------------------------------------------------
fig = go.Figure()

# 남자 막대 그래프 (왼쪽, 음수 값)
fig.add_trace(go.Bar(
    y=age_categories,
    x=male_pop,
    name='남성',
    orientation='h',
    marker=dict(color='#6c8ea4'),  # 따뜻하고 차분한 블루톤
    hovertemplate='<b>%{y}</b> 남성 인구: %{customdata:,}명<extra></extra>',
    customdata=[-val for val in male_pop]  # 마우스 호버 시 양수로 표기
))

# 여자 막대 그래프 (오른쪽, 양수 값)
fig.add_trace(go.Bar(
    y=age_categories,
    x=female_pop,
    name='여성',
    orientation='h',
    marker=dict(color='#e0896d'),  # 따뜻하고 차분한 랄라/코랄톤
    hovertemplate='<b>%{y}</b> 여성 인구: %{x:,}명<extra></extra>'
))

# 최대 인구수 계산 (x축 대칭 범위를 위해)
max_val = max(max(abs(x) for x in male_pop), max(female_pop))
x_bound = max_val * 1.1 if max_val > 0 else 100

# 그래프 레이아웃 및 축 설정
fig.update_layout(
    title=dict(
        text=f"<b>[{selected_sido} {selected_sigungu} {selected_dong}]</b> 인구 피라미드 ({latest_year}년)",
        font=dict(size=20, color="#4a3b32")
    ),
    barmode='relative',
    bargap=0.1,
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(245,243,238,0.5)',
    legend=dict(
        x=0.85, y=1.1,
        orientation="h",
        font=dict(size=13, color="#4a3b32")
    ),
    xaxis=dict(
        title="인구수 (명)",
        range=[-x_bound, x_bound],
        # x축 눈금에 음수 기호 제거하고 절대값으로 표시
        tickvals=[-int(x_bound*0.8), -int(x_bound*0.4), 0, int(x_bound*0.4), int(x_bound*0.8)],
        ticktext=[f"{abs(int(x_bound*0.8)):,}", f"{abs(int(x_bound*0.4)):,}", "0", f"{int(x_bound*0.4):,}", f"{int(x_bound*0.8):,}"],
        gridcolor='#e0dcd3'
    ),
    # 세로축 고정 설정 (0세가 맨 아래, 100세 이상이 맨 위)
    yaxis=dict(
        title="연령",
        type='category',
        categoryorder='array',
        categoryarray=age_categories,  # 순서 직접 주입
        dtick=10,  # 10세 단위로 눈금 표시
        gridcolor='#e0dcd3'
    ),
    height=750,
    margin=dict(l=60, r=60, t=80, b=50)
)

# -----------------------------------------------------------------------------
# 6. 화면 출력 및 요약 통계
# -----------------------------------------------------------------------------
st.plotly_chart(fig, use_container_width=True)

# 주요 인구 통계 요약 카드
tot_male = sum(-val for val in male_pop)
tot_female = sum(female_pop)
tot_pop = tot_male + tot_female

m_col, f_col, t_col = st.columns(3)
m_col.metric("총 남성 인구", f"{tot_male:,} 명")
f_col.metric("총 여성 인구", f"{tot_female:,} 명")
t_col.metric("총 인구수", f"{tot_pop:,} 명")
