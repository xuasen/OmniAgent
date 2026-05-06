# OmniAgent

Enterprise-grade **Agent Control Plane + Decision Intelligence Engine**.

OmniAgent sits above existing Agent frameworks (OpenClaw, Hermess, AWS AgentCore) as a transparent proxy, providing strategy optimization, A/B experimentation, cost control, and multi-agent conflict resolution — without requiring any code changes to your agents.

## Architecture

```
┌─────────────────────────────────────────────┐
│        Your Agent Framework (OpenClaw, etc.) │
│            LLM_BASE_URL changed             │
└──────────────────┬──────────────────────────┘
                   │ OpenAI-compatible API
                   ▼
┌─────────────────────────────────────────────┐
│              OmniAgent Proxy                 │
│                                             │
│  Pre-hooks:  Policy → FinOps → Experiment   │
│  Post-hooks: Trace → Cost Recording         │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│          Intelligence Plane                  │
│                                             │
│  Strategy Engine (Pareto + Thompson)         │
│  Decision Graph (expression-based routing)   │
│  A/B Experiments (statistical significance)  │
│  Learning Loop (auto-optimization)           │
│  Conflict Resolver (Nash + weighted voting)  │
│  AI FinOps (circuit breaker + budgets)       │
└─────────────────────────────────────────────┘
```

## Quick Start

### 1. Start services

```bash
docker compose up -d
```

### 2. Point your agent to OmniAgent

```bash
# Before
export LLM_BASE_URL=https://api.openai.com/v1

# After
export LLM_BASE_URL=http://localhost:8000/v1
```

That's it. Zero SDK, zero code changes.

### 3. (Optional) Add tracing headers

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "X-OmniAgent-Agent-Id: my-agent" \
  -H "X-OmniAgent-Strategy: strategy-123" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4", "messages": [{"role": "user", "content": "hello"}]}'
```

## Local Development

```bash
# Install dependencies
make install

# Run dev server
make dev

# Run tests
make test

# Lint
make lint
```

## Core Capabilities

---

### 1. Strategy Engine (Pareto + Thompson Sampling)

**What it does**: Given multiple candidate execution paths, automatically selects the optimal one based on your declared business objectives and constraints.

**Algorithms**:
- **Pareto Frontier**: Finds non-dominated solutions across multiple conflicting objectives, then selects using weighted Chebyshev scalarization
- **Thompson Sampling**: Bandit-based exploration/exploitation — balances trying new paths vs. exploiting known-good ones

**Configuration** (`config/strategies/example.yaml`):

```yaml
name: "cost-quality-balance"
version: "1.0"

objectives:
  - metric: ROI
    direction: maximize
    priority: 2
    weight: 1.0
  - metric: cost
    direction: minimize
    priority: 1
    weight: 0.8
  - metric: latency_ms
    direction: minimize
    priority: 1
    weight: 0.5

constraints:
  - metric: cost
    operator: "<"
    value: 5000
    hard: true
  - metric: latency_ms
    operator: "<"
    value: 30000
    hard: false

config:
  evaluation_mode: "pareto"  # or "thompson" or "weighted"
```

**API Usage**:

```bash
# Register a strategy
curl -X POST http://localhost:8000/api/v1/strategies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "cost-quality-balance",
    "version": "1.0",
    "objectives": [
      {"metric": "ROI", "direction": "maximize", "priority": 2, "weight": 1.0},
      {"metric": "cost", "direction": "minimize", "priority": 1, "weight": 0.8}
    ],
    "constraints": [
      {"metric": "cost", "operator": "<", "value": 5000, "hard": true}
    ]
  }'

# Evaluate candidates against strategy
curl -X POST http://localhost:8000/api/v1/strategies/{strategy_id}/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "candidates": [
      {"name": "path_a", "ROI": 15, "cost": 3000, "latency_ms": 5000},
      {"name": "path_b", "ROI": 8, "cost": 1000, "latency_ms": 2000},
      {"name": "path_c", "ROI": 20, "cost": 6000, "latency_ms": 8000}
    ]
  }'

# Response: path_c eliminated (cost > 5000), Pareto selects between path_a and path_b
```

**Use via Proxy** (attach strategy to requests):

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer $API_KEY" \
  -H "X-OmniAgent-Strategy: cost-quality-balance" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4", "messages": [{"role": "user", "content": "analyze this"}]}'
```

---

### 2. Decision Graph (Expression-Based Routing)

**What it does**: Routes requests through different execution paths based on runtime conditions. Supports a CEL-like expression language for complex routing rules, with per-path performance tracking.

**Key features**:
- Expression evaluation: `&&`, `||`, comparison operators, `in`, `contains`
- Nested variable resolution: `request.model`, `user.tier`, `context.priority`
- Rolling performance statistics per path (latency, cost, success rate)
- Cascading fallback with configurable depth

**Configuration** (`config/decisions/routing.yaml`):

```yaml
name: "user-tier-routing"

paths:
  - id: premium_path
    name: "Premium Model Path"
    conditions:
      _expr: "user.tier == 'premium' && request.tokens > 100"
    nodes:
      - node_id: "analyze"
        action: "gpt-4-turbo"
    expected_cost: 0.05
    expected_latency_ms: 3000

  - id: high_complexity
    name: "Complex Request Path"
    conditions:
      _expr: "request.complexity >= 0.7 || request.model contains 'gpt-4'"
    nodes:
      - node_id: "analyze"
        action: "gpt-4"
    expected_cost: 0.03
    expected_latency_ms: 5000

  - id: standard_path
    name: "Standard Path"
    conditions:
      _expr: "user.tier in ['free', 'basic']"
    nodes:
      - node_id: "analyze"
        action: "gpt-3.5-turbo"
    expected_cost: 0.002
    expected_latency_ms: 1000

fallback_paths:
  - id: economy_fallback
    name: "Economy Fallback"
    nodes:
      - node_id: "analyze"
        action: "gpt-3.5-turbo"
    expected_cost: 0.001
```

**API Usage**:

```bash
# Register decision graph
curl -X POST http://localhost:8000/api/v1/decisions/graphs \
  -H "Content-Type: application/json" \
  -d @config/decisions/routing.yaml

# Query path performance stats
curl http://localhost:8000/api/v1/decisions/graphs/{graph_id}/stats

# Response:
# {
#   "premium_path": {"avg_latency_ms": 2800, "avg_cost": 0.048, "success_rate": 0.97, "sample_count": 523},
#   "standard_path": {"avg_latency_ms": 900, "avg_cost": 0.0018, "success_rate": 0.99, "sample_count": 4210}
# }
```

---

### 3. A/B Experiments (Statistical Significance)

**What it does**: Run controlled experiments with multiple strategy variants, automatically split traffic, collect metrics, and determine statistical significance — so you know which approach is actually better, not just guessing.

**Statistical tests**:
- **Chi-squared test**: For binary outcomes (success/failure rate comparison)
- **Welch's t-test**: For continuous metrics (cost, latency comparison)
- **SPRT (Sequential Probability Ratio Test)**: Allows early stopping when significance is reached, saving traffic

**Safety features**:
- Auto-stop variant if error rate exceeds threshold
- Configurable minimum sample size before concluding
- Real-time safety monitoring with event alerts

**API Usage**:

```bash
# Create experiment
curl -X POST http://localhost:8000/api/v1/experiments \
  -H "Content-Type: application/json" \
  -d '{
    "name": "new-prompt-v2-test",
    "variants": [
      {"id": "control", "strategy_id": "strategy-uuid-1", "traffic_percentage": 50},
      {"id": "new_prompt", "strategy_id": "strategy-uuid-2", "traffic_percentage": 50}
    ],
    "target_sample_size": 2000,
    "target_duration_hours": 72,
    "safety_thresholds": {
      "error_rate": 0.05,
      "cost": 1.0
    }
  }'

# Start experiment
curl -X POST http://localhost:8000/api/v1/experiments/{exp_id}/start

# Route requests through experiment (via header)
curl http://localhost:8000/v1/chat/completions \
  -H "X-OmniAgent-Experiment: {exp_id}" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"model": "gpt-4", "messages": [...]}'

# Check statistical significance
curl http://localhost:8000/api/v1/experiments/{exp_id}/significance?metric=success

# Response:
# {
#   "test": "chi_squared",
#   "significant": true,
#   "p_value": 0.003,
#   "confidence": 0.95,
#   "variant_a_rate": 0.82,
#   "variant_b_rate": 0.91
# }

# Check if experiment can stop early (SPRT)
curl http://localhost:8000/api/v1/experiments/{exp_id}/sequential?metric=success
# Response: "accept_h1" (new variant is better, can stop)

# Get full report
curl http://localhost:8000/api/v1/experiments/{exp_id}/report

# Stop experiment
curl -X POST http://localhost:8000/api/v1/experiments/{exp_id}/stop
```

---

### 4. Learning Loop (Auto-Optimization)

**What it does**: Continuously monitors execution results, detects when actual performance deviates from expected, and automatically generates optimization suggestions using gradient-free optimization (Nelder-Mead simplex).

**How it works**:
1. Records execution metrics per strategy over time
2. Smooths noisy data with Exponential Moving Average (EMA)
3. Computes deviation between expected and actual metrics
4. When deviation exceeds threshold (default 15%), generates an adjustment suggestion
5. Optimizes parameters using Nelder-Mead to find values that minimize the gap
6. Supports manual approval or auto-apply mode

**API Usage**:

```bash
# Record execution result (called automatically by proxy, or manually)
curl -X POST http://localhost:8000/api/v1/learning/record \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": "strategy-uuid",
    "metrics": {
      "cost": 0.045,
      "latency_ms": 3200,
      "success_rate": 0.88
    }
  }'

# Trigger analysis (normally runs on schedule, can be triggered manually)
curl -X POST http://localhost:8000/api/v1/learning/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": "strategy-uuid",
    "expected_metrics": {
      "cost": 0.03,
      "latency_ms": 2000,
      "success_rate": 0.95
    }
  }'

# Response (if deviation detected):
# {
#   "id": "adjustment-uuid",
#   "status": "pending",
#   "trigger_reason": "Metrics deviate by 32.5% (threshold: 15.0%). Deviating metrics: cost, latency_ms",
#   "current_params": {"cost": 0.03, "latency_ms": 2000, "success_rate": 0.95},
#   "suggested_params": {"cost": 0.042, "latency_ms": 2850, "success_rate": 0.89},
#   "expected_improvement": {"deviation_reduction": 0.16}
# }

# List pending adjustments
curl http://localhost:8000/api/v1/learning/adjustments?status=pending

# Approve an adjustment
curl -X POST http://localhost:8000/api/v1/learning/adjustments/{adj_id}/approve \
  -H "Content-Type: application/json" \
  -d '{"approver_id": "admin@company.com"}'

# Or reject
curl -X POST http://localhost:8000/api/v1/learning/adjustments/{adj_id}/reject
```

**Configuration**:

```yaml
intelligence:
  learning_loop:
    analysis_interval_hours: 24
    auto_apply_threshold: 0.15   # 15% deviation triggers suggestion
    mode: "manual"               # "manual" = require approval, "auto" = apply immediately
```

---

### 5. Conflict Resolver (Nash + Weighted Voting)

**What it does**: When multiple agents compete for the same resource or make conflicting decisions (e.g., recommendation agent vs. advertising agent fighting for a display slot), automatically arbitrates based on configurable rules.

**Arbitration methods**:
- **Priority-based**: Simple priority ordering (default)
- **Weighted Voting**: Each agent votes with confidence; weights are adjusted by a fairness penalty to prevent one agent from dominating
- **Nash Bargaining**: Game-theoretic allocation maximizing the product of each agent's surplus over their disagreement point

**Fairness mechanism**: After each conflict, the winner's penalty increases and losers' penalties decay — ensuring long-run fairness even with fixed priority rules.

**API Usage**:

```bash
# Report a conflict for resolution
curl -X POST http://localhost:8000/api/v1/conflicts/resolve \
  -H "Content-Type: application/json" \
  -d '{
    "execution_id": "workflow-uuid",
    "resource": "homepage_slot_1",
    "agent_decisions": {
      "recommendation_agent": {
        "action": "show_product_A",
        "confidence": 0.85,
        "priority": 3,
        "utility": 10,
        "risk_level": "low"
      },
      "advertising_agent": {
        "action": "show_ad_campaign_B",
        "confidence": 0.92,
        "priority": 2,
        "utility": 8,
        "risk_level": "low"
      },
      "personalization_agent": {
        "action": "show_editorial_content",
        "confidence": 0.70,
        "priority": 1,
        "utility": 5,
        "risk_level": "low"
      }
    }
  }'

# Response (weighted_voting mode):
# {
#   "id": "conflict-uuid",
#   "conflict_type": "resource_contention:homepage_slot_1",
#   "resolution": {
#     "winner": "advertising_agent",
#     "decision": {"action": "show_ad_campaign_B", "confidence": 0.92},
#     "method": "weighted_voting",
#     "scores": {
#       "recommendation_agent": 2.55,
#       "advertising_agent": 2.76,
#       "personalization_agent": 0.70
#     }
#   },
#   "escalated": false
# }

# Get fairness scores (shows accumulated penalties)
curl http://localhost:8000/api/v1/conflicts/fairness

# Response:
# {
#   "advertising_agent": 0.4,
#   "recommendation_agent": 0.1,
#   "personalization_agent": 0.0
# }
# Note: advertising_agent has higher penalty from winning often, 
# making it slightly harder to win next time (fairness)

# List historical conflict records
curl http://localhost:8000/api/v1/conflicts?limit=20
```

**Configuration**:

```yaml
intelligence:
  conflict_resolver:
    default_arbitration: "weighted_voting"   # "priority" | "weighted_voting" | "nash"
    high_risk_escalation: true               # escalate to HITL if risk_level == "high"
```

---

### 6. AI FinOps (Circuit Breaker + Budgets)

**What it does**: Controls LLM costs across your entire agent fleet with intelligent model routing, automatic failover, budget enforcement, and predictive cost estimation.

**Key features**:
- **Circuit Breaker per Provider**: Detects repeated failures, stops sending traffic to unhealthy providers, auto-recovers after timeout
- **Sliding Window Budget**: Track cost per model within a 1-hour rolling window
- **Automatic Downgrade**: When cumulative cost exceeds limit, routes to cheaper model tier
- **Tier-Based Routing**: Route premium users to GPT-4, standard users to GPT-3.5, based on configurable rules
- **Predictive Cost**: Estimate cost before making the call
- **Multi-Provider Failover**: If primary model's circuit opens, automatically route to next priority

**Configuration** (`config/omniagent.yaml`):

```yaml
intelligence:
  finops:
    cost_check_interval_seconds: 30
    failover_timeout_seconds: 5
    routing_rules:
      - name: "premium_users"
        conditions:
          user_tier: "premium"
        target_cost_tier: "premium"
        max_cost_usd: 10.0
      - name: "standard_users"
        conditions:
          user_tier: "standard"
        target_cost_tier: "standard"
        max_cost_usd: 2.0
      - name: "default"
        conditions: {}
        target_cost_tier: "economy"
        max_cost_usd: 0.5
```

**API Usage**:

```bash
# Register model routes
curl -X POST http://localhost:8000/api/v1/finops/routes \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "gpt-4-turbo",
    "endpoint": "https://api.openai.com",
    "cost_tier": "premium",
    "cost_per_1k_tokens": 0.01,
    "max_latency_ms": 10000,
    "capabilities": ["function_calling", "vision"],
    "priority": 0,
    "enabled": true
  }'

curl -X POST http://localhost:8000/api/v1/finops/routes \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "gpt-3.5-turbo",
    "endpoint": "https://api.openai.com",
    "cost_tier": "standard",
    "cost_per_1k_tokens": 0.0005,
    "max_latency_ms": 3000,
    "priority": 1,
    "enabled": true
  }'

curl -X POST http://localhost:8000/api/v1/finops/routes \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "llama-3-8b",
    "endpoint": "http://local-inference:8080",
    "cost_tier": "economy",
    "cost_per_1k_tokens": 0.0001,
    "max_latency_ms": 1000,
    "priority": 2,
    "enabled": true
  }'

# Get model health (circuit breaker status)
curl http://localhost:8000/api/v1/finops/providers/health

# Response:
# {
#   "gpt-4-turbo": {
#     "state": "closed",
#     "failure_count": 0,
#     "avg_latency_ms": 2340.5,
#     "hourly_cost": 12.45
#   },
#   "gpt-3.5-turbo": {
#     "state": "closed",
#     "failure_count": 1,
#     "avg_latency_ms": 890.2,
#     "hourly_cost": 3.21
#   },
#   "llama-3-8b": {
#     "state": "half_open",
#     "failure_count": 4,
#     "avg_latency_ms": 450.0,
#     "hourly_cost": 0.08
#   }
# }

# Get cost summary
curl http://localhost:8000/api/v1/finops/costs/summary

# Response:
# {
#   "total_cost_usd": 156.78,
#   "by_model": {
#     "gpt-4-turbo": 98.50,
#     "gpt-3.5-turbo": 45.20,
#     "llama-3-8b": 13.08
#   },
#   "downgrade_count": 23
# }

# Predict cost before making a call
curl http://localhost:8000/api/v1/finops/predict \
  -d '{"model_id": "gpt-4-turbo", "estimated_tokens": 5000}'
# Response: {"estimated_cost_usd": 0.05}
```

**How automatic downgrade works**:

```
Request comes in → Check cumulative cost for this execution
  ├── Under budget → Route to configured tier (e.g., premium → gpt-4)
  └── Over budget → Automatically downgrade to economy tier (e.g., llama-3-8b)
       └── Log "finops.downgrade" event with before/after model
```

**How circuit breaker works**:

```
Normal (CLOSED) → 5 consecutive failures → OPEN (reject traffic)
  └── After 5s timeout → HALF_OPEN (allow 3 test requests)
       ├── 3 successes → Back to CLOSED
       └── Any failure → Back to OPEN
```

## API Endpoints

### Proxy (OpenAI-compatible)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/chat/completions` | Proxied chat completion |
| POST | `/v1/embeddings` | Proxied embedding |
| POST | `/v1/completions` | Proxied legacy completion |

### Management API

| Group | Prefix | Description |
|-------|--------|-------------|
| Strategies | `/api/v1/strategies` | Strategy CRUD + evaluation |
| Decisions | `/api/v1/decisions/graphs` | Decision graph management |
| Experiments | `/api/v1/experiments` | A/B experiment lifecycle |
| Learning | `/api/v1/learning` | Adjustment review + apply |
| Conflicts | `/api/v1/conflicts` | Conflict records |
| FinOps | `/api/v1/finops` | Routes, costs, budgets |
| Workflows | `/api/v1/workflows` | DAG orchestration |
| Policies | `/api/v1/policies` | ACL, quotas, tool access |
| Audit | `/api/v1/audit` | Audit logs + export |
| Health | `/health`, `/ready` | Liveness + readiness |

## Tech Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI + Pydantic v2
- **Database**: PostgreSQL 16 (JSONB)
- **Proxy**: httpx async client
- **Algorithms**: Pure Python (no scipy dependency)
- **Deployment**: Docker Compose

## Project Structure

```
src/omniagent/
├── proxy/              # OpenAI-compatible reverse proxy + hooks
├── intelligence/
│   ├── algorithms/     # Pure algorithm implementations
│   ├── services/       # Business logic (7 services)
│   ├── models/         # Pydantic domain models
│   └── api/            # REST endpoints
├── control/            # Orchestration, HITL, policies, audit
├── common/             # Base classes, event bus, config loader
└── db/                 # SQLAlchemy ORM + migrations
```

## Configuration

All configuration via `config/omniagent.yaml` with `${ENV_VAR:-default}` substitution:

```yaml
proxy:
  upstream_url: "${LLM_UPSTREAM_URL:-https://api.openai.com}"

intelligence:
  strategy_engine:
    evaluation_interval_seconds: 300
  experiment_engine:
    min_sample_size: 100
  learning_loop:
    mode: "manual"  # or "auto"
    auto_apply_threshold: 0.15
  finops:
    failover_timeout_seconds: 5
```

## License

Apache-2.0
