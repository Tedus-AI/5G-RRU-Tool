import streamlit as st
import pandas as pd
import numpy as np

# === APP 設定 ===
st.set_page_config(page_title="5G RRU Thermal Calculator (Pro)", layout="wide")

st.title("📡 5G RRU 體積估算引擎 (Excel 1:1 還原版)")
st.markdown("### 完整物理核心：含 Base/Block 幾何擴散運算")

# ==================================================
# 1. 側邊欄：全域邊界條件 (Table 1)
# ==================================================
st.sidebar.header("🛠️ 全域邊界條件 (Table 1)")

# 環境與係數
with st.sidebar.expander("環境與係數設定", expanded=True):
    T_amb = st.number_input("環境溫度 (°C)", value=45.0, step=1.0)
    h_value = st.number_input("自然對流係數 h (W/m2K)", value=8.8, step=0.1)
    Margin = st.number_input("設計安全係數 (Margin)", value=1.0, step=0.1)
    Slope = 0.03 # 空氣升溫梯度
    Eff = st.number_input("鰭片效率 (Eff)", value=0.95, step=0.01)

# 機構參數
with st.sidebar.expander("PCB 與 機構尺寸", expanded=False):
    L_pcb = st.number_input("PCB 長度 (mm)", value=350)
    W_pcb = st.number_input("PCB 寬度 (mm)", value=250)
    t_base = st.number_input("散熱器基板厚 (mm)", value=7)
    H_shield = st.number_input("HSK內腔深度 (mm)", value=20)
    H_filter = st.number_input("Filter 厚度 (mm)", value=42)

# 材料參數 (對應 Excel 表一 B19~B29)
with st.sidebar.expander("材料導熱係數與厚度", expanded=False):
    st.caption("請對照 Excel 表一參數")
    # Putty
    K_Putty = 9.1
    t_Putty = 0.5
    # Pad
    K_Pad = 7.5
    t_Pad = 1.7
    # Grease
    K_Grease = 3.0
    t_Grease = 0.05
    # Solder
    K_Solder = 58.0
    t_Solder = 0.3
    Voiding = 0.75 # 錫片空洞率
    # Via
    K_Via = 30.0 # 等效 K
    Via_Eff = 0.9 # 製程有效係數

# 散熱器參數
with st.sidebar.expander("鰭片幾何", expanded=False):
    Gap = st.number_input("鰭片間距 (mm)", value=13.2, step=0.1)
    Fin_t = st.number_input("鰭片厚度 (mm)", value=1.2, step=0.1)

# 邊框
Top, Btm, Left, Right = 11, 13, 11, 11

# ==================================================
# 2. 主畫面：元件熱源清單 (Table 2 - 完整版)
# ==================================================
st.subheader("🔥 元件熱源清單 (Table 2)")
st.info("已找回 H/I 欄位 (Base L/W)。請注意：部分元件的 Base 尺寸在 Excel 中是公式 (Pad+Thick)，此處為方便編輯已轉為數值。")

# 建立預設資料 (依照 Excel 最終版邏輯填入)
# Base L/W 的預設值已經幫您算好 (例如 Driver PA: 5 + 2 = 7)
data = {
    "Component": ["Final PA", "Driver PA", "Pre Driver", "Circulator", "Cavity Filter", "CPU (FPGA)", "Si5518", "16G DDR", "Power Mod", "SFP"],
    "Qty": [4, 4, 4, 4, 1, 1, 1, 2, 1, 1],
    "Power(W)": [52.13, 9.54, 0.37, 2.76, 31.07, 35.00, 2.00, 0.40, 29.00, 0.50],
    "Height(mm)": [250, 200, 180, 250, 0, 50, 80, 60, 30, 0], # D欄
    # 幾何尺寸 inputs
    "Pad_L": [20, 5, 2, 10, 0, 35, 8.6, 7.5, 58, 14], # F欄
    "Pad_W": [10, 5, 2, 10, 0, 35, 8.6, 11.5, 61, 50], # G欄
    "Base_L": [55, 7, 4, 12, 0, 0, 10.6, 0, 0, 0],    # H欄 (Excel中部分是公式)
    "Base_W": [35, 7, 4, 12, 0, 0, 10.6, 0, 0, 0],    # I欄
    "Thick(mm)": [2.5, 2.0, 2.0, 2.0, 0, 0, 2.0, 0, 0, 0], # J欄
    "K_Board": [380, K_Via, K_Via, K_Via, 0, 0, K_Via, 0, 0, 0], # K欄
    "Limit(C)": [225, 200, 175, 125, 200, 100, 125, 95, 95, 200], # L欄
    "R_jc": [1.50, 1.70, 50.0, 0.0, 0.0, 0.16, 0.50, 0.0, 0.0, 0.0], # N欄
    # TIM 選擇 (影響 R_TIM 計算參數)
    "TIM_Type": ["Solder", "Grease", "Grease", "Grease", "None", "Putty", "Pad", "Grease", "Grease", "Grease"]
}

df = pd.DataFrame(data)

# 讓使用者編輯表格 (設定欄位格式)
edited_df = st.data_editor(
    df,
    column_config={
        "TIM_Type": st.column_config.SelectboxColumn(
            "TIM Type",
            options=["Solder", "Grease", "Pad", "Putty", "None"],
            required=True,
        ),
        "Height(mm)": st.column_config.NumberColumn("Height (D欄)"),
        "Pad_L": st.column_config.NumberColumn("Pad L (F欄)"),
        "Pad_W": st.column_config.NumberColumn("Pad W (G欄)"),
        "Base_L": st.column_config.NumberColumn("Base L (H欄)"),
        "Base_W": st.column_config.NumberColumn("Base W (I欄)"),
    },
    num_rows="dynamic",
    use_container_width=True
)

# === 後台運算引擎 (Excel 邏輯復刻) ===

# 定義 TIM 參數字典
tim_props = {
    "Solder": {"k": K_Solder, "t": t_Solder},
    "Grease": {"k": K_Grease, "t": t_Grease},
    "Pad":    {"k": K_Pad,    "t": t_Pad},
    "Putty":  {"k": K_Putty,  "t": t_Putty},
    "None":   {"k": 1,        "t": 0}
}

def calculate_excel_logic(row):
    # 1. 計算局部環溫 (E欄)
    # Excel: = B3 + (D * Slope)
    local_amb = T_amb + (row['Height(mm)'] * Slope)
    
    # 準備面積數據 (轉成 m2)
    pad_area_m2 = (row['Pad_L'] * row['Pad_W']) / 1_000_000
    base_area_m2 = (row['Base_L'] * row['Base_W']) / 1_000_000
    
    # 2. R_int 計算 (O欄)
    # Excel 邏輯: Thickness / (K * sqrt(PadArea * BaseArea) * Eff)
    # 如果 K=0 (如 FPGA), R_int = 0
    if row['K_Board'] > 0 and pad_area_m2 > 0:
        # 計算擴散面積幾何平均 (如果 Base=0, 就用 Pad 面積)
        if base_area_m2 > 0:
            eff_area = np.sqrt(pad_area_m2 * base_area_m2)
        else:
            eff_area = pad_area_m2
            
        # 基礎熱阻
        r_int_val = (row['Thick(mm)'] / 1000) / (row['K_Board'] * eff_area)
        
        # 特殊判斷: Final PA (需要加上 Solder Voiding 效應)
        if row['Component'] == "Final PA":
            # Excel: ... + (Solder_t / (Solder_k * PadArea * Voiding))
            solder_adder = (t_Solder / 1000) / (K_Solder * pad_area_m2 * Voiding)
            r_int = r_int_val + solder_adder
        else:
            # 其他元件乘上 Via 效率
            r_int = r_int_val / Via_Eff
    else:
        r_int = 0
        
    # 3. R_TIM 計算 (P欄)
    # 邏輯判斷: 如果有 Base (擴散板), TIM 是貼在 Base 下面 -> 用 Base Area
    # 如果沒有 Base (如 FPGA), TIM 是貼在 Pad 下面 -> 用 Pad Area
    tim_info = tim_props.get(row['TIM_Type'], {"k":1, "t":0})
    
    target_area_m2 = base_area_m2 if base_area_m2 > 0 else pad_area_m2
    
    if target_area_m2 > 0 and tim_info['t'] > 0:
        r_tim = (tim_info['t'] / 1000) / (tim_info['k'] * target_area_m2)
    else:
        r_tim = 0
        
    # 4. 總熱耗與溫升
    total_w = row['Qty'] * row['Power(W)']
    
    # 允許 HSK 溫升 (S欄) = Limit - (Power * (Rjc + Rint + Rtim)) - Local_Amb
    total_r_path = row['R_jc'] + r_int + r_tim
    internal_drop = row['Power(W)'] * total_r_path
    allowed_dt = row['Limit(C)'] - internal_drop - local_amb
    
    return pd.Series([local_amb, r_int, r_tim, total_w, internal_drop, allowed_dt])

# 執行計算
if not edited_df.empty:
    edited_df[['Loc_Amb', 'R_int', 'R_TIM', 'Total_W', 'Drop', 'Allowed_dT']] = edited_df.apply(calculate_excel_logic, axis=1)

    # 找出瓶頸
    valid_rows = edited_df[edited_df['Total_W'] > 0]
    if not valid_rows.empty:
        Total_Watts_Sum = valid_rows['Total_W'].sum()
        Min_dT_Allowed = valid_rows['Allowed_dT'].min()
        bottleneck = valid_rows.loc[valid_rows['Allowed_dT'].idxmin()]
        Bottleneck_Name = bottleneck['Component']
    else:
        Total_Watts_Sum = 0
        Min_dT_Allowed = 50.0
        Bottleneck_Name = "None"
else:
    Total_Watts_Sum = 0
    Min_dT_Allowed = 50.0

# ==================================================
# 3. 體積計算引擎 (Table 3)
# ==================================================
Total_Power = Total_Watts_Sum * Margin

if Total_Power > 0 and Min_dT_Allowed > 0:
    R_sa = Min_dT_Allowed / Total_Power
    Area_req = 1 / (h_value * R_sa * Eff)
    
    L_hsk = L_pcb + Top + Btm
    W_hsk = W_pcb + Left + Right
    Base_Area_m2 = (L_hsk * W_hsk) / 1000000
    
    Fin_Count = W_hsk / (Gap + Fin_t)
    
    try:
        Fin_Height = ((Area_req - Base_Area_m2) * 1000000) / (2 * Fin_Count * L_hsk)
    except:
        Fin_Height = 0
        
    RRU_Height = t_base + Fin_Height + H_filter + H_shield
    Volume_L = (L_hsk * W_hsk * RRU_Height) / 1000000
else:
    Fin_Height = 0
    RRU_Height = 0
    Volume_L = 0

# ==================================================
# 4. 結果儀表板
# ==================================================
st.markdown("---")
st.subheader("📊 最終運算結果 (Excel Check)")

c1, c2, c3, c4 = st.columns(4)
c1.metric("整機總熱耗 (Q45)", f"{round(Total_Power, 2)} W")
c2.metric("系統瓶頸元件 (B50)", f"{Bottleneck_Name}", delta=f"dT: {round(Min_dT_Allowed, 2)}°C")
c3.metric("建議鰭片高度 (B56)", f"{round(Fin_Height, 2)} mm")
c4.metric("★ 整機估算體積 (B60)", f"{round(Volume_L, 2)} L")

# 詳細數據表 (給使用者檢查用)
with st.expander("查看詳細計算數據 (包含 R_int, R_TIM, 局部環溫)"):
    st.dataframe(
        edited_df[['Component', 'Height(mm)', 'Loc_Amb', 'R_int', 'R_TIM', 'Drop', 'Allowed_dT']]
        .style.format("{:.2f}", subset=['Loc_Amb', 'R_int', 'R_TIM', 'Drop', 'Allowed_dT']),
        use_container_width=True
    )
