import streamlit as st
import numpy as np
import pandas as pd
import pytz
import time
from collections import defaultdict
from datetime import datetime, timezone

from repository.emoji_events import EmojiEvents

emoji_events = EmojiEvents()

parse_emoji_name = lambda r: r["emoji_id|emoji_name"].split("|")[1] if isinstance(r, dict) else r.split("|")[1]

#TODO: Make this a metadata row in dynamo
AUTHOR_NAME_TO_ID = {
    "YenSid": "147812991264489472",
    "Big Bezos": "180493684557611009",
    "Jake N' Bake": "180493684557611009",
    "stefan": "362787354844463135",
    "ItsMike": "234159938916581397",
    "Biiig Chiiiick": "294691480029888522"
}

@st.cache(suppress_st_warning=True, ttl=1000, show_spinner=False)
def get_available_emojis():
    data = emoji_events.get_all_emojis()
    return [row["emoji_id|emoji_name"] for row in data]

CACHED_EMOJIS = get_available_emojis()

def parse_into_object(data, obj):
    for entry in data:
        emoji_name = parse_emoji_name(entry)
        last_used = datetime.fromisoformat(entry["timestamp"]).replace(tzinfo=timezone.utc)
        obj[emoji_name].append(int(entry["count"]))
        obj[emoji_name].append(last_used.astimezone(pytz.timezone(tz)).strftime("%B %d, %Y %I:%M %p"))

def render():
    render_emoji_alltime_data()
    render_author_emoji_data()

tz = st.selectbox(label="Timezone", options=["US/Eastern", "US/Pacific"])

def render_emoji_alltime_data():
    if st.button("Refresh cache"):
        st.caching.clear_cache()

    top_emoji_data, lru_data, mru_data = get_alltime_data(tz)

    st.header("All time most popular")
    st.table(top_emoji_data)

    st.header("Most recently used")
    st.table(mru_data)

    st.header("Least recently used")
    st.table(lru_data)


def render_author_emoji_data():
    st.header("Member usage")
    selected_author_name = st.selectbox(label="Member", options=[name for name, _ in AUTHOR_NAME_TO_ID.items()])
    selected_author_id = AUTHOR_NAME_TO_ID[selected_author_name]

    author_emojis = fetch_all_author_emoji_data_from_db(selected_author_id)

    df = pd.DataFrame(author_emojis, index=["Count", "Last Used"])
    st.table(df)


def get_alltime_data(tz):
    results = fetch_from_db()
    top_all_time = sorted(results, key=lambda item : item["count"], reverse=True)[:10]
    least_recently_used = sorted(results, key=lambda item : item["timestamp"])[:10]
    most_recently_used = sorted(results, key=lambda item : item["timestamp"], reverse=True)[:10]

    top_emojis = defaultdict(list)
    lru = defaultdict(list)
    mru = defaultdict(list)


    parse_into_object(top_all_time, top_emojis)
    parse_into_object(least_recently_used, lru)
    parse_into_object(most_recently_used, mru)


    return pd.DataFrame(top_emojis, index=["Count", "Last Used"]), \
           pd.DataFrame(lru, index=["Count", "Last Used"]), \
           pd.DataFrame(mru, index=["Count", "Last Used"])


# Cache values for 5 minutes to prevent crushing the DB
@st.cache(suppress_st_warning=True, ttl=300, show_spinner=False)
def fetch_from_db():
    st.success("Cache refreshed!")
    emoji_events_over_all_time = emoji_events.get_all_emojis()
    return emoji_events_over_all_time

# Cache values for 30 minutes to prevent crushing the DB
@st.cache(suppress_st_warning=True, ttl=1, show_spinner=False)
def fetch_all_author_emoji_data_from_db(author_id):
    author_emojis = defaultdict(list)
    for pk in CACHED_EMOJIS:
        emoji_name = parse_emoji_name(pk)
        # cached call, refreshes every 30 minutes
        results = fetch_author_emoji_from_db(pk, author_id)

        if not results:
            continue

        author_emojis[emoji_name].append(len(results))
        last_used = datetime.fromisoformat(results[0]["timestamp"]).replace(tzinfo=timezone.utc)
        author_emojis[emoji_name].append(last_used.astimezone(pytz.timezone(tz)).strftime("%B %d, %Y %I:%M %p"))
    st.success("Member cache refreshed!")
    return author_emojis

def fetch_author_emoji_from_db(pk, author_id):
    return emoji_events.get_all_emojis_by_author(pk, author_id)



render()
