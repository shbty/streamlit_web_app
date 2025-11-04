import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List


#streamlit run pachilog.py

st.set_page_config(page_title="PachiLog", layout="centered")
st.title("🎰 PachiLog")

# セッション初期化
if "page" not in st.session_state:
    st.session_state.page = "select"
if "records" not in st.session_state:
    st.session_state.records = []
if "machine_info" not in st.session_state:
    st.session_state.machine_info = {}

# ====== ページ1：店名・台番号・レート ======
if st.session_state.page == "select":
    st.title("店名/台番号・レート/持ち玉")
    machine_info = st.session_state.machine_info
    
    machine_info["店名"] = st.text_input("店名を入力")
    machine_info["第番号"] = st.number_input("台番号", min_value=0, step=1)
    machine_info["交換率"] = st.radio("交換レート", ["4円", "1円"], horizontal=True)

    with st.expander("持ち玉あり", expanded=False):
        current_balls = st.number_input("現在の持ち玉数（玉）", min_value=0, step=50, key="current_balls_input")

    if st.button("実践開始 ▶"):
        #現在時刻を取得
        now_time = datetime.now()
        machine_info["持ち玉"] = int(current_balls)
        machine_info["現金投資額"] = 0
        # 🎯 実践開始時刻を保存
        machine_info["実践開始時間"] = now_time.strftime("%H:%M")
        st.session_state.page = "main"
        st.rerun()

# ====== ページ2：メイン画面 ======
elif st.session_state.page == "main":

    info = st.session_state.machine_info
    df = pd.DataFrame(st.session_state.records)

    # 集計系
    total_used_balls = df["使用玉数"].sum() if not df.empty else 0
    total_invest = info.get("現金投資額", 0)
    current_balls = info.get("持ち玉", 0)

    # 平均回転率
    if not df.empty and total_used_balls > 0:
        total_rotations = df["通常回転"].sum()
        rate_unit = 1000 if info.get("交換率") == "1円" else 250
        avg_rotation = total_rotations / total_used_balls * rate_unit
    else:
        avg_rotation = 0

    # メトリクス表示
    col1, col2, col3, col4 = st.columns([4,1,1,1])

    with col1:
        st.metric("現金投資総額", f"{total_invest:,} 円")
        # 💰 投資ボタン
    with col2:
        if st.button("1000円"):
            info["現金投資額"] = total_invest + 1000
            info["貸し玉可能残金"] = info["現金投資額"]
            st.rerun()
    with col3:
        if st.button("5000円"):
            info["現金投資額"] = total_invest + 5000
            info["貸し玉可能残金"] = info["現金投資額"]
            st.rerun()
    with col4:
        if st.button("10000円"):
            info["現金投資額"] = total_invest + 10000
            info["貸し玉可能残金"] = info["現金投資額"]
            st.rerun()


    st.metric("現在持ち玉数", f"{current_balls:,} 玉")
    
    st.metric("平均回転率", f"{avg_rotation:.2f} 回/K")

    st.divider()
    
    col_title, col_button = st.columns([4, 1])
    with col_title:
        st.subheader("📋 記録一覧")

    with col_button:
        if st.button("➕ 行を追加", use_container_width=True):
            st.session_state.edit_index = None
            st.session_state.page = "add_row"
            # 新しい行を追加する際は、前回の大当たり記録をリセットする
            st.session_state.last_hit_payout = 0
            st.session_state.last_hit_round = 0
            st.session_state.last_payout_per_round = 0
            st.rerun()

    # 一覧表示
    if not df.empty:
        header_cols = st.columns([2, 2, 2, 2, 2, 2, 2, 2, 2])
        for col, title in zip(header_cols, 
            ["時間", "使用玉数", "打ち始め", "打ち終わり", "通常回転数","回転率", "獲得玉数", "ラウンド数", "1R出玉"]):
            col.write(title)

        for i, record in enumerate(st.session_state.records):
            cols = st.columns([2, 2, 2, 2, 2, 2, 2, 2, 2])

            cols[0].write(record["時間"])
            cols[1].write(f"{record['使用玉数']:,} 玉")
            cols[2].write(record["打ち始め"])
            cols[3].write(record["打ち終わり"])
            cols[4].write(record["通常回転"])
            cols[5].write(f"{record['回転率']:.2f}")
            cols[6].write(record["獲得玉数"])
            cols[7].write(record["ラウンド数"])
            cols[8].write(f"{record["1Rあたり獲得出玉"]:.2f}")
    else:
        st.info("まだデータがありません。")
        
    st.divider()
        
    if st.button("🏁 実践終了"):
        end_time = datetime.now()
        start_time = datetime.strptime(st.session_state.machine_info["実践開始時間"], "%H:%M")
        elapsed = end_time - start_time

        # 実践時間（例: 3時間15分）
        hours, remainder = divmod(elapsed.seconds, 3600)
        minutes = remainder // 60
        elapsed_str = f"{hours}時間{minutes}分"

        '''# 集計データ作成
        record = {
            "日付": datetime.now().strftime("%Y-%m-%d"),
            "実践時間": elapsed_str,
            "総回転数": st.session_state.machine_info.get("total_spins", 0),
            "現金投資総額": st.session_state.machine_info.get("total_invest", 0),
            "レート": st.session_state.machine_info.get("rate", 4),
            "総使用持ち玉": st.session_state.machine_info.get("used_balls_total", 0),
            "期待値": st.session_state.machine_info.get("expected_value", 0),
            "仕事量": st.session_state.machine_info.get("work_value", 0),
        }

        # セッションに保存（一覧用）
        if "records" not in st.session_state:
            st.session_state["records"] = []
        st.session_state["records"].append(record)

        st.success("✅ 実践結果を一覧に追加しました！")'''
        st.session_state.page = "select"  # ← ページ1の識別名に合わせて変更
        st.rerun()

# ====== ページ3：行追加 ======
elif st.session_state.page == "add_row":
    is_edit = st.session_state.get("edit_index") is not None
    info = st.session_state.machine_info
    current_balls = int(info.get("持ち玉", 0))
    invest_money = int(info.get("現金投資額"))
    new_invest_money = int(info["貸し玉可能残金"])
    #  貸し玉ボタン
    col1, col2 = st.columns([4,1])
    with col1:
        st.metric("貸し玉可能残金", f"{new_invest_money} 円")
    with col2:
        # 貸し玉可能残金が0の場合はボタンを押せない
        zero_invest_money = (new_invest_money == 0)
        if st.button("貸し玉",disabled=zero_invest_money):
            selected_rate = info.get("交換率", "4円")
            if selected_rate == "4円":
                min_money = 500
                added_balls = 125
            else:
                min_money = 200
                added_balls = 200
                
            current_balls = current_balls + added_balls
            info["持ち玉"] = current_balls
            info["貸し玉可能残金"] = new_invest_money - min_money
            st.rerun()

    # 現在の持ち玉数入力
    new_current_balls = st.number_input("現在の持ち玉数を入力", min_value=0, value=current_balls, step=50)

    # 使用球数自動計算
    used_balls = max(current_balls - new_current_balls, 0)
    st.write(f"使用玉数: {used_balls} 玉")

    # 回転数入力
    if is_edit:
        record = st.session_state.records[st.session_state.edit_index]
        start_rot_default = record["打ち始め"]
        end_rot_default = record["打ち終わり"]
    else:
        start_rot_default, end_rot_default = 0,0
    st.number_input("打ち始め回転数", min_value=0, step=1, key="add_row_start_rot")
    st.number_input("打ち終わり回転数", min_value=0, step=1, key="add_row_end_rot")
    
    start_rot = st.session_state["add_row_start_rot"]
    end_rot = st.session_state["add_row_end_rot"]
    
    st.divider()
    if st.button("当たり記録", use_container_width=True):
        # 記録するデータを初期化
        st.session_state.hit_records = [] 
        # 新しいページへ遷移
        st.session_state.page = "hit_dist"
        st.rerun()
    st.divider()
    
    payout_from_round = st.session_state.get("last_hit_round")
    payout_from_per_round = st.session_state.get("last_payout_per_round")
    # 獲得玉数表示
    payout_from_hit = st.session_state.get("last_hit_payout")
    gained_balls = payout_from_hit
    st.write(f"獲得玉数: {gained_balls} 玉")
    # 最終持ち玉計算
    final_balls = new_current_balls + gained_balls
    #st.write(f" 確定後の持ち玉数: {final_balls} 玉")

    # 確定処理
    if st.button("✅ 確定"):
        normal_rot = max(end_rot - start_rot, 0)
        selected_rate = info.get("交換率", "4円")
        rate_unit = 250 if selected_rate == "4円" else 1000
        
        # 🚨 used_balls が 0 の場合のエラーを防ぐチェックを追加
        if used_balls > 0:
            rotation_rate = (normal_rot / used_balls * rate_unit)
        else:
            rotation_rate = 0

        now = datetime.now().strftime("%H:%M")

        new_record = {
            "時間": record["時間"] if is_edit else now,
            "使用玉数": used_balls,
            "打ち始め": start_rot,
            "打ち終わり": end_rot,
            "通常回転": normal_rot,
            "回転率": round(rotation_rate, 2),
            "獲得玉数": gained_balls,
            "ラウンド数": payout_from_round,
            "1Rあたり獲得出玉": payout_from_per_round,
        }

        if is_edit:
            st.session_state.records[st.session_state.edit_index] = new_record
        else:
            st.session_state.records.append(new_record)

        # ✅ 現在持ち玉更新
        st.session_state.machine_info["持ち玉"] = final_balls
        st.session_state.page = "main"
        st.rerun()

    if st.button("⬅ 戻る"):
        st.session_state.page = "main"
        st.session_state.edit_index = None
        st.rerun()
        
# ====== ページ4：当たり ======
elif st.session_state.page == "hit_dist":
    st.title("🎯 当たり詳細記録")
    
    # データフレームの初期化
    # 記録データがなければ空のDataFrameを作成
    hit_df = pd.DataFrame(st.session_state.get("hit_records", []), 
                         columns=["ラウンド", "獲得出玉"])

    # 💡 ラウンド数と出玉の入力を追加
    with st.form("hit_input_form", clear_on_submit=True):
        col_r, col_ball = st.columns(2)
        
        new_round = col_r.number_input("ラウンド数 (R)", min_value=0, step=1)
        new_balls = col_ball.number_input("獲得出玉 (玉)", min_value=0, step=1)
        
        if st.form_submit_button("➕ 記録を追加"):
            if new_round > 0 or new_balls > 0:
                # セッション状態に新しい記録を追加
                st.session_state.hit_records.append({"ラウンド": new_round, "獲得出玉": new_balls})
                st.rerun()
            else:
                st.warning("ラウンド数と獲得出玉を入力してください。")

    st.divider()

    # 計算と結果表示
    if not hit_df.empty:        
        # 3. 合計値の算出
        total_round = hit_df["ラウンド"].sum()
        total_payout = hit_df["獲得出玉"].sum()
        
        # 4. 1Rあたりの獲得出玉の計算
        if total_round > 0:
            payout_per_round = total_payout / total_round
        else:
            payout_per_round = 0
            
        col_total, col_per_r = st.columns(2)
        col_total.metric("合計ラウンド数", f"{total_round} R")
        col_total.metric("合計獲得出玉", f"{total_payout:,} 玉")
        col_per_r.metric("1Rあたり獲得出玉", f"{payout_per_round:.2f} 玉/R")
        
        # 5. メイン画面に戻るボタン
        if st.button("確定", use_container_width=True):
            # 各数値を add_row 画面に渡す
            st.session_state.last_hit_round = total_round
            st.session_state.last_hit_payout = total_payout
            st.session_state.last_payout_per_round = payout_per_round
            
            st.session_state.page = "add_row"
            st.rerun()
    else:
        st.info("ラウンド記録を追加してください。")