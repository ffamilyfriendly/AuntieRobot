from dataclasses import dataclass
import sqlite3
from typing import List

dbCon = sqlite3.connect("data.db")


def ensure_tables():
    cur = dbCon.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS posts(year, post_id, comment_id, posted_at, username, content, flag)")
    cur.execute(
        "CREATE TABLE IF NOT EXISTS years(year PRIMARY KEY, required_replies)")
    cur.execute(
        "CREATE TABLE IF NOT EXISTS users(user PRIMARY KEY, old_flair, new_flair)")
    cur.execute(
        "CREATE TABLE IF NOT EXISTS flair_handout(username, year, applied_flair, reason, UNIQUE(username, year))")


QUERY_FETCH_FOR_USER = '''
        WITH all_years AS (
            -- Replace this with your actual list of years (e.g., from the `years` table)
            SELECT year FROM years
        )
        SELECT
            COALESCE(COUNT(p.year), 0) AS rollcalls_answered,
            ay.year,
            :username AS username,
            SUM(CASE WHEN p.flag = 1 THEN 1 ELSE 0 END) AS times_reported_in,
            SUM(CASE WHEN p.flag = 2 THEN 1 ELSE 0 END) AS times_reported_out,
            SUM(CASE WHEN p.flag = 3 THEN 1 ELSE 0 END) AS times_reported_both,
            (SELECT mark_as FROM edits WHERE user = :username AND year = ay.year) AS manual_flag,
            CASE
                WHEN COUNT(*) > (SELECT required_replies FROM years y WHERE y.year = ay.year) then 1
                ELSE 0
            END AS answered_enough,
            CASE
                WHEN COUNT(p.year) = 0 THEN 0  -- Avoid division by zero
                ELSE (SUM(CASE WHEN p.flag = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(p.year))
            END AS percent_in
        FROM
            all_years ay
        LEFT JOIN
            posts p ON ay.year = p.year AND p.username = :username
        GROUP BY
            ay.year;
'''


@dataclass
class UserWinningInfo:
    rollcalls_answered: int
    year: int
    username: str
    times_reported_in: int
    times_reported_out: int
    times_reported_both: int
    manual_flag: int | None
    answered_enough: int
    percent_in: float


def get_user_winning_info(username: str) -> List[UserWinningInfo]:
    global QUERY_FETCH_FOR_USER
    cur = dbCon.cursor()
    # Use named parameter
    cur.execute(QUERY_FETCH_FOR_USER, {"username": username})
    rows = cur.fetchall()
    return [
        UserWinningInfo(
            rollcalls_answered=row[0],
            year=row[1],
            username=row[2],
            times_reported_in=row[3],
            times_reported_out=row[4],
            times_reported_both=row[5],
            manual_flag=row[6],
            answered_enough=row[7],
            percent_in=row[8],
        )
        for row in rows
    ]


QUERY_LAST_ROLLCALL = '''
 SELECT *
        FROM posts
WHERE
    username = :username
    AND year = :year
ORDER BY
    CASE
        WHEN posted_at IS NOT NULL THEN posted_at  -- Prefer posted_at if available
        ELSE ROWID                                  -- Fall back to ROWID
    END DESC
LIMIT 1;
'''


def get_last_answered_rollcall(username: str, year: int):
    global QUERY_LAST_ROLLCALL
    cur = dbCon.cursor()
    res = cur.execute(QUERY_LAST_ROLLCALL,
                      {"username": username, "year": year})
    return res.fetchone()


def get_users_on_post(post_id: str):
    cur = dbCon.cursor()
    res = cur.execute(
        "SELECT username FROM posts WHERE post_id = ? GROUP BY username", (post_id,))
    return res.fetchall()


def insert_post_entry(year: str, post_id: str, comment_id: str, posted_at: str, username: str, content: str, flag: int):
    cur = dbCon.cursor()
    cur.execute("INSERT INTO posts VALUES(?,?,?,?,?,?,?)",
                (year, post_id, comment_id, posted_at, username, content, flag))
    dbCon.commit()


def insert_user(user: str, year: int, applied_flair: int, reason: str):
    cur = dbCon.cursor()
    cur.execute("INSERT OR IGNORE INTO flair_handout VALUES(?,?,?,?)",
                (user, year, applied_flair, reason,))
    dbCon.commit()


def get_user(user: str, year: int):
    cur = dbCon.cursor()
    cur.execute(
        "SELECT * FROM flair_handout WHERE username = ? AND year = ?", (user, year,))
    return cur.fetchone()


def insert_year(year: int, required_replies: int):
    cur = dbCon.cursor()
    cur.execute("INSERT OR IGNORE INTO years VALUES(?,?)",
                (year, required_replies))
    dbCon.commit()


ensure_tables()
