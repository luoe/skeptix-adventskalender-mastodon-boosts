# Script for getting all users on all days of the Skeptix Advent Calendar 2024 who boosted the respective toot on the same day.
# Author: Lukas Oertel <git@luoe.dev>
# License: MIT

import requests
import datetime
import pytz
from dateutil import parser


SKEPTIX_INSTANCE = "https://mastodon.social"
SKEPTIX_ACCOUNT_ID = "113458176740538217"

REBLOGGED_ENDPOINT = f"{SKEPTIX_INSTANCE}/api/v1/statuses/ID/reblogged_by"
STATUSES_ENDPOINT = f"{SKEPTIX_INSTANCE}/api/v1/accounts/ID/statuses"


TOOT_FILTER = "Türchen "


def check_if_reblog_is_in_time(user_id, toot_id, start, end) -> bool:
    # check if the reblog was done during the specified time frame
    statuses_from_user = requests.get(STATUSES_ENDPOINT.replace("ID", user_id))
    for i in statuses_from_user.json():
        if i["reblog"] is not None and i["reblog"]["in_reply_to_id"] == toot_id:
            created_at = parser.parse(i["reblog"]["created_at"])
            if created_at >= start and created_at <= end:
                return True
    else:
        while True:
            next_url = statuses_from_user.links["next"]["url"]
            if next_url is None:
                return False
            statuses_from_user = requests.get(next_url)
            for i in statuses_from_user.json():
                if i["reblog"] is not None and i["reblog"]["in_reply_to_id"] == toot_id:
                    created_at = parser.parse(i["reblog"]["created_at"])
                    if created_at >= start and created_at <= end:
                        return True
            else:
                return False


def get_all_advent_toots() -> list:
    response = requests.get(STATUSES_ENDPOINT.replace("ID", SKEPTIX_ACCOUNT_ID))
    toots = dict()
    for i in response.json():
        if (
            i["card"] is not None
            and i["card"]["title"].startswith(TOOT_FILTER)
            and "Skeptix Adventskalender 2024" in i["card"]["title"]
        ):
            day = str(i["card"]["title"].split(" ")[1].lstrip("0"))
            toots[day] = dict()
            toots[day]["id"] = i["id"]
            toots[day]["created_at"] = parser.parse(i["created_at"])

    else:
        while True:
            next_url = response.links["next"]["url"]
            if next_url is None:
                return toots
            response = requests.get(next_url)
            for i in response.json():
                if (
                    i["card"] is not None
                    and i["card"]["title"].startswith(TOOT_FILTER)
                    and "Skeptix Adventskalender 2024" in i["card"]["title"]
                ):
                    day = str(i["card"]["title"].split(" ")[1].lstrip("0"))
                    toots[day] = dict()
                    toots[day]["id"] = i["id"]
                    toots[day]["created_at"] = parser.parse(i["created_at"])
            else:
                return toots


def get_reblogs_for_toot(toot_id, start, end) -> list:
    response = requests.get(REBLOGGED_ENDPOINT.replace("ID", str(toot_id)))
    boosts = list()
    for i in response.json():
        user = {}
        username = i["username"]
        user_id = i["id"]
        url = i["url"]

        if check_if_reblog_is_in_time(user_id, toot_id, start, end):
            user["username"] = username
            user["url"] = url
            user["id"] = user_id
            boosts.append(user)

    return boosts


def __main__():

    current_day = datetime.datetime.today().strftime("%d")
    all_advent_toots = get_all_advent_toots()

    for i in range(1, int(current_day) + 1):
        # range(1,1) will not work
        if i == 0:
            continue

        timezone = pytz.timezone("CET")
        current_date = datetime.datetime.now(timezone).date()
        start_datetime = timezone.localize(
            datetime.datetime.combine(current_date, datetime.datetime.min.time())
        )
        end_datetime = (
            start_datetime + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)
        )

        print(f"Nutzer_innen für Türchen {i}:")
        skeptix_toot_id = all_advent_toots[str(i)]["id"]
        reblogs = get_reblogs_for_toot(
            skeptix_toot_id, all_advent_toots[str(i)]["created_at"], end_datetime
        )
        for i in reblogs:
            print(i["username"] + " " + i["url"])

        print("")


if __name__ == "__main__":
    __main__()
