"""Analyst comments, shared by the whole team. SQLite is plenty for ~10 users."""
import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st

from core.data import ROOT

DB_FILE = ROOT / "data" / "comments.db"


@st.cache_resource
def _db() -> sqlite3.Connection:
    DB_FILE.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB_FILE, check_same_thread=False)
    con.execute("""create table if not exists comments(
        id integer primary key autoincrement,
        scope text not null,          -- a category name, or a risk ID like R-016
        author text not null,
        body text not null,
        tag text,                     -- Observation / Action / Escalation
        created text not null)""")
    return con


def add(scope: str, author: str, body: str, tag: str | None = None):
    with _db() as con:  # commits automatically
        con.execute("insert into comments(scope, author, body, tag, created) values(?,?,?,?,?)",
                    (scope, author.strip(), body.strip(), tag,
                     datetime.now().isoformat(timespec="seconds")))


def list_for(scope: str) -> pd.DataFrame:
    return pd.read_sql_query(
        "select id, author, body, tag, created from comments where scope=? order by created desc",
        _db(), params=(scope,))


def delete(comment_id: int):
    with _db() as con:
        con.execute("delete from comments where id=?", (comment_id,))
