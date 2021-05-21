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

@st.cache(suppress_st_warning=True, ttl=0)
def render_emoji_alltime_data():
    tz = st.selectbox(label="Timezone", options=["US/Eastern", "US/Pacific"])
    data = get_alltime_data(tz)
    st.table(data)

def get_alltime_data(tz):

    metadata_all_time = fetch_from_db()

    m = defaultdict(list)
    for entry in metadata_all_time:
        emoji_name = parse_emoji_name(entry)
        last_used = datetime.fromisoformat(entry["timestamp"]).replace(tzinfo=timezone.utc)

        m[emoji_name].append(int(entry["count"]))
        m[emoji_name].append(last_used.astimezone(pytz.timezone(tz)).strftime("%B %d, %Y %I:%M %p"))


    return pd.DataFrame(m, index=["Count", "Last Used"])

@st.cache(ttl=1)
def fetch_from_db():
    return emoji_events.get_all_emojis()


render()
