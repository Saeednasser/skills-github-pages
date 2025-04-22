import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import date

# إعداد صفحة التطبيق
st.set_page_config(
    page_title="فلتر اختراق الشموع البيعية",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ستايل الواجهة
st.markdown(
    """
    <style>
    body { background-color: #f2f2f2; font-family: 'Cairo', sans-serif; }
    .stButton>button { background-color: #3366cc; color: white; font-weight: bold;
                       padding: 0.4em 1em; margin-top: 0.5em; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True
)

# عنوان التطبيق
st.markdown("""
<div style='background-color:#3366cc;padding:10px;border-radius:10px'>
  <h2 style='color:white;text-align:center;'>📉 فلتر اختراق الشموع البيعية</h2>
</div>
""", unsafe_allow_html=True)

# الدوال الرئيسية
def fetch_data(symbols, start_date, end_date, interval):
    try:
        return yf.download(
            tickers=symbols,
            start=start_date,
            end=end_date,
            interval=interval,
            group_by='ticker',
            auto_adjust=True,
            progress=False,
            threads=True
        )
    except Exception as e:
        st.error(f"خطأ في تحميل البيانات: {e}")
        return None

def detect_sell_breakout(df, lose_body_percent=0.55):
    o,h,l,c = df['Open'].values, df['High'].values, df['Low'].values, df['Close'].values
    ratio = np.where((h-l)!=0, np.abs(o-c)/(h-l),0)
    valid = (c<o)&(ratio>=lose_body_percent)
    highs = np.full(len(df), np.nan)
    breakout = np.zeros(len(df), dtype=bool)
    for i in range(1,len(df)):
        if not np.isnan(highs[i-1]) and c[i]>highs[i-1] and not valid[i]:
            breakout[i]=True
            highs[i]=np.nan
        else:
            highs[i] = h[i] if valid[i] else highs[i-1]
    df['breakout'] = breakout
    return df

# واجهة المستخدم
with st.sidebar:
    st.markdown("### ⚙️ إعدادات التحليل")
    market = st.selectbox("اختر السوق", ["السوق السعودي","السوق الأمريكي"])
    suffix = ".SR" if market=="السوق السعودي" else ""
    interval = st.selectbox("اختر الفاصل الزمني", ["1d","1wk","1mo"])
    start_date = st.date_input("تاريخ البدء", date(2020,1,1))
    end_date = st.date_input("تاريخ الانتهاء", date.today())
    st.markdown("---")
    if st.button("🎯 تجربة على رموز مشهورة"):
        st.session_state['symbols'] = "1120 2380 1050" if suffix==".SR" else "AAPL MSFT GOOGL"

symbols_input = st.text_area(
    "أدخل الرموز (افصل بينها بمسافة أو سطر)",
    st.session_state.get('symbols','1120 2380 1050')
)
symbols = [sym.strip()+suffix for sym in symbols_input.replace('\n',' ').split()]

if st.button("🔎 تنفيذ التحليل"):
    data = fetch_data(symbols, start_date, end_date, interval)
    if data is None:
        st.error("فشل تحميل البيانات.")
    else:
        results=[]
        for code in symbols:
            try:
                df = data[code].reset_index()
                res = detect_sell_breakout(df)
                if res['breakout'].iloc[-1]:
                    results.append((code.replace(suffix,''), round(res['Close'].iloc[-1],2)))
            except:
                continue

        if results:
            st.success("✅ الرموز التي تحقق فيها الاختراق:")
            df_out = pd.DataFrame(results,columns=["الرمز","سعر الإغلاق"])
            col1,col2 = st.columns(2)
            col1.metric("رموز مدخلة",len(symbols))
            col2.metric("اختراقات",len(results))
            st.dataframe(df_out)
            st.download_button("📥 تحميل CSV",df_out.to_csv(index=False),file_name="breakouts.csv")

            st.markdown("---")
            for sym,price in results:
                curr = 'ريال' if suffix=='.SR' else '$'
                st.markdown(f"#### 📊 {sym} – {price} {curr}")
                link = (f"https://www.tradingview.com/symbols/TADAWUL-{sym}/"
                        if suffix=='.SR'
                        else f"https://www.tradingview.com/symbols/{sym}/")
                st.markdown(f"🔗 [فتح الشارت في TradingView]({link})")
        else:
            st.info("🔎 لا توجد اختراقات جديدة.")