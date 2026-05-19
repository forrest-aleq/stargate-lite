"""Lazy router exports for Stargate Lite."""

from importlib import import_module
from typing import Any

_ROUTER_MODULES = {
    "connectors": "app.routers.connectors",
    "credentials": "app.routers.credentials",
    "execute": "app.routers.execute",
    "health": "app.routers.health",
    "schemas": "app.routers.schemas",
}

__all__ = [*_ROUTER_MODULES, "oauth_router"]


def __getattr__(name: str) -> Any:
    """Load router modules only when a caller actually requests them."""
    if name == "oauth_router":
        return import_module("app.routers.oauth").router
    module_path = _ROUTER_MODULES.get(name)
    if module_path:
        return import_module(module_path)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
