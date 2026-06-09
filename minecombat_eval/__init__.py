"""Python client for MineCombat-Evaluation (TCP JSON protocol v1)."""

from .agents import AgentFn, make_random_agent, noop_agent
from .connector import EvaluationConnector, EvaluationProtocolError
from .env import MineCombatEnv
from .helpers import (
    aim_at,
    clamp,
    mob_distance,
    mobs,
    mobs_by_distance,
    nearest_mob,
    normalize_yaw,
    player_health_fraction,
    validate_action,
)
from .models import Action, EpisodeResult, PROTOCOL_VERSION
from .policy import Policy

__all__ = [
    "Action",
    "AgentFn",
    "EpisodeResult",
    "PROTOCOL_VERSION",
    "EvaluationConnector",
    "EvaluationProtocolError",
    "MineCombatEnv",
    "Policy",
    "noop_agent",
    "make_random_agent",
    # policy-writing helpers (minecombat_eval.helpers)
    "aim_at",
    "clamp",
    "mob_distance",
    "mobs",
    "mobs_by_distance",
    "nearest_mob",
    "normalize_yaw",
    "player_health_fraction",
    "validate_action",
]
