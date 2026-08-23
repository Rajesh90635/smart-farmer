"""
Reserved for the market module.

Per the foundation-phase rule ("do not create fake business endpoints just
to fill the structure"), this file intentionally defines no routes yet.
It exists so the module boundary and import path are established now,
and so main.py's router-inclusion list won't need restructuring when the
real market endpoints are implemented in a later phase.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/market", tags=["market"])

# No endpoints yet. See PROJECT_STATUS.md for what phase implements this.
