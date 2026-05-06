"""Intelligence plane router."""

from fastapi import APIRouter

from omniagent.intelligence.api.strategies import router as strategies_router
from omniagent.intelligence.api.decisions import router as decisions_router
from omniagent.intelligence.api.replays import router as replays_router
from omniagent.intelligence.api.experiments import router as experiments_router
from omniagent.intelligence.api.learning import router as learning_router
from omniagent.intelligence.api.conflicts import router as conflicts_router
from omniagent.intelligence.api.finops import router as finops_router

router = APIRouter(tags=["intelligence"])

router.include_router(strategies_router)
router.include_router(decisions_router)
router.include_router(replays_router)
router.include_router(experiments_router)
router.include_router(learning_router)
router.include_router(conflicts_router)
router.include_router(finops_router)
