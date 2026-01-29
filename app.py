import streamlit as st
import pandas as pd
import math

# --- 頁面設定 ---
st.set_page_config(
    page_title="5G Base Station Heatsink Vol. Calculator V3.9.7",
    layout="centered"
)

# --- 自定義樣式 (模擬您要求的黑框與高對比) ---
# Streamlit 無法像 Tkinter 那樣精細控制每一個像素，但我們可以用 CSS 強化對比
st.markdown("""
    <style>
    /* 強制表格文字為黑色，並增加邊框 */
    .stDataFrame { border: 1px solid black; }
    div[data-testid="stMetricValue"] { color: blue; font-weight: bold; }
    label { font-weight: bold !important; color: black !important; font-size: 1.1rem !important; }
    
    /* 調整標題樣式 */
    h1, h2, h3 { color: black; }
    
    /* 讓按鈕更醒目 */
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        font-size: 18px;
        font-weight: bold;
        width: 100%;
        border: 2px solid black;
    }
    .stButton > button:hover {
        border-color: #333;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- 標題區 ---
st.title("5G 基地台散熱器體積估算")
st.caption("版本: V3.9.7 (Streamlit Cloud 相容版)")

# --- 建立頁籤 ---
tab1, tab2 = st.tabs(["🖥️ 體積估算主程式", "ℹ️ 說明與版本"])

with tab1:
    st.markdown("### 表一：輸入參數 (Input Parameters)")
    
    # 建立輸入區塊，使用 Columns 模擬表格排版
    # 為了美觀與對齊，我們使用 Streamlit 的原生輸入元件
    
    col1, col2 = st.columns(2)
    
    with col1:
        Q = st.number_input("熱源功耗 Q (Watts)", value=300.0, step=10.0, format="%.1f")
        T_max = st.number_input("允許最高溫度 T_max (°C)", value=85.0, step=1.0, format="%.1f")
        H_fin = st.number_input("鰭片高度 H_fin (mm)", value=50.0, step=1.0, format="%.1f")

    with col2:
        T_amb = st.number_input("環境溫度 T_amb (°C)", value=40.0, step=1.0, format="%.1f")
        # V3.9.6 核心修正：設計裕度
        margin = st.number_input("設計裕度 Margin (Ratio)", value=1.2, step=0.1, format="%.2f")
        t_base = st.number_input("基板厚度 t_base (mm)", value=5.0, step=0.5, format="%.1f")

    st.markdown("---")

    # --- 計算按鈕 ---
    if st.button("執行計算 (Calculate)"):
        
        # --- 核心計算邏輯 (與 V3.9.7 相同) ---
        delta_T = T_max - T_amb
        
        if delta_T <= 0:
            st.error("錯誤：最高溫度 (T_max) 必須大於環境溫度 (T_amb)！")
        else:
            # 1. 目標熱阻 R_th = delta_T / (Q * margin)
            R_th = delta_T / (Q * margin)

            # 2. 經驗公式估算所需面積
            h_eff = 0.0012 
            A_req_cm2 = 1 / (R_th * h_eff)

            # 3. 根據鰭片高度估算幾何尺寸
            ratio = 3 + (H_fin / 10) 
            base_area_cm2 = A_req_cm2 / ratio
            
            side_length_cm = math.sqrt(base_area_cm2)
            L_mm = side_length_cm * 10
            W_mm = side_length_cm * 10
            
            # 4. 總體積
            Volume_cm3 = (L_mm * W_mm * H_fin) / 1000

            # --- 顯示結果 (表二) ---
            st.markdown("### 表二：計算結果 (Calculation Results)")
            
            # 使用 Dataframe 呈現表格，因為這樣最整齊且有邊框
            results_data = {
                "結果項目": [
                    "目標熱阻 (R_th)", 
                    "所需散熱面積 (A_req)", 
                    "預估散熱器長度 (L)", 
                    "預估散熱器寬度 (W)", 
                    "總體積 (Volume)"
                ],
                "數值": [
                    f"{R_th:.4f}", 
                    f"{A_req_cm2:.1f}", 
                    f"{L_mm:.1f}", 
                    f"{W_mm:.1f}", 
                    f"{Volume_cm3:.1f}"
                ],
                "單位": [
                    "°C/W", 
                    "cm²", 
                    "mm", 
                    "mm", 
                    "cm³"
                ]
            }
            
            df_results = pd.DataFrame(results_data)
            
            # 顯示表格 (use_container_width 會讓表格填滿寬度)
            st.table(df_results)
            
            # 額外提供醒目的 Metric 顯示
            m1, m2, m3 = st.columns(3)
            m1.metric("預估長度 (L)", f"{L_mm:.1f} mm")
            m2.metric("預估寬度 (W)", f"{W_mm:.1f} mm")
            m3.metric("總體積", f"{Volume_cm3:.1f} cm³")
            
            st.success("計算成功！")

with tab2:
    st.markdown("""
    ### 版本歷程
    * **V3.9.7**: 針對 Streamlit Cloud 優化介面，高對比顯示。
    * **V3.9.6**: 修正術語為「設計裕度 (Margin)」。
    * **V3.9.5**: 修正基礎物理計算邏輯。
    """)
