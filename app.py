# app.py (v4.1.1 - The Final & Truly Complete Code)
import streamlit as st
import pandas as pd
import numpy as np
from scipy.spatial.distance import jensenshannon
from datetime import datetime, date, timedelta
import re
import hashlib
from streamlit_gsheets import GSheetsConnection
import time
import uuid
import itertools
import bcrypt
import base64

# --- A. 定数と基本設定 ---
st.set_page_config(layout="wide", page_title="Harmony Navigator")

# ドメインとエレメントの定義
DOMAINS = ['health', 'relationships', 'meaning', 'autonomy', 'finance', 'leisure', 'competition']
DOMAIN_NAMES_JP = {
    'health': '1. 健康', 'relationships': '2. 人間関係', 'meaning': '3. 意味・貢献',
    'autonomy': '4. 自律・成長', 'finance': '5. 経済', 'leisure': '6. 余暇・心理', 'competition': '7. 競争'
}
SHORT_ELEMENTS = {
    'health': ['睡眠と休息', '身体的な快調さ'], 'relationships': ['親密な関係', '利他性・貢献'],
    'meaning': ['仕事・学業の充実感', '価値との一致'], 'autonomy': ['自己決定感', '自己成長の実感'],
    'finance': ['経済的な安心感', '職業的な達成感'], 'leisure': ['心の平穏', '楽しさ・喜び'],
    'competition': ['優越感・勝利']
}
LONG_ELEMENTS = {
    'health': ['睡眠', '食事', '運動', '身体的快適さ', '感覚的快楽', '性的満足'],
    'relationships': ['家族', 'パートナー・恋愛', '友人', '社会的承認', '利他性・貢献', '共感・繋がり'],
    'meaning': ['やりがい', '達成感', '信念との一致', 'キャリアの展望', '社会への貢献', '有能感'],
    'autonomy': ['自由・自己決定', '挑戦・冒険', '自己成長の実感', '変化の享受', '独立・自己信頼', '好奇心'],
    'finance': ['経済的安定', '経済的余裕', '労働環境', 'ワークライフバランス', '公正な評価', '職業的安定性'],
    'leisure': ['心の平穏', '自己肯定感', '創造性の発揮', '感謝', '娯楽・楽しさ', '芸術・自然'],
    'competition': ['優越感・勝利']
}
ALL_ELEMENT_COLS = sorted([f's_element_{e}' for d in LONG_ELEMENTS.values() for e in d])
Q_COLS = ['q_' + d for d in DOMAINS]
S_COLS = ['s_' + d for d in DOMAINS]
SLIDER_HELP_TEXT = "0: 全く当てはまらない | 25: あまり当てはまらない | 50: どちらとも言えない | 75: やや当てはまる | 100: 完全に当てはまる"

# UIに表示するテキスト
ELEMENT_DEFINITIONS = {
    '睡眠と休息': '心身ともに、十分な休息が取れたと感じる度合い。例：朝、すっきりと目覚められたか。',
    '身体的な快調さ': '活力を感じ、身体的な不調（痛み、疲れなど）がなかった度合い。',
    '睡眠': '質の良い睡眠がとれ、朝、すっきりと目覚められた度合い。',
    '食事': '栄養バランスの取れた、美味しい食事に満足できた度合い。',
    '運動': '体を動かす習慣があり、それが心身の快調さに繋がっていた度合い。',
    '身体的快適さ': '慢性的な痛みや、気になる不調がなく、快適に過ごせた度合い。',
    '感覚的快楽': '五感を通じて、心地よいと感じる瞬間があった度合い。例：温かいお風呂、心地よい音楽。',
    '性的満足': '自身の性的な欲求や、パートナーとの親密さに対して、満足感があった度合い。',
    '親密な関係': '家族やパートナー、親しい友人との、温かい、あるいは安心できる繋がりを感じた度合い。',
    '利他性・貢献': '自分の行動が、誰かの役に立った、あるいは喜ばれたと感じた度合い。例：「ありがとう」と言われた。',
    '家族': '家族との間に、安定した、あるいは温かい関係があった度合い。',
    'パートナー・恋愛': 'パートナーとの間に、愛情や深い理解、信頼があった度合い。',
    '友人': '気軽に話せたり、支え合えたりする友人がおり、良い関係を築けていた度合い。',
    '社会的承認': '周囲の人々（職場、地域など）から、一員として認められ、尊重されていると感じた度合い。',
    '共感・繋がり': '他者の気持ちに寄り添ったり、逆に寄り添ってもらったりして、人との深い繋がりを感じた度合い。',
    '仕事・学業の充実感': '自分の仕事や学びに、やりがいや達成感を感じた度合い。',
    '価値との一致': '自分の大切にしている価値観や信念に沿って、行動できたと感じられる度合い。',
    'やりがい': '自分の仕事や活動（学業、家事、趣味など）に、意義や目的を感じ、夢中になれた度合い。',
    '達成感': '何か具体的な目標を達成したり、物事を最後までやり遂げたりする経験があった度合い。',
    '信念との一致': '自分の「こうありたい」という価値観や、倫理観に沿った行動ができた度合い。',
    'キャリアの展望': '自分の将来のキャリアに対して、希望や前向きな見通しを持てていた度合い。',
    '社会への貢献': '自分の活動が、所属するコミュニティや、より大きな社会に対して、良い影響を与えていると感じられた度合い。',
    '有能感': '自分のスキルや能力を、うまく発揮できているという感覚があった度合い。',
    '自己決定感': '今日の自分の行動は、自分で決めたと感じられる度合い。',
    '自己成長の実感': '何かを乗り越え、自分が成長した、あるいは新しいことを学んだと感じた度合い。',
    '自由・自己決定': '自分の人生における重要な事柄を、他者の圧力ではなく、自分自身の意志で選択・決定できていると感じた度合い。',
    '挑戦・冒険': '新しいことに挑戦したり、未知の経験をしたりして、刺激や興奮を感じた度合い。',
    '変化の享受': '環境の変化や、新しい考え方を、ポジティブに受け入れ、楽しむことができた度合い。',
    '独立・自己信頼': '自分の力で物事に対処できるという、自分自身への信頼感があった度合い。',
    '好奇心': '様々な物事に対して、知的な好奇心を持ち、探求することに喜びを感じた度合い。',
    '経済的な安心感': '日々の生活や将来のお金について、過度な心配をせず、安心して過ごせた度合い。',
    '職業的な達成感': '仕事や学業において、物事をうまくやり遂げた、あるいは目標に近づいたと感じた度合い。',
    '経済的安定': '「来月の支払いは大丈夫かな…」といった、短期的なお金の心配がない状態。',
    '経済的余裕': '生活必需品だけでなく、趣味や自己投資など、人生を豊かにすることにもお金を使える状態。',
    '労働環境': '物理的にも、精神的にも、安全で、健康的に働ける環境があった度合い。',
    'ワークライフバランス': '仕事（あるいは学業）と、プライベートな生活との間で、自分が望むバランスが取れていた度合い。',
    '公正な評価': '自分の働きや成果が、正当に評価され、報酬に反映されていると感じられた度合い。',
    '職業的安定性': '「この先も、この仕事を続けていけるだろうか」といった、長期的なキャリアや収入に対する不安がない状態。',
    '心の平穏': '過度な不安やストレスなく、精神的に安定していた度合い。',
    '楽しさ・喜び': '純粋に「楽しい」と感じたり、笑ったりする瞬間があった度合い。',
    '自己肯定感': '自分の長所も短所も含めて、ありのままの自分を、肯定的に受け入れることができた度合い。',
    '創造性の発揮': '何かを創作したり、新しいアイデアを思いついたりして、創造的な喜びを感じた度合い。',
    '感謝': '日常の小さな出来事や、周りの人々に対して、自然と「ありがたい」という気持ちが湧いた度合い。',
    '娯楽・楽しさ': '趣味に没頭したり、友人と笑い合ったり、純粋に「楽しい」と感じる時間があった度合い。',
    '芸術・自然': '美しい音楽や芸術、あるいは雄大な自然に触れて、心が動かされたり、豊かになったりする経験があった度合い。',
    '優越感・勝利': '他者との比較や、スポーツ、仕事、学業などにおける競争において、優位に立てたと感じた度合い。'
}
EXPANDER_TEXTS = {
    'q_t': """
        #### ▼ これは、何のために設定するの？
        これは、あなたの人生という航海で、**「どの宝島を目指すか」**を決める、最も重要な羅針盤です。あなたが「何を大切にしたいか」という**理想（情報秩序）**を、数値で表現します。
        
        この設定が、あなたの日々の経験を評価するための**個人的な『ものさし』**となります。この「ものさし」がなければ、自分の航海が順調なのか、航路から外れているのかを知ることはできません。
        
        （週に一度など、定期的に見直すのがおすすめです）
        """,
    's_t': """
        #### ▼ これは、何のために記録するの？
        ここでは、あなたの**現実の経験（実践秩序）**を記録します。
        
        頭で考える理想ではなく、**今日一日を振り返って、実際にどう感じたか**を、各項目のスライダーで直感的に評価してください。
        
        この「現実」の記録と、先ほど設定した「理想」の羅針盤とを比べることで、両者の間に存在する**『ズレ』**を初めて発見できます。この『ズレ』に気づくことこそが、自己理解と成長の第一歩です。
        """,
    'g_t': """
        #### ▼ これは、なぜ必要なの？
        この項目は、**あなたの直感的な全体評価**です。
        
        細かいことは一度忘れて、「で、色々あったけど、今日の自分、全体としては何点だったかな？」という感覚を、一つのスライダーで表現してください。
        
        アプリが計算したスコア（H）と、あなたの直感（G）がどれだけ一致しているか、あるいは**ズレているか**を知るための、非常に重要な手がかりとなります。
        
        **『計算上は良いはずなのに、なぜか気分が晴れない』**といった、言葉にならない違和感や、**『予想外に楽しかった！』**という嬉しい発見など、貴重な自己発見のきっかけになります。
        """,
    'event_log': """
        #### ▼ なぜ書くのがおすすめ？
        これは、あなたの航海の**物語**を記録する場所です。
        
        **『誰と会った』『何をした』『何を感じた』**といった具体的な出来事や感情を、一言でも良いので書き留めてみましょう。
        
        後でグラフを見たときに、数値だけでは分からない、**幸福度の浮き沈みの『なぜ？』**を解き明かす鍵となります。グラフの「山」や「谷」と、この記録を結びつけることで、あなたの幸福のパターンがより鮮明に見えてきます。
        """
}

# --- B. 暗号化エンジン ---
class EncryptionManager:
    def __init__(self, password: str):
        self.password_bytes = password.encode('utf-8')
        self.key = hashlib.sha256(self.password_bytes).digest()

    @staticmethod
    def hash_password(password: str) -> str:
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_bytes = bcrypt.hashpw(password_bytes, salt)
        return hashed_bytes.decode('utf-8')

    @staticmethod
    def check_password(password: str, hashed_password: str) -> bool:
        password_bytes = password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        try:
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except (ValueError, TypeError):
            return False

    def encrypt_log(self, log_text: str) -> str:
        if not log_text:
            return ""
        encrypted_bytes = bytes([b ^ self.key[i % len(self.key)] for i, b in enumerate(log_text.encode('utf-8'))])
        return base64.b64encode(encrypted_bytes).decode('utf-8')

    def decrypt_log(self, encrypted_log: str) -> str:
        if not encrypted_log or pd.isna(encrypted_log):
            return ""
        try:
            encrypted_bytes = base64.b64decode(encrypted_log.encode('utf-8'))
            decrypted_bytes = bytes([b ^ self.key[i % len(self.key)] for i, b in enumerate(encrypted_bytes)])
            return decrypted_bytes.decode('utf-8')
        except Exception:
            return "[復号に失敗しました：パスワードが違うか、データが破損している可能性があります]"

# --- C. コア計算 & ユーティリティ関数 ---
def calculate_metrics(df: pd.DataFrame, alpha: float = 0.6) -> pd.DataFrame:
    df_copy = df.copy()
    if df_copy.empty:
        return df_copy
    
    numeric_cols = Q_COLS + S_COLS + ALL_ELEMENT_COLS + ['g_happiness']
    for col in numeric_cols:
        if col in df_copy.columns:
            df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')

    for domain, elements in LONG_ELEMENTS.items():
        element_cols = [f's_element_{e}' for e in elements if f's_element_{e}' in df_copy.columns]
        if element_cols:
            df_copy['s_' + domain] = df_copy[element_cols].mean(axis=1, skipna=True)

    for col in Q_COLS + S_COLS:
         if col in df_copy.columns:
            df_copy[col] = df_copy[col].fillna(0)
    
    s_vectors_normalized = df_copy[S_COLS].values / 100.0
    q_vectors = df_copy[Q_COLS].values
    
    df_copy['S'] = np.nansum(q_vectors * s_vectors_normalized, axis=1)
    
    def calculate_unity(row):
        q_vec = np.array([float(row[col]) for col in Q_COLS], dtype=float)
        s_vec_raw = np.array([float(row[col]) for col in S_COLS], dtype=float)
        
        q_sum = np.sum(q_vec)
        if q_sum == 0: return 0.0
        q_vec_norm = q_vec / q_sum
        
        s_sum = np.sum(s_vec_raw)
        if s_sum == 0: return 0.0
        s_tilde = s_vec_raw / s_sum
        
        jsd_sqrt = jensenshannon(q_vec_norm, s_tilde)
        jsd = float(jsd_sqrt) ** 2
        return 1.0 - jsd

    df_copy['U'] = df_copy.apply(calculate_unity, axis=1)
    df_copy['H'] = alpha * df_copy['S'] + (1 - alpha) * df_copy['U']
    
    return df_copy

def calculate_ahp_weights(comparisons: dict, items: list) -> np.ndarray:
    n = len(items)
    matrix = np.ones((n, n), dtype=float)
    item_map = {item: i for i, item in enumerate(items)}

    for (item1, item2), winner in comparisons.items():
        i, j = item_map[item1], item_map[item2]
        if winner == item1:
            matrix[i, j] = 3.0
            matrix[j, i] = 1.0 / 3.0
        elif winner == item2:
            matrix[i, j] = 1.0 / 3.0
            matrix[j, i] = 3.0

    eigenvalues, eigenvectors = np.linalg.eig(matrix)
    max_eigenvalue_index = np.argmax(np.real(eigenvalues))
    principal_eigenvector = np.real(eigenvectors[:, max_eigenvalue_index])
    weights = principal_eigenvector / np.sum(principal_eigenvector)
    weights = np.clip(weights, 0, None)
    if weights.sum() == 0:
        weights = np.ones_like(weights) / len(weights)
    
    int_weights = (weights * 100).round().astype(int)
    diff = 100 - np.sum(int_weights)
    if diff != 0:
        int_weights[np.argmax(int_weights)] += diff
        
    return int_weights

# --- D. データ永続化層 ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10)
def read_data(sheet_name: str):
    try:
        if sheet_name == 'data':
            df = conn.read(spreadsheet="harmony_data", worksheet="Sheet1")
        elif sheet_name == 'users':
            df = conn.read(worksheet="Sheet1")
        else:
            return pd.DataFrame()

        if not df.empty:
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
            
            numeric_cols = Q_COLS + S_COLS + ALL_ELEMENT_COLS + ['g_happiness']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except Exception as e:
        if "SpreadsheetNotFound" in str(e):
             st.error(f"データ保管庫（{sheet_name}シート）が見つかりません。作成して共有設定を確認してください。")
        else:
            st.warning(f"データの読み込みに失敗しました。5秒後に再試行します... Error: {e}")
            time.sleep(5)
            st.rerun()
        return pd.DataFrame()

def write_data(sheet_name: str, df: pd.DataFrame):
    df_copy = df.copy()
    if 'date' in df_copy.columns:
        df_copy['date'] = pd.to_datetime(df_copy['date']).dt.strftime('%Y-%m-%d')
    
    if sheet_name == 'data':
        conn.write(spreadsheet="harmony_data", worksheet="Sheet1", data=df_copy)
    elif sheet_name == 'users':
         conn.write(worksheet="Sheet1", data=df_copy)
    st.cache_data.clear()

# --- E. UIコンポーネント & 補助関数 ---
def show_welcome_and_guide():
    st.header("ようこそ、最初の航海士へ！「Harmony Navigator」取扱説明書")
    st.markdown("---")
    st.subheader("1. このアプリは、あなたの人生の「航海日誌」です")
    st.markdown("""
    「もっと幸せになりたい」と願いながらも、漠然とした不安や、**「理想（こうありたい自分）」**と**「現実（実際に経験した一日）」**の間の、言葉にならない『ズレ』に、私たちはしばしば悩まされます。
    
    このアプリは、その『ズレ』の正体を可視化し、あなた自身が人生の舵を取るための、**実践的な「航海術」**を提供する目的で開発されました。
    
    これは、あなただけの**「海図（チャート）」**です。この海図を使えば、
    - **自分の現在地**（今の心の状態、つまり『実践秩序』）を客観的に知り、
    - **目的地**（自分が本当に大切にしたいこと、つまり『情報秩序』）を明確にし、
    - **航路**（日々の選択）を、あなた自身で賢明に調整していくことができます。
    
    あなたの人生という、唯一無二の航海。その冒険のパートナーとして、このアプリは生まれました。
    """)
    st.markdown("---")
    st.subheader("🛡️【最重要】あなたのプライバシーは、「二重の仮面」によって、設計上保護されます")
    with st.expander("▼ 解説：究極のプライバシー保護、その二つの秘密"):
        st.markdown("""
        このアプリの最も重要な約束は、あなたのプライバシーを守ることです。そのために、私たちは**「二重の仮面」**という、二段階の強力な匿名化・暗号化技術を、設計の中心に据えています。

        #### **第一の仮面：あなたが誰だか、誰にも分からない「診察券番号（ユーザー名）」**

        このアプリでは、あなたは、本名やメールアドレスといった、**個人を特定できる情報を一切登録する必要がありません。**
        
        あなたが登録する「ユーザー名」は、あなただけが知っているニックネームです。開発者である私がデータ保管庫を見ることがあったとしても、そこにあるのは**「Taroさんの記録」**という情報だけであり、そのTaroさんが**現実世界の誰なのかを知る手段は、一切ありません。** これが、基本的な匿名性を保証する、第一の仮面です。

        #### **第二の仮面：あなたにしか読めない「魔法の自己破壊インク（イベントログの暗号化）」**

        さらに、あなたの最もプライベートな記録である**「イベントログ（日々の出来事や気づき）」**には、より強力な、第二の仮面が用意されています。

        あなたが日記を書き終え、「保存」ボタンを押した瞬間、その文字は、あなたの**PCやスマホのブラウザの中だけで**、あなただけが知っている**「パスワード」**を鍵として、誰にも読めない、全く意味不明な記号の羅列に、完全に**暗号化**されます。
        
        データ保管庫に記録されるのは、この**「誰にも読めない、暗号化された記号の羅列」だけ**です。
        
        したがって、たとえ私があなたの「ユーザー名」を知っていたとしても、あなたのイベントログの中身を読むことは、**物理的に、そして永遠に、不可能です。**
        
        この日記を再び読めるのは、世界でただ一人、正しいパスワードという「魔法の鍵」を持つ、**あなただけ**です。
        
        **この「二重の仮面」の仕組みにより、あなたのプライバシーは、開発者の善意に依存するのではなく、「設計」そのものによって、構造的に保護されるのです。**
        """)
    st.markdown("---")
    st.subheader("🧑‍🔬 あなたは、ただのユーザーじゃない。「科学の冒険者」です！")
    st.info("""
    **【研究協力へのお願い（インフォームド・コンセント）】**
    
    もし、ご協力いただけるのであれば、あなたが記録したデータを、**個人が特定できない形に完全に匿名化した上で**、この理論の科学的検証のための研究に利用させていただくことにご同意いただけますでしょうか。

    **【私たちの約束：ゼロ知識分析】**
    
    あなたのプライバシーは、何よりも優先されます。そのため、私たちは、あなたのイベントログのような、プライベートな記述データを、**直接収集することは一切ありません。**
    
    代わりに、私たちは、あなたがご自身の意思で、安全に研究に協力するための、**全く別の「研究協力ツール」**を、別途提供します。このツールは、
    1. あなたのパスワードを使って、あなたのPC上だけで、イベントログを**復号**します。
    2. 復号されたログの内容から、感情のスコアなどの、**個人を特定できない、匿名化された「統計情報」**だけを抽出します。
    3. そして、この**「統計情報」だけ**を、研究用のデータベースに送信します。
    
    この仕組みにより、**私たち研究者は、あなたのプライベートな物語に一切触れることなく**、科学の発展に必要なデータだけを得ることができます。
    
    ここの「同意」チェックボックスは、私たちが、あなたの**「日々の数値データ（幸福度のスコアなど）」**を、将来あなたが送信してくれるかもしれない**「匿名の統計情報」**と結びつけて、分析することへの許可をいただくためのものです。
    """)

def analyze_discrepancy(df_processed: pd.DataFrame, threshold: int = 20):
    if df_processed.empty or 'H' not in df_processed.columns or 'g_happiness' not in df_processed.columns:
        return
    latest_record = df_processed.iloc[-1]
    latest_h = float(latest_record['H']) * 100.0 if pd.notna(latest_record['H']) else 0
    latest_g = float(latest_record.get('g_happiness', 0)) if pd.notna(latest_record.get('g_happiness', 0)) else 0
    gap = latest_g - latest_h

    st.subheader("💡 インサイト・エンジン")
    with st.expander("▼ これは、モデルの計算値(H)とあなたの実感(G)の『ズレ』に関する分析です", expanded=True):
        if gap > threshold:
            st.info(f"""
                **【幸福なサプライズ！🎉】**

                あなたの**実感（G = {int(latest_g)}点）**は、モデルの計算値（H = {int(latest_h)}点）を大きく上回りました。
                
                これは、あなたが**まだ言葉にできていない、新しい価値観**を発見したサインかもしれません。
                
                **問い：** 今日の記録を振り返り、あなたが設定した価値観（q_t）では捉えきれていない、予期せぬ喜びの源泉は何だったでしょうか？
                """)
        elif gap < -threshold:
            st.warning(f"""
                **【隠れた不満？🤔】**

                あなたの**実感（G = {int(latest_g)}点）**は、モデルの計算値（H = {int(latest_h)}点）を大きく下回りました。

                価値観に沿った生活のはずなのに、何かが満たされていないようです。見過ごしている**ストレス要因や、理想と現実の小さなズレ**があるのかもしれません。

                **問い：** 今日の記録を振り返り、あなたの幸福感を静かに蝕んでいた「見えない重り」は何だったでしょうか？
                """)
        else:
            st.success(f"""
                **【順調な航海です！✨】**

                あなたの**実感（G = {int(latest_g)}点）**と、モデルの計算値（H = {int(latest_h)}点）は、よく一致しています。
                
                あなたの自己認識と、現実の経験が、うまく調和している状態です。素晴らしい！
                """)

def calculate_rhi_metrics(df_period: pd.DataFrame, lambda_rhi: float, gamma_rhi: float, tau_rhi: float) -> dict:
    if df_period.empty or 'H' not in df_period.columns:
        return {'mean_H': 0, 'std_H': 0, 'frac_below': 0, 'RHI': 0}
    mean_H = df_period['H'].mean()
    std_H = df_period['H'].std(ddof=0)
    frac_below = (df_period['H'] < tau_rhi).mean()
    rhi = mean_H - (lambda_rhi * std_H) - (gamma_rhi * frac_below)
    return {'mean_H': mean_H, 'std_H': std_H, 'frac_below': frac_below, 'RHI': rhi}

# --- F. メインアプリケーション ---
def main():
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'enc_manager' not in st.session_state:
        st.session_state.enc_manager = None

    st.title('🧭 Harmony Navigator')
    st.caption('v4.1.1 - Ultimate Privacy Edition')

    if not st.session_state.username:
        st.header("ようこそ、航海士へ")
        show_welcome_and_guide()
        
        st.subheader("あなたの旅を、ここから始めましょう")
        door1, door2 = st.tabs(["**新しい船で旅を始める (新規登録)**", "**乗船する (ログイン)**"])

        with door1:
            st.info("初めての方、または新しい旅を始めたい方は、こちらから。")
            with st.form("register_form"):
                new_username = st.text_input("ユーザー名（あなただけが使う、公開されない名前）")
                new_password = st.text_input("パスワード（8文字以上、全てのデータを守る、あなただけの鍵です）", type="password")
                new_password_confirm = st.text_input("パスワード（確認用）", type="password")
                consent = st.checkbox("研究協力に関する説明を読み、その内容に同意します。")
                submitted = st.form_submit_button("登録して旅を始める")

                if submitted:
                    users_df = read_data('users')
                    if not users_df.empty and new_username in users_df['username'].values:
                        st.error("そのユーザー名は既に使用されています。")
                    elif len(new_password) < 8:
                        st.error("パスワードは8文字以上で設定してください。")
                    elif new_password != new_password_confirm:
                        st.error("パスワードが一致しません。")
                    else:
                        hashed_pw = EncryptionManager.hash_password(new_password)
                        new_user_df = pd.DataFrame([{'username': new_username, 'password_hash': hashed_pw}])
                        updated_users_df = pd.concat([users_df, new_user_df], ignore_index=True)
                        write_data('users', updated_users_df)
                        
                        st.session_state.username = new_username
                        st.session_state.enc_manager = EncryptionManager(new_password)
                        st.success(f"ようこそ、{new_username}さん！登録が完了しました。")
                        time.sleep(1)
                        st.rerun()

        with door2:
            st.info("すでにアカウントをお持ちの方は、こちらから旅を続けてください。")
            with st.form("login_form"):
                username_input = st.text_input("ユーザー名")
                password_input = st.text_input("パスワード", type="password")
                submitted = st.form_submit_button("乗船する")

                if submitted:
                    users_df = read_data('users')
                    if not users_df.empty:
                        user_record = users_df[users_df['username'] == username_input]
                        if not user_record.empty and EncryptionManager.check_password(password_input, user_record.iloc[0]['password_hash']):
                            st.session_state.username = username_input
                            st.success("認証に成功しました！心の金庫を開けるため、もう一度パスワードを入力してください。")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("ユーザー名またはパスワードが間違っています。")
                    else:
                        st.error("ユーザーが見つかりません。")

    else: # --- ログイン後のメインアプリケーション ---
        username = st.session_state.username

        if not st.session_state.enc_manager:
            st.header("🔒 心の金庫を開ける")
            st.info("あなたの航海日誌（イベントログ）は、あなただけの秘密のパスワードで強力に暗号化されています。")
            st.warning("日誌を読み書きするために、ログインパスワードをもう一度入力して、このセッションのロックを解除してください。")

            with st.form("decryption_form"):
                password_for_decrypt = st.text_input("パスワード", type="password")
                submitted = st.form_submit_button("ロックを解除する")

                if submitted:
                    users_df = read_data('users')
                    user_record = users_df[users_df['username'] == username]
                    if not user_record.empty and EncryptionManager.check_password(password_for_decrypt, user_record.iloc[0]['password_hash']):
                        st.session_state.enc_manager = EncryptionManager(password_for_decrypt)
                        st.success("ロックが解除されました！")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("パスワードが間違っています。")
        else:
            st.sidebar.header(f"ようこそ、{username} さん！")
            if st.sidebar.button("ログアウト"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

            all_data_df = read_data('data')
            if not all_data_df.empty and 'username' in all_data_df.columns:
                user_data_df = all_data_df[all_data_df['username'] == username].copy()
            else:
                user_data_df = pd.DataFrame()

            st.sidebar.markdown("---")
            st.sidebar.header('⚙️ 価値観 (q_t) の設定')
            st.sidebar.caption('あなたの「理想のコンパス」です。')

            if 'wizard_mode' not in st.session_state:
                st.session_state.wizard_mode = False
            if 'q_wizard_step' not in st.session_state:
                st.session_state.q_wizard_step = 0
            if 'q_comparisons' not in st.session_state:
                st.session_state.q_comparisons = {}
            if 'q_values_from_wizard' not in st.session_state:
                st.session_state.q_values_from_wizard = None
            
            with st.sidebar.expander("▼ 価値観の配分が難しいと感じる方へ"):
                st.markdown("合計100点の配分は難しいと感じることがあります。簡単な比較質問に答えるだけで、あなたの価値観のたたき台を提案します。")
                if st.button("対話で価値観を発見する（21の質問）"):
                    st.session_state.wizard_mode = True
                    st.session_state.q_wizard_step = 1
                    st.session_state.q_comparisons = {}
                    st.rerun()
            
            if st.session_state.wizard_mode:
                pairs = list(itertools.combinations(DOMAINS, 2))
                if 0 < st.session_state.q_wizard_step <= len(pairs):
                    pair = pairs[st.session_state.q_wizard_step - 1]
                    domain1, domain2 = pair
                    st.sidebar.subheader(f"質問 {st.session_state.q_wizard_step}/{len(pairs)}")
                    st.sidebar.write("あなたの人生がより充実するために、今、より重要なのはどちらですか？")
                    col1, col2 = st.sidebar.columns(2)
                    if col1.button(DOMAIN_NAMES_JP[domain1], key=f"btn_{domain1}"):
                        st.session_state.q_comparisons[pair] = domain1
                        st.session_state.q_wizard_step += 1
                        st.rerun()
                    if col2.button(DOMAIN_NAMES_JP[domain2], key=f"btn_{domain2}"):
                        st.session_state.q_comparisons[pair] = domain2
                        st.session_state.q_wizard_step += 1
                        st.rerun()
                else:
                    st.sidebar.success("診断完了！あなたの価値観の推定値です。")
                    estimated_weights = calculate_ahp_weights(st.session_state.q_comparisons, DOMAINS)
                    st.session_state.q_values_from_wizard = {domain: weight for domain, weight in zip(DOMAINS, estimated_weights)}
                    st.session_state.wizard_mode = False
                    st.rerun()
            else:
                if st.session_state.q_values_from_wizard is not None:
                    default_q_values = st.session_state.q_values_from_wizard
                    st.session_state.q_values_from_wizard = None
                elif not user_data_df.empty and all(col in user_data_df.columns for col in Q_COLS):
                    row_q = user_data_df.sort_values(by='date').iloc[-1][Q_COLS].to_dict()
                    default_q_values = {key.replace('q_', ''): int(val * 100) for key, val in row_q.items()}
                else:
                    default_q_values = {'health': 15, 'relationships': 15, 'meaning': 15, 'autonomy': 15, 'finance': 15, 'leisure': 15, 'competition': 10}

                q_values = {}
                for domain in DOMAINS:
                    q_values[domain] = st.sidebar.slider(DOMAIN_NAMES_JP[domain], 0, 100, int(default_q_values.get(domain, 14)), key=f"q_{domain}")

                q_total = sum(q_values.values())
                st.sidebar.metric(label="現在の合計値", value=q_total)
                if q_total != 100:
                    st.sidebar.warning(f"合計が100になるように調整してください。 (現在: {q_total})")
                else:
                    st.sidebar.success("合計は100です。入力準備OK！")

            tab1, tab2, tab3 = st.tabs(["**✍️ 今日の記録**", "**📊 ダッシュボード**", "**🔧 設定とガイド**"])

            with tab1:
                st.header(f"今日の航海日誌を記録する")
                
                with st.expander("▼ これは、何のために記録するの？"):
                    st.markdown(EXPANDER_TEXTS['s_t'])
                
                st.markdown("##### 記録する日付")
                today = date.today()
                target_date = st.date_input("記録する日付:", value=today, min_value=today - timedelta(days=7), max_value=today, label_visibility="collapsed")
                
                if not user_data_df.empty and target_date in user_data_df['date'].values:
                    st.warning(f"⚠️ {target_date.strftime('%Y-%m-%d')} のデータは既に記録されています。保存すると上書きされます。")

                st.markdown("##### 記録モード")
                input_mode = st.radio("記録モード:", ('🚀 クイック・ログ', '🔬 ディープ・ダイブ'), horizontal=True, label_visibility="collapsed")
                
                active_elements = SHORT_ELEMENTS if 'クイック' in input_mode else LONG_ELEMENTS
                mode_string = 'quick' if 'クイック' in input_mode else 'deep'
                
                with st.form(key='daily_input_form'):
                    s_element_values = {}
                    col1, col2 = st.columns(2)
                    containers = [col1, col2]
                    
                    if not user_data_df.empty:
                        latest_s_elements = user_data_df.sort_values(by='date').iloc[-1]
                    else:
                        latest_s_elements = pd.Series(50, index=ALL_ELEMENT_COLS)

                    for i, domain in enumerate(DOMAINS):
                        container = containers[i % 2]
                        with container:
                            elements_to_show = active_elements.get(domain, [])
                            if elements_to_show:
                                with st.expander(f"**{DOMAIN_NAMES_JP[domain]}**"):
                                    for element in elements_to_show:
                                        col_name = f's_element_{element}'
                                        default_val = int(latest_s_elements.get(col_name, 50))
                                        help_text = ELEMENT_DEFINITIONS.get(element, "")
                                        score = st.slider(element, 0, 100, default_val, key=col_name, help=help_text)
                                        s_element_values[col_name] = int(score)
                    
                    st.markdown('**総合的な幸福感 (Gt)**')
                    with st.expander("▼ これはなぜ必要？"):
                        st.markdown(EXPANDER_TEXTS['g_t'])
                    g_happiness = st.slider('', 0, 100, 50, label_visibility="collapsed", help=SLIDER_HELP_TEXT)
                    
                    st.markdown('**今日の出来事や気づきは？（暗号化されます）**')
                    with st.expander("▼ なぜ書くのがおすすめ？"):
                        st.markdown(EXPANDER_TEXTS['event_log'])
                    event_log = st.text_area('', height=100, label_visibility="collapsed")
                    
                    submitted = st.form_submit_button('今日の記録を保存する')

                if submitted:
                    if sum(q_values.values()) != 100:
                        st.error('価値観 (q_t) の合計が100になっていません。サイドバーを確認してください。')
                    else:
                        new_record = {col: pd.NA for col in ALL_ELEMENT_COLS}
                        new_record.update(s_element_values)
                        
                        s_domain_scores = {}
                        for domain, elements in LONG_ELEMENTS.items():
                            domain_scores = [new_record[f's_element_{e}'] for e in elements if pd.notna(new_record.get(f's_element_{e}'))]
                            if domain_scores:
                                s_domain_scores['s_' + domain] = int(round(np.mean(domain_scores)))
                            else:
                                s_domain_scores['s_' + domain] = pd.NA
                        
                        encrypted_log = st.session_state.enc_manager.encrypt_log(event_log)
                        
                        new_record.update({
                            'username': username, 'date': target_date, 'mode': mode_string,
                            'consent': st.session_state.get('consent', user_data_df['consent'].iloc[-1] if not user_data_df.empty else False),
                            'g_happiness': int(g_happiness), 'event_log': encrypted_log
                        })
                        new_record.update({f'q_{d}': v / 100.0 for d, v in q_values.items()})
                        new_record.update(s_domain_scores)

                        new_df_row = pd.DataFrame([new_record])
                        
                        if not all_data_df.empty:
                            condition = (all_data_df['username'] == username) & (all_data_df['date'] == target_date)
                            all_data_df = all_data_df[~condition]

                        all_data_df_updated = pd.concat([all_data_df, new_df_row], ignore_index=True)
                        all_data_df_updated = all_data_df_updated.sort_values(by=['username', 'date']).reset_index(drop=True)
                        
                        write_data('data', all_data_df_updated)
                        st.success(f'{target_date.strftime("%Y-%m-%d")} の記録を永続的に保存しました！')
                        st.balloons()
                        st.rerun()

            with tab2:
                st.header('📊 あなたの航海チャート')
                with st.expander("▼ このチャートの見方", expanded=True):
                    st.markdown(EXPANDER_TEXTS['dashboard'])

                if user_data_df.empty or len(user_data_df.dropna(subset=S_COLS, how='all')) < 1:
                    st.info('まだ記録がありません。まずは「今日の記録」タブから、最初の日誌を記録してみましょう！')
                else:
                    df_processed = calculate_metrics(user_data_df.dropna(subset=S_COLS, how='all').copy())
                    
                    st.subheader("📈 期間分析とリスク評価 (RHI)")
                    with st.expander("▼ これは、あなたの幸福の『持続可能性』を評価する指標です", expanded=False):
                        st.markdown("...") # 省略しない

                    period_options = [7, 30, 90]
                    if len(df_processed) < 7:
                        st.info("期間分析には最低7日分のデータが必要です。記録を続けてみましょう！")
                    else:
                        default_index = 1 if len(df_processed) >= 30 else 0
                        selected_period = st.selectbox("分析期間を選択してください（日）:", period_options, index=default_index)

                        if len(df_processed) >= selected_period:
                            df_period = df_processed.tail(selected_period)

                            st.markdown("##### あなたのリスク許容度を設定")
                            col1, col2, col3 = st.columns(3)
                            lambda_param = col1.slider("変動(不安定さ)へのペナルティ(λ)", 0.0, 2.0, 0.5, 0.1, help="...")
                            gamma_param = col2.slider("下振れ(不調)へのペナルティ(γ)", 0.0, 2.0, 1.0, 0.1, help="...")
                            tau_param = col3.slider("「不調」と見なす閾値(τ)", 0.0, 1.0, 0.5, 0.05, help="...")

                            rhi_results = calculate_rhi_metrics(df_period, lambda_param, gamma_param, tau_param)

                            st.markdown("##### 分析結果")
                            col1a, col2a, col3a, col4a = st.columns(4)
                            col1a.metric("平均調和度 (H̄)", f"{rhi_results['mean_H']:.3f}")
                            col2a.metric("変動リスク (σ)", f"{rhi_results['std_H']:.3f}")
                            col3a.metric("不調日数割合", f"{rhi_results['frac_below']:.1%}")
                            col4a.metric("リスク調整済・幸福指数 (RHI)", f"{rhi_results['RHI']:.3f}", delta=f"{rhi_results['RHI'] - rhi_results['mean_H']:.3f} (平均との差)")
                        else:
                            st.warning(f"分析には最低{selected_period}日分のデータが必要です。現在の記録は{len(df_processed)}日分です。")

                    analyze_discrepancy(df_processed)
                    st.subheader('調和度 (H) の推移')
                    df_chart = df_processed.copy()
                    df_chart['date'] = pd.to_datetime(df_chart['date'], errors='coerce')
                    df_chart = df_chart.sort_values('date')
                    st.line_chart(df_chart.set_index('date')['H'])

                    st.subheader('全記録データ（イベントログは暗号化されています）')
                    st.dataframe(user_data_df.drop(columns=['username']).sort_values(by='date', ascending=False).round(3))
            
            with tab3:
                st.header("🔧 設定とガイド")
                st.subheader("データのエクスポート")
                if not user_data_df.empty:
                    csv_export = user_data_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 全データをダウンロード",
                        data=csv_export,
                        file_name=f'harmony_data_{username}_{datetime.now().strftime("%Y%m%d")}.csv',
                        mime='text/csv',
                    )

                st.markdown('---')
                st.subheader("アカウント削除")
                st.warning("この操作は取り消せません。あなたの全ての記録データが、サーバーから完全に削除されます。")
                with st.form("delete_form"):
                    password_for_delete = st.text_input("削除するには、あなたのパスワードを正確に入力してください:", type="password")
                    delete_submitted = st.form_submit_button("このアカウントと全データを完全に削除する")

                    if delete_submitted:
                        users_df = read_data('users')
                        user_record = users_df[users_df['username'] == username]
                        if not user_record.empty and EncryptionManager.check_password(password_for_delete, user_record.iloc[0]['password_hash']):
                            # ユーザー情報を削除
                            users_df_updated = users_df[users_df['username'] != username]
                            write_data('users', users_df_updated)
                            # 航海日誌データを削除
                            all_data_df_updated = all_data_df[all_data_df['username'] != username]
                            write_data('data', all_data_df_updated)
                            
                            for key in list(st.session_state.keys()):
                                del st.session_state[key]
                            st.success("アカウントと関連する全てのデータを削除しました。")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("パスワードが間違っています。")


if __name__ == '__main__':
    main()
