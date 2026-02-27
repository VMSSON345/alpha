# src/agent/configuration.py
from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Optional

from langchain_core.runnables import RunnableConfig

@dataclass(kw_only=True)
class Configuration:
    """The configuration for the agent."""

    # 1. Embedding Model
    embedding_model: str = "nomic-ai/nomic-embed-text-v1.5"

    # 2. LLM Model (CẬP NHẬT CHÍNH XÁC TỪ DANH SÁCH CỦA BẠN)
    # Chúng ta dùng Llama 3.3 (v3p3) 70B Instruct
    llm_model: str = "accounts/fireworks/models/llama-v3p3-70b-instruct"

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> Configuration:
        """Create a Configuration instance from a RunnableConfig object."""
        configurable = (config.get("configurable") or {}) if config else {}
        _fields = {f.name for f in fields(cls) if f.init}
        return cls(**{k: v for k, v in configurable.items() if k in _fields})