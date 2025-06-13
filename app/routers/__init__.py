"""app/routers/__init__.py

Роутеры для aiogram 3 бота.
"""

from .admin import admin_router
from .admin_menu import admin_menu_router
from .common import common_router
from .menu import menu_router

__all__ = ["admin_router", "admin_menu_router", "common_router", "menu_router"]
