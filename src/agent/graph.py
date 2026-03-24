# src/agent/graph.py
import os
from langgraph.graph import StateGraph
# from langgraph.checkpoint.memory import MemorySaver # <-- Comment dòng này lại

from agent.state import State
from agent.agents.user_input_agent import user_input_agent
from agent.agents.hypothesis_agent import hypothesis_agent
# Nếu bạn chưa có file alpha_generator_agent thì comment dòng dưới lại
from agent.agents.alpha_generator_agent import alpha_generator_agent 
from agent.agents.alpha_coder_agent import alpha_coder_agent
from agent.agents.backtest import alpha_backtester


def create_graph():
    """Create and configure the LangGraph workflow."""

    # Define the graph workflow
    workflow = StateGraph(State)

    # Add agents to the graph
    workflow.add_node("user_input", user_input_agent)
    workflow.add_node("hypothesis_generator", hypothesis_agent)
    workflow.add_node("alpha_generator", alpha_generator_agent)
    workflow.add_node("alpha_coder", alpha_coder_agent)
    workflow.add_node("alpha_backtester", alpha_backtester)

    # Connect the agents
    # Luồng đi: Start -> User Input -> Hypothesis -> Alpha Generator -> Alpha Coder -> End
    workflow.add_edge("__start__", "user_input")
    workflow.add_edge("user_input", "hypothesis_generator")
    workflow.add_edge("hypothesis_generator", "alpha_generator")
    workflow.add_edge("alpha_generator", "alpha_coder")
    workflow.add_edge("alpha_coder", "alpha_backtester")
    workflow.add_edge("alpha_backtester", "__end__")

    # --- SỬA ĐỔI: BỎ CHECKPOINTER ĐỂ CHẠY STUDIO ---
    # LangGraph Studio sẽ tự động bơm checkpointer vào, mình không cần khai báo
    graph = workflow.compile() 
    
    graph.name = "Alpha Generation and Coding Workflow"
    
    return graph

# Create the graph
graph = create_graph()