import streamlit as st
import asyncio
import pandas as pd
import numpy as np
import os

from agent.graph import graph as graph_app

st.set_page_config(page_title="Alpha-GPT Trader", page_icon="📈", layout="wide")

st.title("🤖 Alpha-GPT: Quant Research Assistant")
st.markdown("---")



############################################################
# CHAT HISTORY
############################################################

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


############################################################
# RUN LANGGRAPH
############################################################

async def run_analysis(user_input):

    status_box = st.status("🧠 Alpha-GPT đang phân tích...", expanded=True)

    final_output = {}

    try:

        inputs = {"trading_idea": user_input}

        async for event in graph_app.astream(inputs, stream_mode="updates"):

            for node_name, node_output in event.items():

                if node_name == "hypothesis_generator":
                    status_box.write("✅ Hypothesis generated")

                elif node_name == "alpha_generator":
                    status_box.write("✅ Alpha formulas generated")

                elif node_name == "alpha_coder":
                    status_box.write("✅ Python alpha code created")

                elif node_name == "alpha_backtester":
                    status_box.write("✅ Backtest completed")
                    final_output = node_output

        status_box.update(label="✅ Done", state="complete")

        return final_output

    except Exception as e:

        status_box.update(label="❌ Error", state="error")
        st.error(str(e))
        return {}

############################################################
# USER INPUT
############################################################

if prompt := st.chat_input("Nhập trading idea..."):

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):

        result = asyncio.run(run_analysis(prompt))

        if result and "backtest_results" in result:

            results = result["backtest_results"]

            for i, r in enumerate(results):

                with st.expander(f"📊 Strategy {i+1}: {r['name']}", expanded=True):

                    st.markdown(f"**Description:** {r['desc']}")
                    st.code(r["code"], language="python")

                    if "metrics" in r:

                        m = r["metrics"]

                        col1, col2, col3, col4 = st.columns(4)

                        col1.metric("IC", f"{m['IC']:.3f}")
                        col2.metric("Sharpe", f"{m['Sharpe']:.2f}")
                        col3.metric("Return", f"{m['Total Return']*100:.2f}%")
                        col4.metric("Entry Ratio", f"{m['Entry Ratio']:.2f}")

                        st.line_chart(m["Equity Curve"])

                    else:
                        st.error(r["error"])

        else:

            st.warning("No alpha generated.")