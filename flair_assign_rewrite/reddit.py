import json
import praw
import time
from praw.models import MoreComments
from tqdm import tqdm

config = json.load(open("./config.json"))

client = praw.Reddit(
    client_id=config["clientID"],
    client_secret=config["clientSecret"],
    password=config["password"],
    username=config["username"],
    user_agent="AuntieRobot (AutoFlair)"
)


def get_flair_for_user(user_id):
    current_flair = client.subreddit("nonutnovember").flair(redditor=user_id)
    old_flair = ""
    for _flair in current_flair:
        old_flair = _flair["flair_text"]
    return old_flair


def apply_flair(user_id: str, flair: str):
    data = {
        "name": user_id,
        "text": flair,
        "background_color": "#00fffb"
    }
    client.subreddit("nonutnovember")._reddit.request(
        "POST", f"/r/nonutnovember/api/selectflair", data=data)


def message_user(user_id: str, title: str, text: str):
    try:
        client.redditor(user_id).message(title, text)
    except Exception:
        print(f"Could not message '{user_id}'")


def check_post(post_id):
    post = client.submission(id=post_id)

    comments = post.comments

    def filter(l):
        raw_Comments = [a for a in l if not isinstance(a, MoreComments)]
        more_Comments = [a for a in l if isinstance(a, MoreComments)]
        return (raw_Comments, more_Comments)

    comments_res = filter(comments)

    raw_comments_key = 0
    more_comments_key = 1
    rawComments = comments_res[raw_comments_key]
    moreComments = comments_res[more_comments_key]

    def loadAll():
        with tqdm(desc="Loading comments") as pbar:
            while moreComments:
                more = moreComments.pop(0)
                if not more or not isinstance(more, MoreComments):
                    continue
                time.sleep(0.3)
                contents = filter(more.comments())
                rawComments.extend(contents[raw_comments_key])
                moreComments.extend(contents[more_comments_key])
                pbar.update(1)
                pbar.set_postfix({"loaded": len(rawComments)})
    loadAll()

    return rawComments
