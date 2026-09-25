from __future__ import annotations

import logging

logger = logging.getLogger("payments")


class DarajaError(Exception):
    pass


def get_access_token():
    return "stub-token"


def stk_push(*args, **kwargs):
    return {"ok": True}


def query_transaction_status(*args, **kwargs):
    return {"ok": True}


def build_password(*args, **kwargs):
    return "stub-password"
