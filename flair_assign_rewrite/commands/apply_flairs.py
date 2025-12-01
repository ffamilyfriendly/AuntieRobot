from dataclasses import dataclass
import time
from tqdm import tqdm
from db import get_last_answered_rollcall, get_users_on_post, get_user_winning_info, get_user, insert_user
from reddit import get_flair_for_user, message_user, apply_flair
from shared import rollcalls


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


def won_year(year_inf: UserWinningInfo):
    if (year_inf.manual_flag is not None):
        return bool(year_inf.manual_flag)

    # If the user did not answer enough rollcalls we fail them.
    # This value is different from year to year due to data availibility.
    if (year_inf.answered_enough == 0):
        return False

    # If less than 60% of the rollcall answers do not indicate IN we fail the user.
    if (year_inf.percent_in < 60):
        return False

    last_rollcall = get_last_answered_rollcall(
        year_inf.username, year_inf.year)
    last_rollcall_flag = last_rollcall[6]

    if last_rollcall_flag == 2:
        return False

    return True


FLAIR_EMOJI = ":d:"


def construct_flair(years_won: list[int]):
    global FLAIR_EMOJI
    yrs_won = len(years_won)

    if (yrs_won == 1):
        return f"DiamondNoNutter {years_won[0]} {FLAIR_EMOJI}"
    elif (yrs_won == 2):
        return f"DiamondNoNutter {years_won[0]} and {years_won[1]} {FLAIR_EMOJI}"
    elif (yrs_won == 3):
        return f"Diamond Treble {FLAIR_EMOJI * 3}"
    elif (yrs_won == 4):
        return f"Diamond Fourfold {FLAIR_EMOJI * 4}"
    else:
        return f"{yrs_won}x DiamondNoNutter {FLAIR_EMOJI}"


def get_eligible_flair(user: list[UserWinningInfo]):
    years_won: list[int] = []
    for year in user:
        if won_year(year):
            years_won.append(year.year)
    return (construct_flair(years_won), len(years_won))


def get_flair_value(flair: str):
    if not flair:
        return 0

    sanatized_flair = flair.strip().lower()
    # if flair starts with these it'll have a large flair value
    # we do not want to re-flair all mods or the... turkey fucker
    # lord give me strength
    no_allowed_start = ["nut", "turkey"]

    for item in no_allowed_start:
        if sanatized_flair.startswith(item):
            return 666

    if "fourfold" in sanatized_flair:
        return 4
    if "treble" in sanatized_flair:
        return 3
    if "and" in sanatized_flair:
        return 2
    return 1


STR_USER_DECISION_CTA = '''
Hi there! I’m the r/nonutnovember flair bot. 🎉

You’ve earned the **`{}`** flair, but it looks like you already have a flair with a higher value (**`{}`**). If you’d like to switch to your new flair, you can apply it yourself [on our website](https://flair.evil-corp.work).

If you think there might be a mistake, [send us a modmail](https://www.reddit.com/message/compose?to=r%2Fnonutnovember) and we’ll sort it out!

**PLEASE READ [THIS POST](https://www.reddit.com/r/nonutnovember/comments/1pbm1ew/flair_rollout_is_live/)**

*(Please use modmail instead of messaging individual mods. it helps us help you faster!)*
'''

STR_USER_NOT_ELIGIBLE = '''
Hi there! I’m the r/nonutnovember flair bot.

Thanks for participating in the last roll call! Unfortunately, our system determined you aren’t eligible for a flair this time. We know it can be disappointing, but you can always check your data [on our website](https://flair.evil-corp.work) to see why.

If you think something might be wrong, don’t hesitate to [reach out via modmail](https://www.reddit.com/message/compose?to=r%2Fnonutnovember). We’re happy to take another look!

**PLEASE READ [THIS POST](https://www.reddit.com/r/nonutnovember/comments/1pbm1ew/flair_rollout_is_live/)**

*(Please use modmail instead of messaging individual mods. it helps us help you faster!)*
'''


def apply_flairs(users: list[str]):
    global STR_USER_DECISION_CTA, STR_USER_NOT_ELIGIBLE
    with tqdm(desc="Loading comments", total=len(users)) as pbar:
        for user in users:
            usr_alr_applied = get_user(user, 2025)

            # Skip users we've already dealt with
            if usr_alr_applied is not None:
                pbar.update(1)
                continue

            user_info = get_user_winning_info(user)
            (flair_txt, flair_value) = get_eligible_flair(user_info)

            if flair_value == 0:
                insert_user(user, 2025, "",
                            "user is not eligible for ANY flair")
                message_user(user, "About your flair", STR_USER_NOT_ELIGIBLE)
                time.sleep(3)
                pbar.update(1)
                continue

            current_flair = get_flair_for_user(user)
            current_flair_value = get_flair_value(current_flair)

            if (current_flair_value > flair_value):
                insert_user(user, 2025, flair_txt,
                            "user had a flair of greater value")
                message_user(user, "About your flair",
                             STR_USER_DECISION_CTA.format(flair_txt, current_flair))
                time.sleep(3)
                pbar.update(1)
                continue

            apply_flair(user, flair_txt)
            insert_user(user, 2025, flair_txt,
                        "Everything ok!")

            pbar.update(1)
            time.sleep(2)


def run(*args):
    global STR_USER_DECISION_CTA
    post_id = rollcalls["2025"]["posts"][-1]
    if args[0] and args[0][0]:
        post_id = args[0][0]
    print(f"getting all active members in post '{post_id}'")
    winners = get_users_on_post(post_id)
    filtered = []

    for user in winners:
        if get_user(user[0], 2025) is None:
            filtered.append(user[0])

    apply_flairs(filtered)


def help():
    return "Apply the flairs"
