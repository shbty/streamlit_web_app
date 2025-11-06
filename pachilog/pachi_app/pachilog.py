import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

# 永続化ファイルの定義
DATA_FILE = "pachilog_data.json"

def load_data():
    """保存されたJSONファイルを読み込み、存在しない場合はNoneを返す"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except Exception as e:
            # ファイルが存在するが読み込みに失敗した場合
            st.warning(f"データ読み込み中にエラーが発生しました。初期設定で再開します。エラー: {e}")
            return None
    return None

def save_data(data):
    """現在の全データをJSONファイルに保存する"""
    try:
        # datetimeオブジェクトは直列化できないため、文字列に変換してから保存
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        st.error(f"データの保存中にエラーが発生しました: {e}")
        return False

st.set_page_config(page_title="PachiLog", layout="centered")
st.title("🎰 PachiLog")

# ====== セッション初期化とデータ復元 ======
if "page" not in st.session_state:
    # 最初にデータ読み込みを試行
    loaded_data = load_data()
    
    if loaded_data and loaded_data.get("is_active", False):
        # 実行中のデータがあればセッション状態を復元し、メイン画面から再開
        st.session_state.records = loaded_data.get("records", [])
        st.session_state.machine_info = loaded_data.get("machine_info", {})
        st.session_state.page = "main" 
        st.info("💾 前回の実践データが復元されました。メイン画面から再開します。")
    else:
        # データがない、または前回終了済みの場合、初期値を設定
        st.session_state.records = []
        st.session_state.machine_info = {}
        st.session_state.page = "select"
        
    # 他のセッション状態の初期化
    if "last_hit_payout" not in st.session_state:
        st.session_state.last_hit_payout = 0
    if "last_hit_round" not in st.session_state:
        st.session_state.last_hit_round = 0
    if "last_payout_per_round" not in st.session_state:
        st.session_state.last_payout_per_round = 0


# ====== ページ1：店名・台番号・レート ======
if st.session_state.page == "select":
    # ⚠️ 実践開始前のデータ保存フラグをFalseに
    st.session_state.machine_info["is_active"] = False
    
    st.title("店名/台番号・レート/持ち玉")
    machine_info = st.session_state.machine_info
    
    # 既存の値があれば初期値として使用
    default_shop = machine_info.get("店名", "")
    default_number = machine_info.get("台番号", 0)
    default_rate = machine_info.get("交換率", "4円")
    default_balls = machine_info.get("持ち玉", 0)

    machine_info["店名"] = st.text_input("店名を入力", value=default_shop)
    machine_info["台番号"] = st.number_input("台番号", min_value=0, step=1, value=default_number)
    machine_info["交換率"] = st.radio("交換レート", ["4円", "1円"], horizontal=True, index=["4円", "1円"].index(default_rate))

    with st.expander("持ち玉あり", expanded=False):
        current_balls = st.number_input("現在の持ち玉数（玉）", min_value=0, step=50, key="current_balls_input", value=default_balls)

    if st.button("実践開始 ▶"):
        if machine_info["店名"] and machine_info["台番号"] >= 0:
            now_time = datetime.now()
            
            machine_info["持ち玉"] = int(current_balls)
            machine_info["現金投資額"] = 0
            machine_info["貸し玉可能残金"] = 0 # 初期化
            machine_info["実践開始時間"] = now_time.strftime("%H:%M")
            machine_info["is_active"] = True # 実践中のフラグ
            
            # データ保存 (リフレッシュ対策)
            save_data({"records": st.session_state.records, "machine_info": machine_info, "is_active": True})

            st.session_state.page = "main"
            st.rerun()
        else:
             st.warning("店名と台番号を正しく入力してください。")


# ====== ページ2：メイン画面 ======
elif st.session_state.page == "main":

    info = st.session_state.machine_info
    df = pd.DataFrame(st.session_state.records)

    # 集計系
    total_used_balls = df["使用玉数"].sum() if not df.empty else 0
    total_rotations = df["通常回転"].sum() if not df.empty else 0
    total_payout_balls = df["獲得玉数"].sum() if not df.empty else 0
    total_invest = info.get("現金投資額", 0)
    current_balls = info.get("持ち玉", 0)
    
    st.subheader(f"🏠 {info.get('店名', '未設定')} - 台番号 {info.get('台番号', '未設定')}")
    st.caption(f"開始時刻: {info.get('実践開始時間', '---')} / レート: {info.get('交換率', '---')}")


    # 平均回転率
    if total_used_balls > 0:
        rate_unit = 1000 if info.get("交換率") == "1円" else 250
        avg_rotation = total_rotations / total_used_balls * rate_unit
    else:
        avg_rotation = 0

    # メトリクス表示
    st.divider()
    
    col_kane, col_ball, col_rot = st.columns(3)
    col_kane.metric("現金投資総額", f"{total_invest:,} 円")
    col_ball.metric("現在持ち玉数", f"{current_balls:,} 玉")
    col_rot.metric("平均回転率", f"{avg_rotation:.2f} 回/K")
    st.metric("総通常回転", f"{total_rotations:,} 回転")

    # 💰 投資ボタン
    col1, col2, col3, col4 = st.columns([4,1,1,1])
    col1.subheader("💵 追銭")

    invest_actions = {
        "1000円": 1000, "5000円": 5000, "10000円": 10000
    }
    
    for i, (label, amount) in enumerate(invest_actions.items()):
        if st.columns([4,1,1,1])[i+1].button(label):
            info["現金投資額"] = total_invest + amount
            info["貸し玉可能残金"] = info.get("貸し玉可能残金", 0) + amount
            
            # データ保存 (リフレッシュ対策)
            save_data({"records": st.session_state.records, "machine_info": info, "is_active": True})
            st.rerun()
    
    st.divider()
    
    col_title, col_button = st.columns([4, 1])
    with col_title:
        st.subheader("📋 記録一覧")

    with col_button:
        if st.button("➕ 行を追加", use_container_width=True):
            st.session_state.edit_index = None
            st.session_state.page = "add_row"
            
            # 💡 データの永続化を考慮し、セッションデータのリセットはadd_rowへ移動
            
            st.rerun()

    # 一覧表示
    if not df.empty:
        # 💡 st.dataframeを使用し、見やすく改善
        display_df = df.copy()
        display_df['使用玉数'] = display_df['使用玉数'].apply(lambda x: f"{x:,} 玉")
        display_df['獲得玉数'] = display_df['獲得玉数'].apply(lambda x: f"{x:,} 玉")
        display_df['1Rあたり獲得出玉'] = display_df['1Rあたり獲得出玉'].round(2)
        display_df['回転率'] = display_df['回転率'].round(2)
        
        st.dataframe(
            display_df[[
                "時間", "使用玉数", "打ち始め", "打ち終わり", "通常回転", "回転率", "獲得玉数", "ラウンド数", "1Rあたり獲得出玉"
            ]].rename(columns={
                "通常回転": "回転数", "1Rあたり獲得出玉": "1R出玉"
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("まだデータがありません。")
        
    st.divider()
        
    if st.button("🏁 実践終了"):
        # ⚠️ 実践終了処理：データを保存し、is_activeフラグをFalseに
        info["is_active"] = False
        save_data({"records": st.session_state.records, "machine_info": info, "is_active": False})
        
        # セッション状態を初期化してページ移動
        st.session_state.records = []
        st.session_state.machine_info = {}
        st.session_state.page = "select"
        st.rerun()


# ====== ページ3：行追加 ======
elif st.session_state.page == "add_row":
    is_edit = st.session_state.get("edit_index") is not None
    info = st.session_state.machine_info
    current_balls = int(info.get("持ち玉", 0))
    new_invest_money = int(info.get("貸し玉可能残金", 0)) # 0をデフォルト値に

    st.subheader("📝 記録入力")
    
    # 💡 ページ遷移時に値をリセットする（リフレッシュ対策済みなので、ここでは明示的にリセットする）
    # is_editがNoneで、かつ初回ロード時（または戻るボタン以外での遷移時）に実行
    if not is_edit and not st.session_state.get("add_row_initialized", False):
        # last_hitなどの当たり記録をリセット
        st.session_state.last_hit_payout = 0
        st.session_state.last_hit_round = 0
        st.session_state.last_payout_per_round = 0
        # 回転数入力を初期化（前回の打ち終わりを次の打ち始めにするロジックも追加可能）
        st.session_state["add_row_start_rot"] = 0 
        st.session_state["add_row_end_rot"] = 0
        st.session_state["add_row_new_balls"] = current_balls # 持ち玉を初期値に
        st.session_state.add_row_initialized = True
        
    # 貸し玉ボタン
    col1, col2 = st.columns([4,1])
    with col1:
        st.metric("貸し玉可能残金", f"{new_invest_money} 円")
    with col2:
        zero_invest_money = (new_invest_money < 500 and info.get("交換率") == "4円") or \
                           (new_invest_money < 200 and info.get("交換率") == "1円")
                           
        if st.button("貸し玉", disabled=zero_invest_money):
            selected_rate = info.get("交換率", "4円")
            if selected_rate == "4円":
                min_money = 500
                added_balls = 125
            else:
                min_money = 200
                added_balls = 200
                
            # 貸し玉ボタンは st.number_input と連動させるため、session_stateを更新
            st.session_state["add_row_new_balls"] = st.session_state["add_row_new_balls"] + added_balls
            info["持ち玉"] = st.session_state["add_row_new_balls"]
            info["貸し玉可能残金"] = new_invest_money - min_money
            
            # データ保存 (リフレッシュ対策)
            save_data({"records": st.session_state.records, "machine_info": info, "is_active": True})
            st.rerun()

    # 現在の持ち玉数入力 (keyにより値が保持される)
    st.number_input(
        "現在の持ち玉数を入力", 
        min_value=0, 
        step=50, 
        key="add_row_new_balls" # 💡 keyによりセッション状態に保持
    )
    new_current_balls = st.session_state["add_row_new_balls"]
    
    # 💡 貸し玉前の持ち玉（前回確定時の持ち玉）を取得
    balls_at_start_of_row = info.get("持ち玉", 0) 
    
    # 使用球数自動計算 (新しい持ち玉と、行開始時の持ち玉を比較)
    used_balls = max(balls_at_start_of_row - new_current_balls, 0)
    st.write(f"使用玉数: {used_balls} 玉")


    # 回転数入力
    if is_edit:
        # 編集モードの場合、既存レコードの値を初期値としてセッションに設定
        if "edit_index" in st.session_state:
            record = st.session_state.records[st.session_state.edit_index]
            st.session_state["add_row_start_rot"] = record["打ち始め"]
            st.session_state["add_row_end_rot"] = record["打ち終わり"]
    
    # number_inputをkeyだけで定義することで、セッション状態から値を読み込み、変更をセッションに書き込む
    st.number_input("打ち始め回転数", min_value=0, step=1, key="add_row_start_rot")
    st.number_input("打ち終わり回転数", min_value=0, step=1, key="add_row_end_rot")
    
    start_rot = st.session_state["add_row_start_rot"]
    end_rot = st.session_state["add_row_end_rot"]
    
    st.divider()
    
    # 獲得玉数表示
    payout_from_hit = st.session_state.get("last_hit_payout", 0)
    payout_from_round = st.session_state.get("last_hit_round", 0)
    payout_from_per_round = st.session_state.get("last_payout_per_round", 0)
    gained_balls = payout_from_hit
    
    st.write(f"獲得玉数: {gained_balls} 玉 (合計 {payout_from_round}R)")
    
    if st.button("🎯 当たり記録", use_container_width=True):
        # 記録するデータを初期化
        st.session_state.hit_records = [] 
        # 新しいページへ遷移
        st.session_state.page = "hit_dist"
        st.session_state.add_row_initialized = False # ページ離脱時にリセット
        st.rerun()
        
    st.divider()
    
    # 最終持ち玉計算
    final_balls = new_current_balls + gained_balls

    # 確定処理
    if st.button("✅ 確定"):
        normal_rot = max(end_rot - start_rot, 0)
        selected_rate = info.get("交換率", "4円")
        rate_unit = 250 if selected_rate == "4円" else 1000
        
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
            "1Rあたり獲得出玉": round(payout_from_per_round, 2),
        }

        if is_edit:
            st.session_state.records[st.session_state.edit_index] = new_record
        else:
            st.session_state.records.append(new_record)

        # ✅ 現在持ち玉更新 (確定後の持ち玉)
        st.session_state.machine_info["持ち玉"] = final_balls
        # 貸し玉前の持ち玉を更新
        st.session_state.machine_info["balls_at_start_of_row"] = final_balls 

        # データ保存 (リフレッシュ対策)
        save_data({"records": st.session_state.records, "machine_info": st.session_state.machine_info, "is_active": True})
        
        st.session_state.page = "main"
        st.session_state.add_row_initialized = False # ページ離脱時にリセット
        st.rerun()

    if st.button("⬅ 戻る"):
        st.session_state.page = "main"
        st.session_state.edit_index = None
        st.session_state.add_row_initialized = False # ページ離脱時にリセット
        st.rerun()
        
# ====== ページ4：当たり ======
elif st.session_state.page == "hit_dist":
    st.title("🎯 当たり詳細記録")
    
    # データフレームの初期化
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

    # 記録一覧
    if not hit_df.empty:
        st.dataframe(hit_df, use_container_width=True, hide_index=True)
        st.divider()
        
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
        if st.button("✅ 確定 (戻る)", use_container_width=True):
            # 各数値を add_row 画面に渡す
            st.session_state.last_hit_round = total_round
            st.session_state.last_hit_payout = total_payout
            st.session_state.last_payout_per_round = payout_per_round
            
            st.session_state.page = "add_row"
            st.rerun()
    else:
        st.info("ラウンド記録を追加してください。")
