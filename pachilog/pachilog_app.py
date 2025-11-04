import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List


#streamlit run pachilog_app.py

st.set_page_config(page_title="PachiLog", layout="centered")

st.title("🎰 PachiLog")

# ====== タブの作成 ======
tab1, tab2, tab3, = st.tabs(["📐 ボーダー・期待値計算", "📊 実践記録", "📕実践一覧"])

# =============================
# 📐 タブ1：機種ボーダー・トータル確率算出
# =============================
with tab1:
    if "page" not in st.session_state:
        st.session_state.page = "select"
    if "records" not in st.session_state:
        st.session_state.records = []
    if 'edit_target' not in st.session_state:
        st.session_state.edit_target = None # 現在編集中のデータセット（例: 'normal' / 'rush'）
        
    # RUSH中も共通のデータ（normal）とRUSH時固有のデータ（rush）を区別
    if 'normal_entries' not in st.session_state:
        st.session_state.normal_entries = []
    if 'rush_entries' not in st.session_state:
        st.session_state.rush_entries = []
    if 'normal_rush_entries' not in st.session_state:
        st.session_state.normal_rush_entries = []
    # 登録ごとにユニークなキーを生成するためのカウンター
    if 'entry_id_counter' not in st.session_state:
        st.session_state.entry_id_counter = 0
    # 初期値としてセレクトボックスの最初の選択肢を設定
    if 'mode_selection_state' not in st.session_state:
        st.session_state.mode_selection_state = "確変ループ"
    if 'rate_select_state' not in st.session_state:
        st.session_state.rate_select_state = "等価"
        
    def raund_check(prefix: str):
        display_map = {'normal': '通常時',
                       'rush': 'RUSH時',
                       'normal_rush': '通常時/Rush時', }
        display_text = display_map.get(prefix.lower(), '不明なモード')
        st.subheader(f"ラウンド入力 ({display_text})")
        rounds = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        # 編集対象のリストを取得
        entries_key = f'{prefix}_entries'
        if entries_key not in st.session_state:
            st.session_state[entries_key] = []
            
        entries = st.session_state[entries_key]
        
        # --- 1. ラウンド追加ボタンの配置 (チェックボックスからの変更点) ---
        st.markdown("#### 1. ラウンド数ボタンを押して項目を追加")
        button_cols = st.columns(len(rounds))
        
        for r_index, r in enumerate(rounds):
            with button_cols[r_index]:
                # 💡 変更点1: ボタンに変更し、押されたら項目追加
                if st.button(f"{r}R ", key=f"{prefix}_add_{r}"):
                    
                    # ユニークIDを生成
                    st.session_state.entry_id_counter += 1
                    new_id = st.session_state.entry_id_counter
                    
                    # 新しいエントリーをリストに追加
                    new_entry = {
                        "id": new_id,
                        "ラウンド": r,
                        "割合": 0.0, # 初期値は0.0 (ユーザーが設定)
                        # 他のステータス情報もここに追加可能
                    }
                    st.session_state[entries_key].append(new_entry)
                    st.rerun() # UI更新のために再実行
                    
        st.markdown("---")

        # --- 2. 割合の入力フィールドの配置（リストの項目をループ） ---
        st.markdown("#### 2. 追加された項目の割合を入力")
        
        input_col_left, input_col_right = st.columns(2)
        
        # 💡 変更点2: リストの項目をループして入力フィールドを生成
        # リストのコピーを使用し、インデックスが変わらないようにする
        for index, entry in enumerate(entries):
            target_col = input_col_left if index % 2 == 0 else input_col_right
            
            # 固有のキー（id）を使用して session_state を直接操作しない
            unique_key = f"{prefix}_percent_{entry['id']}" 
            unique_key_state = f"{prefix}_state_{entry['id']}"

            with target_col:
                # 削除ボタンと入力フィールドを横並びにする
                col_input, col_state, col_delete = st.columns([2,2,1])

                with col_input:
                    # 💡 変更点3: st.number_input に on_change コールバックを設定し、
                    # 値が変更されるたびにリストを更新する
                    new_percent = st.number_input(
                        f"**{entry['ラウンド']}R** 割合（％）", 
                        value=entry['割合'],
                        step=0.1, 
                        format="%.1f",
                        key=unique_key,
                        label_visibility="visible"
                    )
                    
                with col_state:
                    # 💡 変更点3: st.number_input に on_change コールバックを設定し、
                    # 値が変更されるたびにリストを更新する
                    #new_state = st.text_input("次フロー",key=unique_key_state)
                    OPTIONS = ["確変","時短"]
                    new_state = st.selectbox("次フロー",OPTIONS,index=0,key=unique_key_state)
                
                # 💡 変更点4: 削除ボタンの配置
                with col_delete:
                    st.markdown("<br>", unsafe_allow_html=True) # 位置調整用のスペース
                    if st.button("削除", key=f"{prefix}_delete_{entry['id']}"):
                        # リストからこのIDのエントリを削除
                        st.session_state[entries_key] = [e for e in st.session_state[entries_key] if e['id'] != entry['id']]
                        st.rerun()
            
            if 'ステータス' not in entry or new_state != entry.get('ステータス', ''):
                entry['ステータス'] = new_state
            # 💡 変更点5: number_inputで値が変更されたら、リストの値を更新
            if new_percent != entry['割合']:
                entry['割合'] = new_percent
       
        # --- 3. 合計チェック（フッター） ---
        st.markdown("---")
        
        # 割合の合計を計算
        total_percent = sum(e['割合'] for e in st.session_state[entries_key])
        
        if total_percent != 100:
            st.warning(f"合計: {total_percent:.1f}% (100%になるように調整してください)")
        else:
            st.success(f"合計: {total_percent:.1f}% (OK)")

        # --- 4. 表を作成して保存 ---
        if entries:
            # 表示用のリストを作成
            display_data = []
            
            # ヘッダー行を作成（idは含めない）
            header = ['ラウンド (R)', '割合 (%)', 'ステータス'] 
            display_data.append(header)
            
            for entry in entries:
                # 単位を付与し、idは含めない
                row = [
                    f"{entry['ラウンド']}R",
                    f"{entry['割合']:.1f}%",
                    entry.get('ステータス', '---') # ステータスの値を利用
                ]
                display_data.append(row)
                
            # 💡 修正点: DataFrameを作成し、df_display に代入
            df_display = pd.DataFrame(display_data[1:], columns=display_data[0])
            
            st.session_state[f'{prefix}_display_df'] = df_display
        else:
            st.info("データがありません。ラウンド数ボタンを押して追加してください。")
                
    def get_data_from_raund_check(prefix: str) -> List[dict]:
        """
        指定されたプレフィックスのリストからデータを直接返す
        """
        entries_key = f'{prefix}_entries'
        return st.session_state.get(entries_key, [])
    
    def extract_and_clean_data(df_key: str) -> pd.DataFrame:
        """
        セッション状態から整形済みデータを取り出し、計算用に整形する。
        """
        # DataFrameをセッション状態から取得
        if df_key not in st.session_state:
            st.warning(f"キー '{df_key}' にデータが見つかりません。")
            return pd.DataFrame()

        df_display = st.session_state[df_key].copy()
        
        if df_display.empty:
            return pd.DataFrame()

        # 1. 'ラウンド (R)' から 'R' を取り除き、整数に変換
        # 💡 例: '10R' -> 10
        if 'ラウンド (R)' in df_display.columns:
            df_display['ラウンド_数値'] = df_display['ラウンド (R)'].str.replace('R', '', regex=False).astype(int)
        
        # 2. '割合 (%)' から '%' を取り除き、小数に変換 (例: 50.0% -> 0.50)
        # 💡 例: '50.0%' -> 50.0 -> 0.50
        if '割合 (%)' in df_display.columns:
            # まず '%' を削除し、float型に変換
            df_display['割合_数値'] = df_display['割合 (%)'].str.replace('%', '', regex=False).astype(float)
            # 100で割って確率（0.0～1.0）にする
            df_display['割合_数値'] = df_display['割合_数値'] / 100.0
            
        # 抜き取りたいカラムのみを選択（例: ラウンド数、確率、ステータス）
        if 'ステータス' in df_display.columns:
            df_clean = df_display[['ラウンド_数値', '割合_数値','ステータス']].rename(
                columns={'ラウンド_数値': 'ラウンド (R)', '割合_数値': '割合 (%)','ステータス':'ステータス'}
            )
        else:
            df_clean = df_display[['ラウンド_数値', '割合_数値']].rename(
                columns={'ラウンド_数値': 'ラウンド (R)', '割合_数値': '割合 (%)'}
            )
            

        return df_clean
    
    def list_half():
        
        return
    
    def calculation_boder(rush_continue,A_count,B_count):
        return_data = []
        
        
        #RUSH平均連チャン数
        
        return_data.append(1/(1-rush_continue/100))
        #RUSH中継続時の平均純増出玉
        return_data.append(A_count)
        return_data.append(B_count)
        #1度のRUSH突入で得られる平均純増出玉
        
        #初当たり平均純増出玉
        
        #トータル純増期待出玉
        
        #千円あたりの出玉価値
        
        #ボーダーラインの算出
        
        return return_data

    # === ページ1：機種ボーダー・期待値計算 ===
    if st.session_state.page == "select":
        st.title("📘 基本スペック入力")
        calculation_list = []
            
        machine_name = st.text_input("機種名")
        col1, col2, col3 = st.columns(3)
        with col1:
            prob_normal = st.number_input("大当たり確率（通常時）", value=319.7, step=0.1, format="%.1f")
            prob_rush = st.number_input("大当たり確率（RUSH中）", value=99.9, step=0.1, format="%.1f")
        with col2:
            rush_entry = st.number_input("RUSH突入率（％）", value=50, step=1)
            rush_continue = st.number_input("RUSH継続率（％）", value=80, step=1)
        with col3:
            count_num = st.number_input("カウント数", value=10, step=1)
            attacker_ball = st.number_input("アタッカー賞球", value=10, step=1)

        raund_ball = count_num * attacker_ball

        st.subheader("ラウンド振り分け")
                
        mode = st.radio("ダミーラベル",("確変ループ", "ST"),key="mode_selection_state",label_visibility="collapsed",horizontal=True)
        
        # --- データ表示部分 ---        
        if mode == "確変ループ":
            col1, col2 = st.columns([4,2])
            with col1:
                st.markdown("【確変中も共通】のデータ")
                
            # 'normal' データのみを表示
            with col2:
                if st.button("通常時/Rush時", key="btn_normal_rush_separate"):
                        st.session_state.edit_target = 'normal_rush'
                        st.session_state.page = "raund_select"
                        st.rerun()
            
            if 'normal_rush_display_df' in st.session_state:
                    #st.dataframe(st.session_state.normal_rush_display_df, use_container_width=True, hide_index=True)
                    #表の中の数値を受け取る
                    rush_key = 'normal_rush_display_df' 
                    normal_rush = extract_and_clean_data(rush_key)
                    if not normal_rush.empty:
                       st.dataframe(st.session_state.normal_rush_display_df, use_container_width=True, hide_index=True) 
                       
                       df_normal_rush = normal_rush[normal_rush['ステータス'] == '確変'].copy()
                       #RUSH中継続時の平均純増出玉
                       raund_ball_per_percent = (raund_ball * df_normal_rush['ラウンド (R)']) * (1 - df_normal_rush['割合 (%)'])
                       C_count = raund_ball_per_percent.sum()
                                              
                    
                                        
            else:
                st.info("データを入力してください")

        elif mode == "ST":
            col1, col2 = st.columns([4,2])
            with col1:
                # RUSH時と通常の両方を表示する必要がある
                st.markdown("【通常時】のデータ")                
            with col2:
                # 編集対象を 'normal' にセットし、遷移先の画面で RUSH用データを続けて入力させる
                if st.button("通常時", key="btn_normal_separate"):
                    st.session_state.edit_target = 'normal'
                    st.session_state.page = "raund_select"
                    st.rerun()
                
            if 'normal_display_df' in st.session_state:
                normal_key = "normal_display_df"
                normal = extract_and_clean_data(normal_key)
                if not normal.empty:
                    st.dataframe(st.session_state.normal_display_df, use_container_width=True, hide_index=True)
                    df_normal = normal.copy()
                    
            else:
                st.info("通常時のデータを入力してください")

            col1, col2 = st.columns([4,2])
            with col1:
                st.markdown("【RUSH時】のデータ")
            with col2:
                # RUSH時データ入力ボタンの追加
                if st.button("RUSH時", key="btn_rush_separate"):
                    st.session_state.edit_target = 'rush'
                    st.session_state.page = "raund_select"
                    st.rerun()
                
            if 'rush_display_df' in st.session_state:
                rush_key = "rush_display_df"
                rush = extract_and_clean_data(rush_key)
                if not rush.empty:
                    st.dataframe(st.session_state.rush_display_df, use_container_width=True, hide_index=True)
                    df_rush = rush[rush['ステータス'] == '確変'].copy()
                    
            else:
                st.info("RUSH時のデータを入力してください")
                
        with st.expander("その他の設定", expanded=False):
            rate_select = st.radio("ダミーラベル",("等価", "非等価"),key="rate_select_state",label_visibility="collapsed",horizontal=True)
            if rate_select == "等価":
                exchange_money = st.number_input("換金率", min_value=1, value=4, step=1)
            else:
                exchange_ball = st.number_input("交換率", value=4.00, step=0.01, format="%.2f")
                exchange_money = st.number_input("換金率", value=3.57, step=0.01, format="%.2f")
            
            suport_par = st.number_input("電サポ減算割合（％）", min_value=0, value=10, step=1 )
            suport_par_col = (100 - suport_par) / 100
            if suport_par_col == 0:
                st.info("電サポ割合を修正してください")
               
        #通常時電サポ割合込みのラウンドあたりの玉数 
        A_raund_par_suport = (raund_ball * df_normal['ラウンド (R)']) * suport_par_col
        #   通常時の純増出玉
        if (df_normal['割合 (%)']).all() == 1.0:
            A_raund_ball_per_percent = A_raund_par_suport * (df_normal['割合 (%)'])
            A_count = A_raund_ball_per_percent.sum()
        else:
            A_raund_ball_per_percent = A_raund_par_suport * (df_normal['割合 (%)'])
            A_count = A_raund_ball_per_percent.sum()
                
        #RUSH中電サポ割合込みのラウンドあたりの玉数        
        B_raund_par_suport = (raund_ball * df_rush['ラウンド (R)']) * suport_par_col
        #RUSH中継続時の平均純増出玉
        if (df_rush['割合 (%)']).all() == 1.0:
            B_raund_ball_per_percent = B_raund_par_suport * 1
            B_count = B_raund_ball_per_percent.sum()
        else:
            B_raund_ball_per_percent = B_raund_par_suport * (df_rush['割合 (%)'])
            B_count = B_raund_ball_per_percent.sum()
            
    # === ページ2：ラウンド数の入力 ===       
    if st.session_state.page == "raund_select":
        target = st.session_state.edit_target        
        # データ読み込み/保存用のプレフィックスを渡す（raund_check関数の修正が必要）
        df_display = raund_check(target) 
        
        if st.button("✅確定"):
            # 編集されたデータを、edit_targetに対応するキーに保存する
            st.session_state.normal_distribution_data = get_data_from_raund_check(target) 

            st.session_state.page = "select"
            st.session_state.edit_index = None # 不要なキーをリセット
            st.rerun()  

    # ボーダーライン計算
    if st.button("ボーダーラインを計算"):
        #cal_lis = calculation_boder(rush_continue,A_count,B_count)
        renchan = (1/(1-rush_continue/100))
        st.write(f"平均連チャン数は→　{round(renchan,3)}")
        st.write(f"初当たり(非突入)平均純増出玉→　{A_count}")
        st.write(f"RUSH中継続時の平均純増出玉→　{B_count}")
        dedamaHope = B_count*renchan
        st.write(f"1度のRUSH突入で得られる平均純増出玉→　{round(dedamaHope,3)}")
        new_lucky = A_count + dedamaHope
        st.write(f"初当たり（Rush突入）平均純増出玉→　{round(new_lucky,3)}")
        total_hope_ball = (A_count*0.41) + (new_lucky*0.59)
        st.write(f"トータル純増期待出玉→　{round(total_hope_ball,2)}")
        thousand_par_money = 1000 / exchange_money
        st.write(f"千円当たりの出玉価値→　{round(thousand_par_money,2)}")
        borderLine = (prob_normal * thousand_par_money) / total_hope_ball
        st.write(f"ボーダーライン→　{round(borderLine,2)}")
        #st.rerun()

# =============================
# 📊 タブ2：実践記録
# =============================
with tab2:
    # ====== セッション初期化 ======
    if "page" not in st.session_state:
        st.session_state.page = "select"
    if "records" not in st.session_state:
        st.session_state.records = []
    if "machine_info" not in st.session_state:
        st.session_state.machine_info = {}

    # ====== ページ1：店名・台番号・レート ======
    if st.session_state.page == "select":
        st.title("🎰 店名・台番号選択")

        machine_info = st.session_state.machine_info
        machine_info["shop_name"] = st.text_input("店名を入力")
        machine_info["table_number"] = st.number_input("台番号", min_value=0, step=1)
        machine_info["rate"] = st.radio("交換レート", ["4円", "1円"], horizontal=True)

        with st.expander("持ち玉あり", expanded=False):
            current_balls = st.number_input("現在の持ち玉数（玉）", min_value=0, step=50, key="current_balls_input")

        if st.button("実践開始 ▶"):
            #現在時刻を取得
            now = datetime.now()
            machine_info["current_balls"] = int(current_balls)
            machine_info["total_invest"] = 0
            # 🎯 実践開始時刻を保存
            machine_info["start_time"] = now.strftime("%H:%M")
            st.session_state.page = "main"
            st.rerun()

    # ====== ページ2：メイン画面 ======
    elif st.session_state.page == "main":
        st.title("📊 PachiLog - 実践記録")

        info = st.session_state.machine_info
        df = pd.DataFrame(st.session_state.records)

        # === 集計系 ===
        total_used_balls = df["使用玉数"].sum() if not df.empty else 0
        total_invest = info.get("total_invest", 0)
        current_balls = info.get("current_balls", 0)

        # === 平均回転率 ===
        if not df.empty and total_used_balls > 0:
            total_rotations = df["通常回転"].sum()
            rate_unit = 1000 if info.get("rate") == "1円" else 250
            avg_rotation = total_rotations / total_used_balls * rate_unit
        else:
            avg_rotation = 0

        # === メトリクス表示 ===
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("現金投資総額", f"{total_invest:,} 円")
        with col2:
            st.metric("現在持ち玉数", f"{current_balls:,} 玉")
        with col3:
            st.metric("平均回転率", f"{avg_rotation:.2f} 回/K")

        # === 💰 投資ボタン ===
        if st.button("500円"):
            selected_rate = info.get("rate", "4円")
            added_balls = 125 if selected_rate == "4円" else 500

            info["current_balls"] = current_balls + added_balls
            info["total_invest"] = total_invest + 500
            st.rerun()

        st.divider()
        
        col_title, col_button = st.columns([4, 1])
        with col_title:
            st.subheader("📋 記録一覧")

        with col_button:
            if st.button("➕ 行を追加", use_container_width=True):
                st.session_state.edit_index = None
                st.session_state.page = "add_row"
                st.rerun()

        # === 一覧表示 ===
        if not df.empty:
            header_cols = st.columns([2, 2, 2, 2, 2])
            for col, title in zip(header_cols, ["時間", "使用玉数", "打ち始め", "打ち終わり", "回転率"]):
                col.write(title)

            for i, record in enumerate(st.session_state.records):
                cols = st.columns([2, 2, 2, 2, 2])

                cols[0].write(record["時間"])
                cols[1].write(f"{record['使用玉数']:,} 玉")
                cols[2].write(record["打ち始め"])
                cols[3].write(record["打ち終わり"])
                cols[4].write(f"{record['回転率']:.2f}")
        else:
            st.info("まだデータがありません。")
            
        st.divider()
            
        if st.button("🏁 実践終了"):
            end_time = datetime.now()
            start_time = datetime.strptime(st.session_state.machine_info["start_time"], "%H:%M")
            elapsed = end_time - start_time

            # 実践時間（例: 3時間15分）
            hours, remainder = divmod(elapsed.seconds, 3600)
            minutes = remainder // 60
            elapsed_str = f"{hours}時間{minutes}分"

            # 集計データ作成
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

            st.success("✅ 実践結果を一覧に追加しました！")
            st.session_state.page = "select"  # ← ページ1の識別名に合わせて変更
            st.rerun()

    # ====== ページ3：行追加 ======
    elif st.session_state.page == "add_row":
        is_edit = st.session_state.get("edit_index") is not None
        st.title("➕ 行の追加")

        info = st.session_state.machine_info
        current_balls = int(info.get("current_balls", 0))

        # === 現在の持ち玉数入力 ===
        new_current_balls = st.number_input("現在の持ち玉数を入力", min_value=0, value=current_balls, step=50)

        # === 使用球数自動計算 ===
        used_balls = max(current_balls - new_current_balls, 0)
        st.write(f"使用玉数: {used_balls} 玉")

        # === 回転数入力 ===
        if is_edit:
            record = st.session_state.records[st.session_state.edit_index]
            start_rot_default = record["打ち始め"]
            end_rot_default = record["打ち終わり"]
        else:
            start_rot_default, end_rot_default = 0, 0

        start_rot = st.number_input("打ち始め回転数", min_value=0, step=1, value=start_rot_default)
        end_rot = st.number_input("打ち終わり回転数", min_value=0, step=1, value=end_rot_default)
        
        with st.expander("大当たり記録", expanded=False):
            # === 獲得玉数入力 ===
            gained_balls = st.number_input("獲得玉数を入力", min_value=0, step=50)
            #=== 最終持ち玉計算　===
            final_balls = new_current_balls + gained_balls
            st.write(f"✅ 確定後の持ち玉数: {final_balls} 玉")

        st.divider()

        # === 確定処理 ===
        if st.button("✅ 確定"):
            normal_rot = max(end_rot - start_rot, 0)
            selected_rate = info.get("rate", "4円")
            rate_unit = 250 if selected_rate == "4円" else 1000
            rotation_rate = (normal_rot / used_balls * rate_unit) if used_balls > 0 else 0

            now = datetime.now().strftime("%H:%M")

            new_record = {
                "時間": record["時間"] if is_edit else now,
                "使用玉数": used_balls,
                "打ち始め": start_rot,
                "打ち終わり": end_rot,
                "通常回転": normal_rot,
                "回転率": round(rotation_rate, 2),
            }

            if is_edit:
                st.session_state.records[st.session_state.edit_index] = new_record
            else:
                st.session_state.records.append(new_record)

            # ✅ 現在持ち玉更新
            st.session_state.machine_info["current_balls"] = final_balls
            
            st.success("✅ データを保存しました")
            st.session_state.page = "main"
            st.session_state.edit_index = None
            st.rerun()

        if st.button("⬅ 戻る"):
            st.session_state.page = "main"
            st.session_state.edit_index = None
            st.rerun()
    
# =============================
# 📐 タブ３：📕実践一覧
# ============================= 
with tab3:
    st.header("📊 実践一覧")

    if "records" not in st.session_state or len(st.session_state["records"]) == 0:
        st.info("まだ実践データがありません。")
    else:
        df = pd.DataFrame(st.session_state["records"])
        #df = df.sort_values(by="日付", ascending=True)
        st.dataframe(df, use_container_width=True)

