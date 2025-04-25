import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import datetime
import plotly.express as px 
import ast


st.title('Uber pickups in NYC')

DATE_COLUMN = 'date/time'
DATA_URL = ('https://s3-us-west-2.amazonaws.com/'
         'streamlit-demo-data/uber-raw-data-sep14.csv.gz')
@st.cache_data
def load_data(nrows):
    data = pd.read_csv(DATA_URL, nrows=nrows)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns', inplace=True)
    data[DATE_COLUMN] = pd.to_datetime(data[DATE_COLUMN])
    return data

# Create a text element and let the reader know the data is loading.
data_load_state = st.text('Loading data...')
# Load 10,000 rows of data into the dataframe.
data = load_data(10000)
# Notify the reader that the data was successfully loaded.
data_load_state.text('Loading data...done!')

st.subheader("Raw Data")
st.write(data)

 
st.subheader("Number of pickups by hour")
hist_values = np.histogram(
    data[DATE_COLUMN].dt.hour,bins=24,range=(0,24))[0]
st.bar_chart(hist_values)
 
st.subheader("2D Map of Pickups in NYC")
st.map(data)
hour_to_filter = st.slider('hour', 0, 23, 17)
filtered_data = data[data[DATE_COLUMN].dt.hour == hour_to_filter]
st.subheader(f'Map of all pickups at {hour_to_filter}:00')
st.map(filtered_data)


selected_date = st.date_input("Select a date", value=datetime.date(2014, 9, 1))

filtered_data = data[
    (data[DATE_COLUMN].dt.date == selected_date)] 

filtered_data['latlon_str'] = filtered_data.apply(
    lambda row: f"({row['lat']}, {row['lon']})", axis=1)

selected_point = st.selectbox(
    "Select a location (only from selected date)",
    options=filtered_data['latlon_str'].dropna().unique()
)

# prevent error
try:
    if isinstance(selected_point, str):
        selected_lat, selected_lon = ast.literal_eval(selected_point)
    else:
        st.stop()
except Exception as e:
    st.error(f"error: {e}")
    st.stop()

highlight_point = pd.DataFrame([{
    'lat': selected_lat,
    'lon': selected_lon
}])

st.subheader("3D Map of Pickups by selected date")

st.pydeck_chart(
    pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=filtered_data['lat'].mean(),
            longitude=filtered_data['lon'].mean(),
            zoom=11,
            pitch=50,
        ),
        layers=[
            pdk.Layer(
                "HexagonLayer",
                data=filtered_data,
                get_position="[lon, lat]",
                radius=200,
                elevation_scale=4,
                elevation_range=[0, 1000],
                pickable=True,
                extruded=True,
            ),
            pdk.Layer(  
                "ScatterplotLayer",
                data=highlight_point,
                get_position="[lon, lat]",
                get_color="[255, 20, 147, 255]",  
                get_radius=500,
            ),
        ],
    )
)

# pickup
data['datetime_hour'] = data['date/time'].dt.floor('H') 

df_time = data.groupby('datetime_hour').size().reset_index(name='pickups')

filter_for_date = st.checkbox("Show selected date in line graph")

if filter_for_date:
    df_time = df_time[df_time['datetime_hour'].dt.date == selected_date]

color = st.color_picker("Pick A Color", "#00f900")

fig = px.line(
    df_time,
    x='datetime_hour',
    y='pickups',
    title='Number of Uber Pickups by Hour (Date-Time)',
)

fig.update_traces(line=dict(color=color), mode='lines+markers')

fig.update_layout(
    xaxis_title='Date-Time (Hour)',
    yaxis_title='Number of Pickups',
    template='plotly_white'
)

st.plotly_chart(fig, use_container_width=True)

# Run_count
if 'run_count' not in st.session_state:
    st.session_state.run_count = 0  

if st.button("Click to increase run count", type= "secondary"):
    st.session_state.run_count += 1

st.write(f"This page has run {st.session_state.run_count} times.")