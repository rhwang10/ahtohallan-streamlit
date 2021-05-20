import streamlit as st
import numpy as np
import pandas as pd

import time

st.title('My first updates')


with st.spinner(text='In progress'):
    time.sleep(5)
    st.success('Done')
