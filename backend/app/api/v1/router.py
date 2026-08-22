"""
Aggregates all /api/v1/* routers. Placeholder domain routers are included
now (with zero routes) so the mount points and OpenAPI grouping exist from
day one; each will gain real endpoints in its own implementation phase.
"""
from fastapi import APIRouter

from app.api.v1 import ai, assistant, auth, cases, crop_assistant, crop_financials, crop_performance, crop_photos, crop_risk, crop_varieties, crops, experts, farmers, farms, harvests, health, health_timeline, invoices, ledger, market, marketplace, notifications, orders, personalization, plots, products, professionals, tasks, treatments, weather, weather_actions

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(farmers.router)
api_router.include_router(farms.router)
api_router.include_router(plots.router)
api_router.include_router(crops.router)
api_router.include_router(crop_varieties.router)
api_router.include_router(crop_photos.router)
api_router.include_router(ai.router)
api_router.include_router(weather.router)
api_router.include_router(notifications.router)
api_router.include_router(professionals.router)
api_router.include_router(cases.router)
api_router.include_router(products.router)
api_router.include_router(orders.router)
api_router.include_router(harvests.router)
api_router.include_router(marketplace.router)
api_router.include_router(assistant.router)
api_router.include_router(market.router)
api_router.include_router(experts.router)
api_router.include_router(tasks.router)
api_router.include_router(ledger.router)
api_router.include_router(invoices.router)
api_router.include_router(crop_financials.router)
api_router.include_router(crop_risk.router)
api_router.include_router(treatments.router)
api_router.include_router(health_timeline.router)
api_router.include_router(crop_assistant.router)
api_router.include_router(weather_actions.router)
api_router.include_router(crop_performance.router)
api_router.include_router(personalization.router)
