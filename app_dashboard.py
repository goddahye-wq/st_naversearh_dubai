import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="Naver API Trend Dashboard", layout="wide")

# 스타일링
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# 데이터 로드 함수
@st.cache_data
def load_data():
    raw_path = "raw_data/"
    files = os.listdir(raw_path)
    
    # 최근 파일 찾기 로직
    search_trend_file = sorted([f for f in files if "dubai_search_trend_2025" in f])[-1]
    blog_file = sorted([f for f in files if "dubai_blog_latest" in f])[-1]
    shop_file = sorted([f for f in files if "dubai_shop_latest" in f])[-1]
    
    df_trend = pd.read_csv(os.path.join(raw_path, search_trend_file))
    df_blog = pd.read_csv(os.path.join(raw_path, blog_file))
    df_shop = pd.read_csv(os.path.join(raw_path, shop_file))
    
    # 전처리
    df_trend['date'] = pd.to_datetime(df_trend['date'])
    df_shop['lprice'] = pd.to_numeric(df_shop['lprice'], errors='coerce')
    
    return df_trend, df_blog, df_shop

try:
    df_trend, df_blog, df_shop = load_data()
except Exception as e:
    st.error(f"데이터 로드 중 오류 발생: {e}")
    st.stop()

# 사이드바 구성
st.sidebar.title("🔍 검색 옵션")
keywords = df_trend['keyword_group'].unique().tolist()
selected_keywords = st.sidebar.multiselect("분석 키워드 선택", keywords, default=keywords)

st.sidebar.markdown("---")
st.sidebar.info("이 대시보드는 Naver API를 통해 수집된 2025년 트렌드 및 최신 데이터를 분석합니다.")

# 메인 헤더
st.title("🍫 두바이 쿠키 & 초콜릿 트렌드 분석 대시보드")
st.markdown(f"**기준일**: {datetime.now().strftime('%Y-%m-%d')}")

# 데이터 필터링
df_trend_filtered = df_trend[df_trend['keyword_group'].isin(selected_keywords)]
df_blog_filtered = df_blog[df_blog['keyword'].isin(selected_keywords)]
df_shop_filtered = df_shop[df_shop['keyword'].isin(selected_keywords)]

# 탭 구성
tab1, tab2, tab3, tab4 = st.tabs(["📈 트렌드 분석", "🛍️ 쇼핑 EDA", "📝 블로그 인사이트", "📊 데이터 원본"])

# Tab 1: 트렌드 분석
with tab1:
    st.header("2025년 검색 트렌드 비교")
    
    # 그래프 1: 시계열 트렌드 (Plotly)
    fig_line = px.line(df_trend_filtered, x='date', y='ratio', color='keyword_group',
                      title="2025년 일별 검색 추이 (상대 비중)",
                      labels={'ratio': '검색 비중 (%)', 'date': '일자'},
                      template="plotly_white")
    st.plotly_chart(fig_line, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        # 표 1: 키워드별 평균/최대 비율 요약
        st.subheader("키워드별 트렌드 요약")
        trend_summary = df_trend_filtered.groupby('keyword_group')['ratio'].agg(['mean', 'max', 'std']).reset_index()
        trend_summary.columns = ['키워드', '평균 비중', '최대 비중', '표준편차']
        st.table(trend_summary.style.format({'평균 비중': '{:.2f}', '최대 비중': '{:.2f}', '표준편차': '{:.2f}'}))
        
    with col2:
        # 그래프 2: 월별 추이 (Bar)
        df_trend_filtered['month'] = df_trend_filtered['date'].dt.strftime('%m')
        monthly_trend = df_trend_filtered.groupby(['month', 'keyword_group'])['ratio'].mean().reset_index()
        fig_bar = px.bar(monthly_trend, x='month', y='ratio', color='keyword_group', barmode='group',
                        title="월별 평균 검색 트렌드", labels={'ratio': '평균 비중', 'month': '월'})
        st.plotly_chart(fig_bar, use_container_width=True)

# Tab 2: 쇼핑 EDA (심화 분석 포함)
with tab2:
    st.header("🛒 쇼핑 데이터 심화 탐색 (Advanced EDA)")
    
    # 2.1 결측치 분석 섹션
    st.subheader("1. 데이터 품질 및 결측치 현황")
    col_missing1, col_missing2 = st.columns([2, 1])
    with col_missing1:
        # 결측값 개수 및 비율 시각화
        missing_values = df_shop_filtered.isnull().sum()
        missing_ratio = (missing_values / len(df_shop_filtered)) * 100
        df_missing = pd.DataFrame({'Column': missing_values.index, 'Count': missing_values.values, 'Ratio': missing_ratio.values})
        df_missing = df_missing[df_missing['Count'] > 0].sort_values('Ratio', ascending=False)
        
        if not df_missing.empty:
            fig_missing = px.bar(df_missing, x='Column', y='Ratio', text='Count',
                                title="컬럼별 결측치 비율 (%) 및 개수",
                                labels={'Ratio': '결측 비율 (%)'}, template="plotly_white", color_discrete_sequence=['#ff4b4b'])
            st.plotly_chart(fig_missing, use_container_width=True)
        else:
            st.success("✅ 선택된 쇼핑 데이터에 결측치가 없습니다!")
            
    with col_missing2:
        st.markdown("""
        **[데이터 전처리 인사이트]**
        - `hprice`(최고가) 컬럼의 결측치가 높은 경우, 대다수 상품이 최저가 단일가로 판매됨을 의미합니다.
        - `brand` 및 `maker` 결측치는 수제 디저트 특성상 브랜드명이 상호명(`mallName`)과 동일하거나 미등록된 경우가 많기 때문입니다.
        """)

    st.markdown("---")

    # 2.2 이상치 및 통계 분석 (Boxplot)
    st.subheader("2. 가격 이상치 및 분포 분석")
    col_box1, col_box2 = st.columns([2, 1])
    with col_box1:
        # 이상치 시각화: 박스플롯
        fig_box = px.box(df_shop_filtered, x='keyword', y='lprice', color='keyword',
                        points="all", title="키워드별 가격 분포 및 이상치(Outlier) 확인",
                        labels={'lprice': '가격(원)', 'keyword': '키워드'})
        st.plotly_chart(fig_box, use_container_width=True)
    with col_box2:
        st.markdown("**기초 통계값 요약**")
        st.write(df_shop_filtered.groupby('keyword')['lprice'].describe())
        st.info("💡 박스플롯의 수염(Whisker)을 벗어나는 점들은 세트 상품이나 대용량 구성 등 가격 편차가 큰 이상치를 나타냅니다.")

    st.markdown("---")

    # 2.3 상관관계 및 히트맵
    st.subheader("3. 변수 간 상관관계 및 분석 (Heatmap)")
    
    # 상관관계 분석을 위한 수치형 데이터 생성 (예: 제목 길이, 키워드 비중 등 추출)
    df_corr = df_shop_filtered.copy()
    df_corr['title_length'] = df_corr['title'].str.len()
    df_corr['mall_name_len'] = df_corr['mallName'].str.len()
    
    # 히트맵 1: 쇼핑 데이터 수치 변수 상관관계
    numerical_cols = ['lprice', 'title_length', 'mall_name_len', 'productType']
    corr_matrix = df_corr[numerical_cols].corr()
    
    col_heat1, col_heat2 = st.columns(2)
    with col_heat1:
        fig_heat1 = px.imshow(corr_matrix, text_auto=True, color_continuous_scale='RdBu_r',
                             title="쇼핑 데이터 주요 변수 상관계수 히트맵")
        st.plotly_chart(fig_heat1, use_container_width=True)
        st.markdown("**해석**: 가격(`lprice`)과 제목 길이(`title_length`) 간의 관계를 통해 홍보 문구의 상세함이 가격 책정에 미치는 영향을 파악할 수 있습니다.")

    with col_heat2:
        # 히트맵 2: 월별-키워드별 검색 비중 히트맵 (df_trend 활용)
        df_trend_filtered['month'] = df_trend_filtered['date'].dt.strftime('%m')
        pivot_trend = df_trend_filtered.pivot_table(index='month', columns='keyword_group', values='ratio', aggfunc='mean')
        fig_heat2 = px.imshow(pivot_trend, text_auto=True, color_continuous_scale='Viridis',
                             title="월별-키워드별 평균 검색 비중 히트맵")
        st.plotly_chart(fig_heat2, use_container_width=True)
        st.markdown("**해석**: 특정 월에 급증하는 트렌드 패턴을 한눈에 비교할 수 있습니다.")

    st.markdown("---")

    # 2.4 피벗테이블 및 막대그래프
    st.subheader("4. 심화 피벗 분석 및 시각화")
    
    col_pv1, col_pv2 = st.columns(2)
    with col_pv1:
        # 피벗테이블 1: 몰별-키워드별 평균 가격
        st.markdown("**[표] 판매처별 키워드 평균가 피벗**")
        pv_mall_price = df_shop_filtered.pivot_table(index='mallName', columns='keyword', values='lprice', aggfunc='mean').head(15)
        st.dataframe(pv_mall_price.style.format('{:,.0f}'), use_container_width=True)
        
        # 막대그래프 1: 카테고리별 상품 수
        st.markdown("**[그래프] 카테고리별 등록 상품 수**")
        cat_counts = df_shop_filtered['category3'].value_counts().reset_index()
        fig_bar_cat = px.bar(cat_counts, x='category3', y='count', text_auto=True,
                            title="카테고리별 상품 유통 현황", color='category3')
        st.plotly_chart(fig_bar_cat, use_container_width=True)

    with col_pv2:
        # 피벗테이블 2: 카테고리별-키워드별 상품 수
        st.markdown("**[표] 카테고리별 키워드 상품 비중**")
        pv_cat_count = df_shop_filtered.pivot_table(index='category3', columns='keyword', values='productId', aggfunc='count', fill_value=0)
        st.dataframe(pv_cat_count, use_container_width=True)

        # 막대그래프 2: 키워드별 평균 배송비/가격 등 (현재 데이터 기준 가격 비교)
        st.markdown("**[그래프] 키워드별 가격 데이터 요약**")
        avg_price = df_shop_filtered.groupby('keyword')['lprice'].mean().reset_index()
        fig_bar_price = px.bar(avg_price, x='keyword', y='lprice', color='keyword',
                              title="키워드별 평균 판매가 비교", text_auto='.0f')
        st.plotly_chart(fig_bar_price, use_container_width=True)

# Tab 3: 블로그 인사이트
with tab3:
    st.header("블로그 검색 인사이트")
    
    # 그래프 6: 블로그 포스팅 날짜 분포
    df_blog_filtered['post_date_dt'] = pd.to_datetime(df_blog_filtered['postdate'], format='%Y%m%d')
    blog_daily = df_blog_filtered.groupby(['post_date_dt', 'keyword']).size().reset_index(name='count')
    fig_blog = px.line(blog_daily, x='post_date_dt', y='count', color='keyword',
                      markers=True, title="최근 블로그 포스팅 빈도 추이")
    st.plotly_chart(fig_blog, use_container_width=True)
    
    col_x, col_y = st.columns([1, 2])
    with col_x:
        # 표 4: 블로거 활동 Top 5
        st.subheader("주요 활동 블로거")
        blogger_top = df_blog_filtered['bloggername'].value_counts().head(5).reset_index()
        st.table(blogger_top)
        
    with col_y:
        # 표 5: 최신 게시물 요약 리스트
        st.subheader("최신 게시물 리스트")
        st.dataframe(df_blog_filtered[['postdate', 'title', 'bloggername', 'link']].sort_values('postdate', ascending=False).head(10),
                    use_container_width=True)

# Tab 4: 데이터 원본
with tab4:
    st.header("수집 데이터 상세보기")
    data_choice = st.selectbox("표시할 데이터를 선택하세요", ["검색 트렌드", "쇼핑 상품", "블로그 게시물"])
    
    if data_choice == "검색 트렌드":
        st.dataframe(df_trend_filtered, use_container_width=True)
    elif data_choice == "쇼핑 상품":
        st.dataframe(df_shop_filtered, use_container_width=True)
    else:
        st.dataframe(df_blog_filtered, use_container_width=True)

st.markdown("---")
st.caption("Produced by Antigravity © 2026 | Naver API Project")
