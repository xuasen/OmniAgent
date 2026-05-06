"""Application settings — merges YAML config with environment variables."""

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from omniagent.common.config_loader import load_yaml_config


class ServerSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    log_level: str = "info"


class DatabaseSettings(BaseModel):
    url: str = "postgresql+asyncpg://omniagent:omniagent_dev@localhost:5432/omniagent"
    pool_size: int = 20
    pool_max_overflow: int = 10


class TraceCollectorSettings(BaseModel):
    buffer_size: int = 1000
    flush_interval_seconds: int = 5
    max_trace_size_mb: int = 10


class TraceStoreSettings(BaseModel):
    retention_days: int = 90
    max_query_limit: int = 500


class AdapterConfig(BaseModel):
    id: str
    type: str
    mode: str = "proxy"
    config: dict = Field(default_factory=dict)


class ExecutionSettings(BaseModel):
    trace_collector: TraceCollectorSettings = Field(default_factory=TraceCollectorSettings)
    trace_store: TraceStoreSettings = Field(default_factory=TraceStoreSettings)
    adapters: list[AdapterConfig] = Field(default_factory=list)


class OrchestratorSettings(BaseModel):
    default_node_timeout_seconds: int = 60
    max_parallel_nodes: int = 10
    checkpoint_enabled: bool = True


class HITLSettings(BaseModel):
    default_timeout_minutes: int = 30
    default_timeout_action: str = "reject"


class ObservabilitySettings(BaseModel):
    audit_log_enabled: bool = True
    audit_retry_max: int = 3
    audit_retry_backoff_base_seconds: int = 2
    metrics_export_interval_seconds: int = 60


class PolicyEngineSettings(BaseModel):
    config_path: str = "config/policies/"
    hot_reload_enabled: bool = True


class ControlSettings(BaseModel):
    orchestrator: OrchestratorSettings = Field(default_factory=OrchestratorSettings)
    hitl: HITLSettings = Field(default_factory=HITLSettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)
    policy_engine: PolicyEngineSettings = Field(default_factory=PolicyEngineSettings)


class StrategyEngineSettings(BaseModel):
    evaluation_interval_seconds: int = 300
    default_objective_priority: int = 1


class DecisionGraphSettings(BaseModel):
    max_fallback_depth: int = 3


class ReplayEngineSettings(BaseModel):
    sandbox_enabled: bool = True
    max_concurrent_replays: int = 5
    batch_max_size: int = 100


class ExperimentEngineSettings(BaseModel):
    min_sample_size: int = 100
    max_concurrent_experiments: int = 10
    safety_check_interval_seconds: int = 60


class LearningLoopSettings(BaseModel):
    analysis_interval_hours: int = 24
    auto_apply_threshold: float = 0.15
    mode: str = "manual"


class ConflictResolverSettings(BaseModel):
    default_arbitration: str = "priority"
    high_risk_escalation: bool = True
    config_path: str = "config/conflicts.yaml"


class FinOpsSettings(BaseModel):
    cost_check_interval_seconds: int = 30
    failover_timeout_seconds: int = 5
    model_routes_path: str = "config/model_routes.yaml"
    routing_rules: list[dict] = Field(default_factory=list)


class IntelligenceSettings(BaseModel):
    strategy_engine: StrategyEngineSettings = Field(default_factory=StrategyEngineSettings)
    decision_graph: DecisionGraphSettings = Field(default_factory=DecisionGraphSettings)
    replay_engine: ReplayEngineSettings = Field(default_factory=ReplayEngineSettings)
    experiment_engine: ExperimentEngineSettings = Field(default_factory=ExperimentEngineSettings)
    learning_loop: LearningLoopSettings = Field(default_factory=LearningLoopSettings)
    conflict_resolver: ConflictResolverSettings = Field(default_factory=ConflictResolverSettings)
    finops: FinOpsSettings = Field(default_factory=FinOpsSettings)


class ProxySettings(BaseModel):
    upstream_url: str = "https://api.openai.com"
    timeout_seconds: float = 60.0
    listen_port: int = 8080


class Settings(BaseSettings):
    server: ServerSettings = Field(default_factory=ServerSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    proxy: ProxySettings = Field(default_factory=ProxySettings)
    execution: ExecutionSettings = Field(default_factory=ExecutionSettings)
    control: ControlSettings = Field(default_factory=ControlSettings)
    intelligence: IntelligenceSettings = Field(default_factory=IntelligenceSettings)

    model_config = {"env_prefix": "OMNIAGENT_", "env_nested_delimiter": "__"}


@lru_cache
def get_settings() -> Settings:
    config_path = os.environ.get("OMNIAGENT_CONFIG", "config/omniagent.yaml")
    if Path(config_path).exists():
        yaml_config = load_yaml_config(config_path)
        return Settings(**yaml_config)
    return Settings()
