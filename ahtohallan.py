import streamlit as st
import numpy as np
import pandas as pd
import pytz
import time
from collections import defaultdict
from datetime import datetime, timezone
import functools
import random

from session_state import get

from repository.emoji_events import EmojiEvents
from constants.loading import LOADING_MESSAGES

st.set_page_config(layout='wide')

emoji_events = EmojiEvents()

parse_emoji_name = lambda r: r["emoji_id|emoji_name"].split("|")[1] if isinstance(r, dict) else r.split("|")[1]

#TODO: Make this a metadata row in dynamo
AUTHOR_NAME_TO_ID = {
    "YenSid": "147812991264489472",
    "Big Bezos": "180493684557611009",
    "Jake N' Bake": "180493684557611009",
    "stefan": "362787354844463135",
    "ItsMike": "234159938916581397",
    "Biiig Chiiiick": "294691480029888522",
    "klaiii": "196104259496837121"
}

# 30 minute caching for emojis
@st.cache(suppress_st_warning=True, ttl=1800, show_spinner=False)
def get_available_emojis():
    data = emoji_events.get_all_emojis()
    return [row["emoji_id|emoji_name"] for row in data]

CACHED_EMOJIS = get_available_emojis()

def parse_into_object(data, obj, tz):
    for entry in data:
        emoji_name = parse_emoji_name(entry)
        last_used = datetime.fromisoformat(entry["timestamp"]).replace(tzinfo=timezone.utc)
        obj[emoji_name].append(int(entry["count"]))
        obj[emoji_name].append(last_used.astimezone(pytz.timezone(tz)).strftime("%B %d, %Y %I:%M %p"))

def render():
    tz = st.selectbox(label="Timezone", options=["US/Eastern", "US/Pacific"])
    render_emoji_alltime_data(tz)
    render_author_emoji_data(tz)

def render_emoji_alltime_data(tz):

    if st.button("Refresh cache"):
        st.caching.clear_cache()

    top_emoji_data, lru_data, mru_data = get_alltime_data(tz)

    st.header("All time most popular")
    st.table(top_emoji_data)

    st.header("Most recently used")
    st.table(mru_data)

    st.header("Least recently used")
    st.table(lru_data)


def render_author_emoji_data(tz):
    st.header("Member usage")
    selected_author_name = st.selectbox(label="Member", options=[name for name, _ in AUTHOR_NAME_TO_ID.items()])
    n = int(st.slider('Number of Top Emojis to show', min_value=1, max_value=10, value=5))
    selected_author_id = AUTHOR_NAME_TO_ID[selected_author_name]

    author_emojis = get_alltime_author_data(selected_author_id, tz)

    top_n_emojis = sorted(author_emojis.items(), key=lambda item: item[1][0], reverse=True)[:n]

    author_top_emojis = pd.DataFrame(dict(top_n_emojis), index=["Count", "Last Used"])

    st.write("Top emoji usage")
    st.table(author_top_emojis)


def get_alltime_data(tz):
    results = fetch_from_db()
    top_all_time = sorted(results, key=lambda item : item["count"], reverse=True)[:10]
    least_recently_used = sorted(results, key=lambda item : item["timestamp"])[:10]
    most_recently_used = sorted(results, key=lambda item : item["timestamp"], reverse=True)[:10]

    top_emojis = defaultdict(list)
    lru = defaultdict(list)
    mru = defaultdict(list)


    parse_into_object(top_all_time, top_emojis, tz)
    parse_into_object(least_recently_used, lru, tz)
    parse_into_object(most_recently_used, mru, tz)


    return pd.DataFrame(top_emojis, index=["Count", "Last Used"]), \
           pd.DataFrame(lru, index=["Count", "Last Used"]), \
           pd.DataFrame(mru, index=["Count", "Last Used"])


# Cache values for 5 minutes to prevent crushing the DB
@st.cache(suppress_st_warning=True, ttl=300, show_spinner=False)
def fetch_from_db():
    success_placeholder = st.empty()
    emoji_events_over_all_time = emoji_events.get_all_emojis()
    success_placeholder.success("Member cache refreshed!")
    time.sleep(0.7)
    success_placeholder.empty()
    return emoji_events_over_all_time

# Cache values for 30 minutes to prevent crushing the DB
@st.cache(suppress_st_warning=True, ttl=1800, show_spinner=False, allow_output_mutation=True)
def get_alltime_author_data(author_id, tz):
    success_placeholder = st.empty()
    author_emojis = defaultdict(list)
    for pk in CACHED_EMOJIS:
        emoji_name = parse_emoji_name(pk)
        # cached call, refreshes every 30 minutes
        results = fetch_author_emoji_from_db(pk, author_id)

        if not results:
            continue

        latest_ts_row = functools.reduce(lambda x, y: x if x["timestamp"] > y["timestamp"] else y, results)
        author_emojis[emoji_name].append(len(results))
        last_used = datetime.fromisoformat(latest_ts_row["timestamp"]).replace(tzinfo=timezone.utc)
        author_emojis[emoji_name].append(last_used.astimezone(pytz.timezone(tz)).strftime("%B %d, %Y %I:%M %p"))

    success_placeholder.success("Member cache refreshed!")
    time.sleep(0.7)
    success_placeholder.empty()
    return author_emojis

def fetch_author_emoji_from_db(pk, author_id):
    return emoji_events.get_all_emojis_by_author(pk, author_id)

session_state = get(password='')

if session_state.password != st.secrets["config"]["password"]:
    pwd_placeholder = st.empty()
    bar_placeholder = st.empty()
    loading_placeholder = st.empty()
    err_placeholder = st.empty()

    pwd = pwd_placeholder.text_input("Password:", value="", type="password")
    session_state.password = pwd
    if session_state.password == st.secrets["config"]["password"]:
        pwd_placeholder.empty()
        err_placeholder.empty()

        loading_msg_1 = random.choice(LOADING_MESSAGES)
        loading_msg_2 = random.choice(LOADING_MESSAGES)
        loading_msg_3 = random.choice(LOADING_MESSAGES)
        loading_msg_4 = random.choice(LOADING_MESSAGES)

        bar_placeholder.progress(0)
        loading_placeholder.info(loading_msg_1)
        for percent_complete in range(100):
            time.sleep(0.1)

            if percent_complete < 25:
                loading_placeholder.info(loading_msg_1)
            if percent_complete > 25 and percent_complete < 50:
                loading_placeholder.info(loading_msg_2)
            if percent_complete > 50 and percent_complete < 75:
                loading_placeholder.info(loading_msg_3)
            if percent_complete > 75:
                loading_placeholder.info(loading_msg_4)

            bar_placeholder.progress(percent_complete + 1)

        loading_placeholder.empty()
        bar_placeholder.empty()
        render()
    elif session_state.password == "":
        err_placeholder.error("This site is locked. Please enter the password to continue")
    else:
        err_placeholder.error("Wrong password entered, please try again")

else:
    render()
