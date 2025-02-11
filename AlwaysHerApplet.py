import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

import streamlit as st

@st.cache_data
def songdata(show_spinner=True, ttl=15):
    silhouette = pd.read_csv("Silhouette (The Halloween Song)-timeline.csv")
    itb = pd.read_csv("In the Beginning-timeline.csv")
    erberger = pd.read_csv("Airport Girl-timeline.csv")
    mr_nice_guy = pd.read_csv( "Mr. Nice Guy-timeline.csv")
    my_brain = pd.read_csv("My Brain is Carrying the World-timeline.csv")
    olay = pd.read_csv("One Look at You - Acoustic-timeline.csv")
    prolly_nun = pd.read_csv("Probably Nothing - Acoustic-timeline.csv")
    savior = pd.read_csv("Savior - Acoustic-timeline.csv")
    itb_acous = pd.read_csv("In the Beginning - Acoustic-timeline.csv")
    erberger_acous = pd.read_csv("Airport Girl - Acoustic-timeline.csv")
    timeless = pd.read_csv("Timeless-timeline.csv")

    silhouette['song'] = 'Silhouette'
    itb['song'] = 'In the Beginning'
    erberger['song'] = 'Airport Girl'
    mr_nice_guy['song'] = 'Mr. Nice Guy'
    my_brain['song'] = 'My Brain is Carrying the World'
    olay['song'] = 'One Look At You - Acoustic'
    prolly_nun['song'] = 'Probably Nothing - Acoustic'
    savior['song'] = 'Savior - Acoustic'
    itb_acous['song'] = 'In the Beginning - Acoustic'
    erberger_acous['song'] = 'Airport Girl - Acoustic'
    timeless['song'] = 'Timeless'

    combined_songs = pd.concat([silhouette, itb, erberger, mr_nice_guy, my_brain,
                            olay, prolly_nun, savior, itb_acous, erberger_acous, timeless])

    combined_songs['date'] = pd.to_datetime(combined_songs['date'])

    return combined_songs


# App code

song_data = songdata()


st.title("Always Her Spotify Stats")

song_titles = ['Silhouette', 'In the Beginning', 'Airport Girl', 'Mr. Nice Guy', 
               'My Brain is Carrying the World', 'One Look At You - Acoustic',
               'Probably Nothing - Acoustic', 'Savior - Acoustic',
               'In the Beginning - Acoustic', 'Airport Girl - Acoustic', 'Timeless']
selected_songs = st.sidebar.multiselect(
    "Select Songs", options=song_titles, default=song_titles)

data_by_song = song_data[song_data['song'].isin(selected_songs)]


# For tab1 col1
song_summary = (data_by_song[data_by_song["streams"] > 0]
                .groupby('song', as_index=False)
                .agg(Streams=('streams', 'sum'),
                     Release_Date=('date', 'min')))

song_summary["Release_Date"] = pd.to_datetime(song_summary["Release_Date"])
today = pd.to_datetime("today")
song_summary["Days"] = (today - song_summary["Release_Date"]).dt.days

song_summary["streams_per_day"] = song_summary["Streams"] / song_summary["Days"]

song_summary = song_summary.sort_values(by='Streams', ascending=False)

grand_total = song_summary["Streams"].sum()


# For tab1, col2
scatter_data = song_summary.copy()

plt.style.use('dark_background')
colors = plt.cm.get_cmap("tab20", len(scatter_data))


# For tab1 col3

def calculate_growth_rate(group):
    group['avg_last_10_days'] = group['streams'].rolling(window=10, min_periods=1).mean()
    group['avg_prior_10_days'] = group['streams'].shift(10).rolling(window=10, min_periods=1).mean()
    
    group['growth_rate'] = ((group['avg_last_10_days'] - group['avg_prior_10_days']) / group['avg_prior_10_days']) * 100

    return group

data_by_song = data_by_song.groupby('song', group_keys=False).apply(calculate_growth_rate)

growth_rate_per_song = (data_by_song.dropna(subset=['growth_rate'])  # Remove NaN values
                        .groupby('song', as_index=False)
                        .agg({'growth_rate': 'last'})  # Take last non-null value
                        .sort_values(by='growth_rate', ascending=False))




tab1, tab2 = st.tabs(['General Stats', 'Cumulative Weekly Streams'])

with tab1:

    col1 = st.columns([1])[0]

    with col1:
        st.subheader("Total Streams & Days Since Release")
        song_summary = song_summary.rename(columns={'song': 'Song', 'Days': 'Days Since Release', 'streams_per_day': 'Streams Per Day' })
        song_summary_col1 = song_summary.drop(columns='Release_Date')
        st.data_editor(song_summary_col1, hide_index=True, use_container_width=True, height=422)
        st.write(f"**Grand Total Streams**: {grand_total}")

    col2 = st.columns([1])[0]

    with col2:
        st.subheader("Days Since Release vs. Streams")
        fig, ax = plt.subplots()

        for idx, (song, days, streams) in enumerate(zip(scatter_data["song"], scatter_data["Days"], scatter_data["Streams"])):
            ax.scatter(days, streams, color=colors(idx), label=song, s=15, alpha=0.8)  

        # Trendline Calculation
        x = scatter_data["Days"]
        y = scatter_data["Streams"]
        
        if len(x) > 1:
            coeffs = np.polyfit(x, y, deg=1)
            trendline = np.poly1d(coeffs)  
            sorted_x = np.sort(x)
            ax.plot(sorted_x, trendline(sorted_x), linestyle="dashed", color="white", alpha=0.7, linewidth=0.8, label="Trendline")

        # Labels & Formatting
        ax.set_xlabel("Days Since Release", color='white')
        ax.set_ylabel("Total Streams", color='white')
        ax.grid(True, linestyle='--', color='gray', alpha=0.5)
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=3)

        st.pyplot(fig)

    col3 = st.columns([1])[0]

    with col3:
        st.subheader("10-day Moving Growth Rate")
        growth_rate_per_song = growth_rate_per_song.rename(columns={'song': 'Song', 'growth_rate': 'Growth Rate %'})
        st.dataframe(growth_rate_per_song, hide_index=True, use_container_width=True, height = 423)

        with st.expander("See explanation"):
            st.write("""
                The 10-day moving growth rate is calculated by taking the average streams of a given song for 
                the past 10 days and comparing to its own average streams for the 10 days prior
                to that. For example, if a song has a 10-day growth rate of 15%, that means it was streamed
                about 15% more than in the 10 day period before.
                    """)



    with tab2:

        st.subheader("Average Daily Streams per Song")
        view_option = st.radio("Select View", ["Daily Average Streams", "Weekly Average Streams"])

        # Filter data to only include songs released after the earliest release date
        earliest_release_date = song_summary["Release_Date"].min()
        filtered_data = data_by_song[data_by_song["date"] >= earliest_release_date].copy()

        # Calculate Daily or Weekly Average Streams
        if view_option == "Weekly Average Streams":
            filtered_data = (filtered_data
                            .groupby(pd.Grouper(key="date", freq="W"))["streams"]
                            .mean()
                            .reset_index()
                            .rename(columns={"streams": "Weekly Streams"}))
            y_column = "Weekly Streams"
        else:
            # For Daily Average Streams, calculate the sum of streams per day and divide by number of songs on each day
            daily_avg_streams = (filtered_data
                                .groupby(pd.Grouper(key="date", freq="D"))["streams"]
                                .sum()
                                .reset_index(name="Total Daily Streams"))

            # Count number of songs that have streams on each day
            daily_song_count = (filtered_data[filtered_data["streams"] > 0]
                                .groupby(pd.Grouper(key="date", freq="D"))
                                .size()
                                .reset_index(name="Song Count"))
            
            # Merge the two datasets and calculate the daily average streams
            daily_avg_streams = daily_avg_streams.merge(daily_song_count, on="date", how="left")
            daily_avg_streams["Daily Average Streams"] = daily_avg_streams["Total Daily Streams"] / daily_avg_streams["Song Count"]
            
            y_column = "Daily Average Streams"

        # Compute the total number of songs released up until each date
        total_songs_released = song_summary.groupby(pd.Grouper(key="Release_Date", freq="D"))["Release_Date"].count().reset_index(name="Total Songs")
        total_songs_released = total_songs_released.sort_values("Release_Date")

        # Merge the total number of songs released with the filtered data
        merged_data = daily_avg_streams.merge(total_songs_released, left_on="date", right_on="Release_Date", how="left")

        # Plot both lines: average streams and total songs
        st.line_chart(merged_data.set_index("date")[["Total Songs", y_column]], use_container_width=True, color=["#B55BF0", "#1DB954"])