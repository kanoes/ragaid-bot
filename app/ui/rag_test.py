"""
RAGテスト関連コンポーネント
"""

import os
import streamlit as st
import dotenv

from robot.rag import RAGModule

dotenv.load_dotenv()

def render_rag_test():
    """
    RAGテストインターフェイスをレンダリングし、ユーザーがRAGモジュールのQA機能を直接テストできるようにします
    """

    st.header("RAGシステムテスト")

    # OpenAI APIキーを使用
    api_key = os.environ.get("OPENAI_API_KEY", None)

    # 現在のディレクトリの取得
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # 知識ディレクトリの指定
    knowledge_dir = os.path.join(current_dir, "robot", "rag", "knowledge")
    # ベクトルDBディレクトリの指定
    vector_db_dir = os.path.join(knowledge_dir, "vector_db")

    # セッション状態にRAGモジュールが存在しない場合は初期化
    if "rag_module" not in st.session_state:
        rag = RAGModule(
            api_key=api_key,
            knowledge_dir=knowledge_dir,
            vector_db_dir=vector_db_dir,
            top_k=3
        )
        st.session_state["rag_module"] = rag
    else:
        rag = st.session_state["rag_module"]

    # RAGモジュールの準備状態を確認
    if not rag.is_ready():
        st.warning("ナレッジベースがロードされていない、またはAPIキーが設定されていません。純粋なLLM回答が使用される可能性があります。")
    else:
        st.success(f"ナレッジベースを正常にロードしました: {knowledge_dir}")

    # テストインターフェイスを作成
    test_tabs = st.tabs(["QAテスト", "思考レイヤーテスト", "トリガーレイヤーテスト", "意思決定インターフェーステスト"])

    # QAテストタブ
    with test_tabs[0]:
        st.subheader("直接QAテスト")
        query = st.text_input("質問を入力してください：（例：現在ありオーダー3番卓、5番卓、8番卓、配達順序を教えて）", key="qa_query")
        use_rag = st.checkbox("RAG強化回答を使用する", value=True, key="qa_use_rag")

        if st.button("質問を送信", key="qa_submit"):
            if not query:
                st.error("質問内容を入力してください")
            else:
                with st.spinner("思考中..."):
                    try:
                        answer = rag.query_answer(query, use_rag=use_rag)
                        st.success("回答成功")
                        st.info(answer)
                    except Exception as e:
                        st.error(f"エラーが発生しました: {e}")

    # 思考レイヤーテストタブ
    with test_tabs[1]:
        st.subheader("思考レイヤーテスト")
        query = st.text_input("質問を入力してください：（例：現在ありオーダー3番卓、5番卓、8番卓、配達順序を教えて）", key="thinking_query")
        use_rag = st.checkbox("RAG強化回答を使用する", value=True, key="thinking_use_rag")

        if st.button("質問を送信", key="thinking_submit"):
            if not query:
                st.error("質問内容を入力してください")
            else:
                with st.spinner("思考レイヤーで処理中..."):
                    try:
                        raw_response, context_docs = rag.thinking_layer(query, use_rag=use_rag)

                        # 結果を表示
                        st.write("#### 思考レイヤー出力")
                        st.write(f"**取得したドキュメント数:** {len(context_docs)} 件")

                        for i, doc in enumerate(context_docs, 1):
                            with st.expander(f"ドキュメント {i}"):
                                st.write(doc)

                        st.write("#### LLMの生レスポンス:")
                        st.info(raw_response)

                        # 決定レイヤー処理結果を表示
                        action = rag.decision_layer(raw_response)
                        st.write("#### 意思決定レイヤー簡易結果:")
                        st.success(action)

                    except Exception as e:
                        st.error(f"エラーが発生しました: {e}")

    # トリガーレイヤーテストタブ
    with test_tabs[2]:
        st.subheader("トリガーレイヤーテスト")
        event_type = st.selectbox(
            "イベントタイプを選択してください:",
            ["plan", "obstacle"],
            format_func=lambda x: "経路計画イベント" if x == "plan" else "障害物処理イベント"
        )

        if event_type == "plan":
            robot_id = st.number_input("ロボットID", value=1, min_value=1, step=1)
            start_x = st.number_input("スタートX座標", value=0, step=1)
            start_y = st.number_input("スタートY座標", value=0, step=1)
            goal_x = st.number_input("ゴールX座標", value=10, step=1)
            goal_y = st.number_input("ゴールY座標", value=10, step=1)

            context = {
                'robot_id': robot_id,
                'start': (start_x, start_y),
                'goal': (goal_x, goal_y)
            }
        else:  # obstacle
            robot_id = st.number_input("ロボットID", value=1, min_value=1, step=1)
            pos_x = st.number_input("現在X座標", value=5, step=1)
            pos_y = st.number_input("現在Y座標", value=5, step=1)
            goal_x = st.number_input("ゴールX座標", value=10, step=1)
            goal_y = st.number_input("ゴールY座標", value=10, step=1)
            obstacle_x = st.number_input("障害物X座標", value=6, step=1)
            obstacle_y = st.number_input("障害物Y座標", value=6, step=1)

            context = {
                'robot_id': robot_id,
                'position': (pos_x, pos_y),
                'goal': (goal_x, goal_y),
                'obstacle': (obstacle_x, obstacle_y)
            }

        if st.button("テストを送信", key="trigger_submit"):
            with st.spinner(f"{event_type} イベントをトリガーレイヤーで処理中..."):
                try:
                    result = rag.trigger_layer(event_type, context)

                    # 結果を表示
                    st.write("#### トリガーレイヤー結果")
                    st.write(f"**アクション:** {result['action']}")
                    st.write(f"**コンテキスト使用:** {result['context_used']}")
                    st.write(f"**取得ドキュメント数:** {len(result['context_docs'])}")

                    if result['context_docs']:
                        with st.expander("取得されたドキュメント"):
                            for i, doc in enumerate(result['context_docs'], 1):
                                st.write(f"ドキュメント {i}:")
                                st.write(doc)
                                st.write("---")

                    st.write("#### LLMの生レスポンス:")
                    st.info(result['raw_response'])

                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")

    # 決定インターフェーステストタブ
    with test_tabs[3]:
        st.subheader("意思決定インターフェーステスト")
        situation_type = st.selectbox(
            "シチュエーションタイプを選択してください:",
            ["plan", "obstacle"],
            format_func=lambda x: "経路計画" if x == "plan" else "障害物処理"
        )

        if situation_type == "plan":
            robot_id = st.number_input("ロボットID", value=1, min_value=1, step=1, key="decision_robot_id")
            start_x = st.number_input("スタートX座標", value=0, step=1, key="decision_start_x")
            start_y = st.number_input("スタートY座標", value=0, step=1, key="decision_start_y")
            goal_x = st.number_input("ゴールX座標", value=10, step=1, key="decision_goal_x")
            goal_y = st.number_input("ゴールY座標", value=10, step=1, key="decision_goal_y")

            kwargs = {
                'robot_id': robot_id,
                'start': (start_x, start_y),
                'goal': (goal_x, goal_y)
            }
        else:  # obstacle
            robot_id = st.number_input("ロボットID", value=1, min_value=1, step=1, key="decision_robot_id")
            pos_x = st.number_input("現在X座標", value=5, step=1, key="decision_pos_x")
            pos_y = st.number_input("現在Y座標", value=5, step=1, key="decision_pos_y")
            goal_x = st.number_input("ゴールX座標", value=10, step=1, key="decision_goal_x")
            goal_y = st.number_input("ゴールY座標", value=10, step=1, key="decision_goal_y")
            obstacle_x = st.number_input("障害物X座標", value=6, step=1, key="decision_obs_x")
            obstacle_y = st.number_input("障害物Y座標", value=6, step=1, key="decision_obs_y")

            kwargs = {
                'robot_id': robot_id,
                'position': (pos_x, pos_y),
                'goal': (goal_x, goal_y),
                'context': (obstacle_x, obstacle_y)
            }

        if st.button("テストを送信", key="decision_submit"):
            with st.spinner(f"意思決定インターフェースをテスト中、シチュエーション: {situation_type}..."):
                try:
                    action = rag.make_decision(situation_type, **kwargs)

                    # 結果を表示
                    st.write("#### 意思決定結果")
                    st.success(action)

                except Exception as e:
                    st.error(f"エラーが発生しました: {e}") 