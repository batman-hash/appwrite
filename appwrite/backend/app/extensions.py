"""Shared handles used by the modular backend layer."""

from __future__ import annotations

from backend import webapp as legacy


app = legacy.app
db = legacy.db_orm
mail = legacy.mail
conn = legacy.conn
session = legacy.session

