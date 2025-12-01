from db import insert_post_entry
from praw.models import Comment
from shared import rollcalls
from reddit import check_post
import re


def check_comment_eligibility(comment: str):
    still_in_pattern = re.compile(
        r'\b(still\s*in|reporting\s*in|present|here|in|check\s*in|check\s*in!)\b',
        flags=re.IGNORECASE
    )

    out_pattern = re.compile(
        r'\b(i[\'\’]?m\s*out|i\s*lost|out|dropping\s*out|no\s*longer\s*in)\b',
        flags=re.IGNORECASE
    )

    comment_body = re.sub(r'[^\w\s]', '', comment.lower())

    still_in = bool(still_in_pattern.search(comment_body))
    now_out = bool(out_pattern.search(comment_body))

    if still_in and now_out:
        flag = 3
    elif now_out:
        flag = 2
    elif still_in:
        flag = 1
    else:
        flag = 0

    return (flag, comment_body)


def check_eligibility(comments: list[Comment], post_id, year):
    for comment in comments:
        if comment.author is None or comment.body is None:
            print("comment author or comment body was none.")
            continue

        (flag, comment_body) = check_comment_eligibility(comment.body)
        insert_post_entry(year, post_id, comment.id,
                          comment.created_utc, comment.author.name, comment_body[:300], flag)


def run(args: list):
    if len(args) != 2:
        print("missing required args")
        return

    year = args[0]
    range_str: str = args[1]
    [start, end] = range_str.split("-")

    start_int = int(start)
    end_int = int(end)
    post_range = range(start_int, end_int)

    posts = rollcalls[year]["posts"]

    for n in post_range:
        post_id = posts[n]
        print(f"Checking {post_id}")
        comments = check_post(post_id)
        check_eligibility(comments, post_id, year)


def help():
    return "check posts. check_posts year <start>-<end>"
