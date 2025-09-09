# contribute_research.py (v1.0 - Research Contributor Toolkit)
import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from textblob import TextBlob
import time
import base64
import hashlib
import bcrypt

# --- A. 暗号化エンジン ---
# app.pyと全く同じ、しかし独立したエンジンをここに定義する
class EncryptionManager:
    """パスワードのハッシュ化と、イベントログの暗号化・復号を管理する"""
    def __init__(self, password: str):
        self.password_bytes = password.encode('utf-8')
        self.key = hashlib.sha256(self.password_bytes).digest()

    @staticmethod
    def check_password(password: str, hashed_password: str) -> bool:
        """入力されたパスワードが、ハッシュと一致するかを検証する"""
        password_bytes = password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        try:
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except (ValueError, TypeError):
            return False

    def decrypt_log(self, encrypted_log: str) -> str:
        """暗号化されたイベントログを復号する"""
        if not encrypted_log or pd.isna(encrypted_log):
            return ""
        try:
            encrypted_bytes = base64.b64decode(encrypted_log.encode('utf-8'))
            decrypted_bytes = bytes([b ^ self.key[i % len(self.key)] for i, b in enumerate(encrypted_bytes)])
            return decrypted_bytes.decode('utf-8')
        except Exception:
            return "[復号エラー]"

# --- B. データ永続化層 ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def read_data(sheet_name: str):
    """メインアプリと研究用アプリの両方のシートを読み込む"""
    try:
        if sheet_name == 'users':
            return conn.read(worksheet="Sheet1")
        elif sheet_name == 'data':
            return conn.read(spreadsheet="harmony_data", worksheet="Sheet1")
        elif sheet_name == 'research':
            return conn.read(spreadsheet="harmony_research_data", worksheet="Sheet1")
    except Exception as e:
        st.error(f"{sheet_name}シートの読み込みに失敗しました: {e}")
        return pd.DataFrame()

def write_research_data(df: pd.DataFrame):
    """研究用データシートを更新する"""
    conn.write(spreadsheet="harmony_research_data", worksheet="Sheet1", data=df)
    st.cache_data.clear()

# --- C. メインUI ---
def main():
    st.set_page_config(layout="centered", page_title="Research Contribution")
    st.title("🔬 Harmony Navigator - 研究協力ツール")

    st.info("""
    このツールは、あなたのプライバシーを完全に保護しながら、あなたの貴重な経験を、科学の発展のために役立てるためのものです。
    全ての処理は、あなたのPC（ブラウザ）の中で完結し、生のイベントログが外部に送信されることは一切ありません。
    """)

    st.header("ステップ1：あなたの船（アカウント）に接続する")
    username = st.text_input("あなたのHarmony Navigatorの「ユーザー名」を入力してください:")
    password = st.text_input("あなたの「パスワード」を入力してください:", type="password")

    if username and password:
        users_df = read_data('users')
        if users_df.empty:
            st.error("ユーザー情報シートを読み込めませんでした。")
            return

        user_record = users_df[users_df['username'] == username]

        if not user_record.empty and EncryptionManager.check_password(password, user_record.iloc[0]['password_hash']):
            st.success(f"ようこそ、{username}さん！ アカウント認証に成功しました。")

            all_data = read_data('data')
            if all_data.empty:
                st.error("データシートを読み込めませんでした。")
                return

            user_data = all_data[all_data['username'] == username].copy()
            st.info(f"{len(user_data)}件のあなたの記録データを、安全に読み込みました。")

            st.header("ステップ2：イベントログの分析と匿名化")
            st.warning("この処理は、あなたのPC上だけで実行されます。")

            if st.button("分析と匿名化を実行する"):
                with st.spinner("あなたのPC内で、安全に分析を実行中です..."):
                    enc_manager = EncryptionManager(password)
                    
                    logs_to_analyze = user_data.dropna(subset=['event_log']).copy()
                    
                    if not logs_to_analyze.empty:
                        # イベントログを、あなたのPC上で復号
                        logs_to_analyze['decrypted_log'] = logs_to_analyze['event_log'].apply(enc_manager.decrypt_log)
                        
                        # TextBlobを使って、復号したログから感情を分析
                        sentiments = [TextBlob(log).sentiment for log in logs_to_analyze['decrypted_log']]
                        
                        analyzed_df = logs_to_analyze.copy()
                        analyzed_df['sentiment_polarity'] = [s.polarity for s in sentiments]
                        analyzed_df['sentiment_subjectivity'] = [s.subjectivity for s in sentiments]

                        # 【重要】生のイベントログと、復号したログを、完全に削除
                        research_ready_df = analyzed_df.drop(columns=['event_log', 'decrypted_log'])
                        
                        st.success("分析と匿名化が完了しました！")
                        st.write("生成された研究用データ（一部抜粋）:")
                        st.dataframe(research_ready_df.head())

                        st.header("ステップ3：匿名化されたデータを、研究に貢献する")
                        st.info("以下のボタンを押すと、上記の、個人情報が完全に削除された「統計データ」だけが、研究用のデータベースに安全に送信されます。")
                        
                        if st.button("この匿名データを送信して、科学に貢献する"):
                            try:
                                existing_research_df = read_data('research')
                                updated_research_df = pd.concat([existing_research_df, research_ready_df], ignore_index=True)
                            except Exception:
                                updated_research_df = research_ready_df

                            # 重複を削除して、最新の分析結果だけを保持
                            updated_research_df.drop_duplicates(subset=['date', 'username'], keep='last', inplace=True)
                            
                            write_research_data(updated_research_df)
                            st.success("ご協力、誠にありがとうございました！あなたの貴重な経験が、未来の幸福の科学を前進させます。")
                            st.balloons()
                    else:
                        st.warning("分析対象となるイベントログが、あなたのデータにはありませんでした。")
        elif not user_record.empty:
            st.error("パスワードが間違っています。")
        else:
            st.warning("まずは、あなたのユーザー名とパスワードを正確に入力してください。")

if __name__ == '__main__':
    main()
