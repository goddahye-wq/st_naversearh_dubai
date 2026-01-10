import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime
from dotenv import load_dotenv

# 페이지 설정
st.set_page_config(page_title="Naver API Trend Dashboard", layout="wide")

# 스타일링
st.markdown("""
<style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .reportview-container .main .block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# API 키 로드 로직 (Streamlit Secrets 우선, 이후 환경변수)
def get_api_keys():
    try:
        if "NAVER_CLIENT_ID" in st.secrets:
            return st.secrets["NAVER_CLIENT_ID"], st.secrets["NAVER_CLIENT_SECRET"]
    except:
        pass
    
    load_dotenv()
    return os.getenv("NAVER_CLIENT_ID"), os.getenv("NAVER_CLIENT_SECRET")

CLIENT_ID, CLIENT_SECRET = get_api_keys()

# 데이터 로드 함수
@st.cache_data
def load_data():
    raw_path = "raw_data/"
    if not os.path.exists(raw_path):
        os.makedirs(raw_path)
    
    files = [f for f in os.listdir(raw_path) if f.endswith('.csv')]
    if not files:
        return None, None, None
    
    # 트렌드, 블로그, 쇼핑 파일 자동 감지
    trend_files = sorted([f for f in files if "search_trend" in f])
    blog_files = sorted([f for f in files if "blog_latest" in f])
    shop_files = sorted([f for f in files if "shop_latest" in f])
    
    if not (trend_files and blog_files and shop_files):
        return None, None, None

    df_trend = pd.read_csv(os.path.join(raw_path, trend_files[-1]))
    df_blog = pd.read_csv(os.path.join(raw_path, blog_files[-1]))
    df_shop = pd.read_csv(os.path.join(raw_path, shop_files[-1]))
    
    # 전처리
    df_trend['date'] = pd.to_datetime(df_trend['date'])
    df_shop['lprice'] = pd.to_numeric(df_shop['lprice'], errors='coerce')
    
    return df_trend, df_blog, df_shop

df_trend, df_blog, df_shop = load_data()

if df_trend is None:
    st.warning("⚠️ raw_data 폴더에 수집된 CSV 파일이 없습니다. 데이터를 먼저 수집해 주세요.")
    st.stop()

# 사이드바 구성
st.sidebar.title("🔍 검색 옵션")
keywords = df_trend['keyword_group'].unique().tolist()
selected_keywords = st.sidebar.multiselect("분석 키워드 선택", keywords, default=keywords)

st.sidebar.markdown("---")
st.sidebar.info("이 대시보드는 Naver API를 통해 수집된 데이터를 분석합니다.")

# 메인 헤더
st.title("🍫 두바이 쿠키 & 초콜릿 트렌드 분석")
st.markdown(f"**기준일**: {datetime.now().strftime('%Y-%m-%d')}")

# 데이터 필터링
df_trend_filtered = df_trend[df_trend['keyword_group'].isin(selected_keywords)]
df_blog_filtered = df_blog[df_blog['keyword'].isin(selected_keywords)]
df_shop_filtered = df_shop[df_shop['keyword'].isin(selected_keywords)]

# 탭 구성
tab1, tab2, tab3, tab4 = st.tabs(["📈 트렌드 비교", "🛒 쇼핑 EDA (심화)", "📝 블로그 인사이트", "📊 데이터 원본"])

# Tab 1: 트렌드 분석
with tab1:
    st.header("2025년 검색 트렌드 분석")
    fig_line = px.line(df_trend_filtered, x='date', y='ratio', color='keyword_group',
                      title="2025년 검색 추이 (Plotly Line)", labels={'ratio': '비중'}, template="plotly_white")
    st.plotly_chart(fig_line, use_container_width=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("키워드 요약 통계")
        summary = df_trend_filtered.groupby('keyword_group')['ratio'].agg(['mean', 'max']).reset_index()
        st.table(summary.style.format({'mean': '{:.2f}', 'max': '{:.2f}'}))
    with c2:
        df_trend_filtered['month'] = df_trend_filtered['date'].dt.strftime('%m')
        monthly = df_trend_filtered.groupby(['month', 'keyword_group'])['ratio'].mean().reset_index()
        fig_bar = px.bar(monthly, x='month', y='ratio', color='keyword_group', barmode='group', title="월별 평균 트렌드")
        st.plotly_chart(fig_bar, use_container_width=True)

# Tab 2: 쇼핑 EDA
with tab2:
    st.header("쇼핑 데이터 심화 분석 (EDA)")
    
    # 1. 결측치 시각화
    st.subheader("1. 결측치 현황")
    missing = df_shop_filtered.isnull().sum()
    df_missing = pd.DataFrame({'Column': missing.index, 'Count': missing.values})
    df_missing = df_missing[df_missing['Count'] > 0]
    
    if not df_missing.empty:
        fig_miss = px.bar(df_missing, x='Column', y='Count', title="결측치 발생 컬럼 목록", color_discrete_sequence=['red'])
        st.plotly_chart(fig_miss, use_container_width=True)
    else:
        st.success("결측치가 발견되지 않았습니다.")

    # 2. 박스플롯 (이상치)
    st.subheader("2. 가격 이상치 분석 (Boxplot)")
    fig_box = px.box(df_shop_filtered, x='keyword', y='lprice', color='keyword', points="all", title="가격 분포 및 이상치")
    st.plotly_chart(fig_box, use_container_width=True)

    # 3. 히트맵 (상관관계)
    st.subheader("3. 상관관계 분석 (Heatmap)")
    df_shop_filtered['title_len'] = df_shop_filtered['title'].str.len()
    corr = df_shop_filtered[['lprice', 'title_len']].corr()
    fig_heat = px.imshow(corr, text_auto=True, title="가격 vs 제목 길이 상관관계")
    st.plotly_chart(fig_heat, use_container_width=True)

    # 4. 피벗 테이블 (2개)
    ct1, ct2 = st.columns(2)
    with ct1:
        st.subheader("판매처별 평균 가격")
        pv1 = df_shop_filtered.pivot_table(index='mallName', values='lprice', aggfunc='mean').sort_values('lprice', ascending=False).head(10)
        st.dataframe(pv1.style.format('{:,.0f}'))
    with ct2:
        st.subheader("카테고리별 상품 수")
        pv2 = df_shop_filtered.pivot_table(index='category3', columns='keyword', values='productId', aggfunc='count', fill_value=0)
        st.dataframe(pv2)

# Tab 3: 블로그
with tab3:
    st.header("블로그 게시물 분석")
    st.dataframe(df_blog_filtered[['postdate', 'title', 'bloggername', 'link']].head(20))

# Tab 4: Raw Data
with tab4:
    st.header("데이터 원본")
    st.write(df_shop_filtered)

st.markdown("---")
st.caption("Dashboad Created for Naver API Project")
