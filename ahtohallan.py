import streamlit as st
import numpy as np
import pandas as pd
import pytz
import time
from collections import defaultdict
from datetime import datetime, timezone

from repository.emoji_events import EmojiEvents

emoji_events = EmojiEvents()
parse_emoji_name = lambda r: r["emoji_id|emoji_name"].split("|")[1]

def render():
    render_emoji_alltime_data()
    # render_emoji_date_data()

def render_emoji_alltime_data():
    tz = st.selectbox(label="Timezone", options=["US/Eastern", "US/Pacific"])
    if st.button("Refresh cache"):
        st.caching.clear_cache()
    data = get_alltime_data(tz)
    st.table(data)

def render_emoji_date_data():
    st.date_input("Pick a day")

def get_alltime_data(tz):

    metadata_all_time = fetch_from_db()

    m = defaultdict(list)
    for entry in sorted(metadata_all_time, key=lambda item : item["count"], reverse=True):
        emoji_name = parse_emoji_name(entry)
        last_used = datetime.fromisoformat(entry["timestamp"]).replace(tzinfo=timezone.utc)

        m[emoji_name].append(int(entry["count"]))
        m[emoji_name].append(last_used.astimezone(pytz.timezone(tz)).strftime("%B %d, %Y %I:%M %p"))


    return pd.DataFrame(m, index=["Count", "Last Used"])

# Cache values for 5 minutes to prevent crushing the DB
@st.cache(suppress_st_warning=True, ttl=300, show_spinner=False)
def fetch_from_db():
    st.success("Cache refreshed!")
    return emoji_events.get_all_emojis()

render()
