import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

START_DATE = "2025-12-17"
END_DATE = datetime.today().strftime('%Y-%m-%d') # 현재 날짜까지 실시간 수집

# 웹 페이지 제목 및 레이아웃 설정
st.set_page_config(page_title="그룹 프로젝트 투자 수익률", layout="wide")
st.title("2025 스마트시티와 회계학 그룹 프로젝트")
st.markdown(f"{START_DATE} ~ {END_DATE} 투자 수익률")

# 9개 그룹별 투자/미투자 기업 데이터 매핑
group_data = {
    "1조": {"inv_name": "DB손해보험", "inv_code": "005830.KS", "non_name": "현대해상", "non_code": "001450.KS"},
    "2조": {"inv_name": "GS리테일", "inv_code": "007070.KS", "non_name": "BGF리테일", "non_code": "282330.KS"},
    "3조": {"inv_name": "SK바이오사이언스", "inv_code": "302440.KS", "non_name": "셀트리온", "non_code": "068270.KS"},
    "4조": {"inv_name": "KG이니시스", "inv_code": "035600.KQ", "non_name": "카카오페이", "non_code": "377300.KS"},
    "5조": {"inv_name": "셀트리온", "inv_code": "068270.KS", "non_name": "삼성바이오로직스", "non_code": "207940.KS"},
    "6조": {"inv_name": "넥슨게임즈", "inv_code": "225570.KQ", "non_name": "시프트업", "non_code": "462870.KS"},
    "7조": {"inv_name": "LIG넥스원", "inv_code": "079550.KS", "non_name": "현대로템", "non_code": "064350.KS"},
    "8조": {"inv_name": "삼성전기", "inv_code": "009150.KS", "non_name": "LG이노텍", "non_code": "011070.KS"},
    "9조": {"inv_name": "DB하이텍", "inv_code": "000990.KS", "non_name": "LX세미콘", "non_code": "108320.KS"}
}

@st.cache_data(ttl=3600)  # 1시간 동안 데이터를 캐싱하여 속도 최적화
def load_all_data():
    summary_results = []
    df_timeline = pd.DataFrame()
    
    for group, info in group_data.items():
        inv_hist = yf.Ticker(info["inv_code"]).history(start=START_DATE, end=END_DATE)
        non_hist = yf.Ticker(info["non_code"]).history(start=START_DATE, end=END_DATE)
        
        if not inv_hist.empty and not non_hist.empty:
            inv_start, inv_end = inv_hist['Close'].iloc[0], inv_hist['Close'].iloc[-1]
            non_start, non_end = non_hist['Close'].iloc[0], non_hist['Close'].iloc[-1]
            
            inv_return = ((inv_end - inv_start) / inv_start) * 100
            non_return = ((non_end - non_start) / non_start) * 100
            
            summary_results.append({
                "그룹": group,
                "투자기업": info["inv_name"],
                "투자_최초주가": round(inv_start),
                "투자_현재주가": round(inv_end),
                "투자_수익률(%)": round(inv_return, 2),
                "미투자기업": info["non_name"],
                "미투자_최초주가": round(non_start),
                "미투자_현재주가": round(non_end),
                "미투자_수익률(%)": round(non_return, 2),
                "투자-미투자(%p)": round(inv_return - non_return, 2)
            })
            
            # 시계열 수익률 계산
            col_name = f"{group} ({info['inv_name']})"
            inv_hist[col_name] = ((inv_hist['Close'] - inv_start) / inv_start) * 100
            if df_timeline.empty:
                df_timeline = inv_hist[[col_name]]
            else:
                df_timeline = df_timeline.join(inv_hist[[col_name]], how='outer')
                
    return pd.DataFrame(summary_results), df_timeline.ffill().dropna()

with st.spinner("KRX 마켓으로부터 데이터를 불러오는 중입니다..."):
    df_raw, df_timeline = load_all_data()

def color_pos_neg(val):
    if val > 0:
        return 'color: red; font-weight: bold;'
    elif val < 0:
        return 'color: blue; font-weight: bold;'
    return ''

# 데이터 포맷 규칙 정의
format_dict = {
    "투자_최초주가": "{:,.0f}원", "투자_현재주가": "{:,.0f}원", "투자_수익률(%)": "{:+.2f}%",
    "미투자_최초주가": "{:,.0f}원", "미투자_현재주가": "{:,.0f}원", "미투자_수익률(%)": "{:+.2f}%",
    "투자-미투자(%p)": "{:+.2f}%p"
}

# 탭 구조로 리더보드 분리
tab1, tab2, tab3 = st.tabs(["🏆 투자 수익률", "⚖️ 투자 선택 격차", "📈 시계열 수익률"])

with tab1:
   
    df1 = df_raw[["그룹", "투자_수익률(%)", "투자기업", "투자_최초주가", "투자_현재주가"]].copy()
    df1 = df1.sort_values(by="투자_수익률(%)", ascending=False).reset_index(drop=True)
    df1.index += 1
    
    styled_df1 = df1.style.map(color_pos_neg, subset=["투자_수익률(%)"]).format(format_dict)
    st.dataframe(styled_df1, use_container_width=True)

with tab2:
    
    df2 = df_raw[["그룹", "투자-미투자(%p)", "투자기업", "투자_수익률(%)", "미투자기업", "미투자_수익률(%)"]].copy()
    df2 = df2.sort_values(by="투자-미투자(%p)", ascending=False).reset_index(drop=True)
    df2.index += 1

    styled_df2 = df2.style.map(color_pos_neg, subset=["투자-미투자(%p)"]).format(format_dict)
    st.dataframe(styled_df2, use_container_width=True)

with tab3:
    
    fig = go.Figure()
    for col in df_timeline.columns:
        custom_labels = df_timeline[col].map(lambda v: f"{v:+.2f}%")
        fig.add_trace(go.Scatter(
            x=df_timeline.index,
            y=df_timeline[col],
            customdata=custom_labels,
            mode='lines',
            name=col,
            hovertemplate=f"{col}<br>" + "%{customdata}<extra></extra>"
        ))
    
    fig.update_layout(
        xaxis_title="날짜",
        yaxis_title="수익률 (%)",
        yaxis_tickformat="+.1f%",
        hovermode="closest",
        template="plotly_white",
        legend=dict(
            itemclick="toggleothers",  # 클릭 시 해당 기업만 표시
            itemdoubleclick="toggle",  # 더블클릭 시 전체 표시 복원
            orientation="h", 
            yanchor="bottom", 
            y=-0.35, 
            xanchor="center", 
            x=0.5
        ),
        height=600
    )
    st.plotly_chart(fig, use_container_width=True)
