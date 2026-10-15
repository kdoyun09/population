# population
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="동네별 인구 피라미드", layout="wide")

st.title("👨‍👩‍👧‍👦 우리 동네 인구 피라미드")

@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/kdoyun09/population/main/population_ts_yearly_gender.zip"
    df = pd.read_csv(url, compression='zip')
    max_year = df['연도'].max()
    return df[df['연도'] == max_year].copy(), max_year

try:
    df_latest, latest_year = load_data()
    st.sidebar.success(f"기준 연도: {latest_year}년")
except Exception as e:
    st.error(f"데이터 로드 오류: {e}")
    st.stop()

st.subheader("📍 지역 선택")
col1, col2, col3 = st.columns(3)

with col1:
    sido_list = sorted(df_latest['시도'].dropna().unique())
    selected_sido = st.selectbox("시·도", sido_list)

sigungu_filtered = df_latest[df_latest['시도'] == selected_sido]
with col2:
    sigungu_list = sorted(sigungu_filtered['시군구'].dropna().unique())
    selected_sigungu = st.selectbox("시·군·구", sigungu_list)

dong_filtered = sigungu_filtered[sigungu_filtered['시군구'] == selected_sigungu]
with col3:
    dong_list = sorted(dong_filtered['동'].dropna().unique())
    selected_dong = st.selectbox("읍·면·동", dong_list)

target_row = dong_filtered[dong_filtered['동'] == selected_dong]

if not target_row.empty:
    target_data = target_row.iloc[0]
    
    age_categories = [f"{i}세" for i in range(101)]
    age_categories[-1] = "100세 이상"

    male_pop = [-target_data.get(f"남_{age}", 0) for age in age_categories]
    female_pop = [target_data.get(f"여_{age}", 0) for age in age_categories]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=age_categories, x=male_pop, name='남성', orientation='h',
        marker=dict(color='#6c8ea4'), customdata=[-val for val in male_pop],
        hovertemplate='%{y} 남성: %{customdata:,}명<extra></extra>'
    ))

    fig.add_trace(go.Bar(
        y=age_categories, x=female_pop, name='여성', orientation='h',
        marker=dict(color='#e0896d'),
        hovertemplate='%{y} 여성: %{x:,}명<extra></extra>'
    ))

    max_val = max(max(abs(x) for x in male_pop), max(female_pop), 10)
    x_bound = max_val * 1.1

    fig.update_layout(
        title=f"<b>[{selected_sido} {selected_sigungu} {selected_dong}]</b> 인구 피라미드 ({latest_year}년)",
        barmode='relative',
        bargap=0.1,
        xaxis=dict(
            range=[-x_bound, x_bound],
            tickvals=[-int(x_bound*0.8), 0, int(x_bound*0.8)],
            ticktext=[f"{abs(int(x_bound*0.8)):,}", "0", f"{int(x_bound*0.8):,}"]
        ),
        yaxis=dict(type='category', categoryorder='array', categoryarray=age_categories, dtick=10),
        height=700
    )

    st.plotly_chart(fig, use_container_width=True)
