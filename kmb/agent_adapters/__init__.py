"""Runtime adapters for the openKylin Agent discovery profiles."""

from .hermes import HermesAdapter
from .kylinagent import KylinAgentAdapter
from .kylinbot import KylinBotAdapter
from .openclaw import OpenClawAdapter

__all__ = ["HermesAdapter", "KylinAgentAdapter", "KylinBotAdapter", "OpenClawAdapter"]
