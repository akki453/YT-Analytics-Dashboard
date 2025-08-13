
from sqlalchemy import create_engine
import pandas as pd
from googleapiclient.discovery import build
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
import urllib.parse

import seaborn as sns
import matplotlib.pyplot as plt
import requests
import matplotlib.ticker as ticker
import re
import nltk
from nltk.corpus import stopwords
from transformers import pipeline
from bertopic import BERTopic
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from urllib.parse import quote_plus
load_dotenv()
def get_youtube_service():
    return build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY"))
from extract import (
    get_top_channels_by_keyword,
    get_channel_metadata_by_keyword,
    get_uploads_playlist_id,
    get_all_videos_from_playlist,
    get_channel_by_id
)
from transform import channel_transform,video_transform
from load import (upload_channel,upload_videos)


user = os.getenv("POSTGRES_USER")
password = quote_plus(os.getenv("POSTGRES_PASSWORD"))  # URL-encode special chars
host = os.getenv("POSTGRES_HOST")
port = os.getenv("POSTGRES_PORT", 5432)
db = os.getenv("POSTGRES_DB")

engine = create_engine(
    f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}'
)


def render_channel_card(channel):
    # Create a container to isolate each card
    with st.container():
        # Button key (needed for consistency)
        button_key = f"view_{channel['channel_id']}"

        # Create the HTML content and place the button just before closing the card
        st.markdown(f"""
        <div style="
            border: 1px solid rgba(200,200,200,0.2);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            background-color: rgba(255, 255, 255, 0.01);
        ">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <img src="{channel['thumbnail']}" 
                     style="border-radius: 50%; width: 80px; height: 80px; margin-right: 20px;">
                <div style="color: inherit;">
                    <h4 style="margin: 0; padding: 0;">{channel['title']}</h4>
                    <a href="{channel['channel_url']}" target="_blank" style="font-size: 14px; color: #1f77f2;">
                        Visit Channel
                    </a>
                    <p style="margin: 5px 0 0 0; font-size: 14px;">
                        <strong>Subscribers:</strong> {channel['subscriber_count']:,} |
                        <strong>Videos:</strong> {channel['video_count']} |
                        <strong>Views:</strong> {channel['view_count']:,}
                    </p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Button visually and logically inside the card
        if st.button("View Details", key=button_key):
            st.session_state['selected_channel'] = channel

        # Close the HTML div after the button
        st.markdown("</div>", unsafe_allow_html=True)


def show_channel_tabs(channel):
    st.markdown(f"# 📺 {channel['title']}")
    st.markdown(f"🔗 [Open on YouTube]({channel['channel_url']})")
    st.markdown(f"**Subscribers:** {channel['subscriber_count']:,} | **Videos:** {channel['video_count']} | **Views:** {channel['view_count']:,}")
   

    playlist_id = get_uploads_playlist_id(channel['channel_id'])
    videos = get_all_videos_from_playlist(playlist_id)
    df_channel=channel_transform(channel)
    upload_channel(df_channel)

    df_final=video_transform(videos,channel)
    upload_videos(df_final)

    tab1, tab2, tab4 = st.tabs(["📘 Channel Description", "🎥 All Videos", "📊 Analysis"])
    
    with tab1:
        st.markdown(f"**Description**:\n\n{channel['description'] or 'No description available.'}")
        st.markdown(f"**Published at:** {channel['published_at']}")
        st.markdown(f"**Country:** {channel['country']}")
    
    with tab2:
        st.subheader("🎥 All Videos by the Creator")

        query = "SELECT * FROM videos"

        try:
            df_videos = pd.read_sql(query, con=engine)
            df_videos['published_at'] = pd.to_datetime(df_videos['published_at'])

            # --- Sorting ---
            sort_by = st.selectbox(
                "🔽 Sort By",
                options=["Newest First", "Oldest First", "Most Viewed", "Least Viewed"],
                key="video_sort"
            )

            # --- Sorting logic ---
            if sort_by == "Newest First":
                df_videos = df_videos.sort_values(by="published_at", ascending=False)
            elif sort_by == "Oldest First":
                df_videos = df_videos.sort_values(by="published_at", ascending=True)
            elif sort_by == "Most Viewed":
                df_videos = df_videos.sort_values(by="views", ascending=False)
            elif sort_by == "Least Viewed":
                df_videos = df_videos.sort_values(by="views", ascending=True)

            # --- Pagination setup ---
            videos_per_page = 20
            total_videos = len(df_videos)
            total_pages = (total_videos - 1) // videos_per_page + 1

            if "video_page" not in st.session_state:
                st.session_state.video_page = 1

            # --- Pagination buttons ---
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("⬅️ Previous") and st.session_state.video_page > 1:
                    st.session_state.video_page -= 1
                    st.experimental_rerun()

            with col3:
                if st.button("Next ➡️") and st.session_state.video_page < total_pages:
                    st.session_state.video_page += 1
                    st.experimental_rerun()

            with col2:
                st.markdown(f"<div style='text-align: center;'>Page {st.session_state.video_page} of {total_pages}</div>", unsafe_allow_html=True)

            # --- Slice DataFrame ---
            start_idx = (st.session_state.video_page - 1) * videos_per_page
            end_idx = start_idx + videos_per_page
            current_page_videos = df_videos.iloc[start_idx:end_idx]

            # --- Display Videos ---
            for _, row in current_page_videos.iterrows():
                video_url = f"https://www.youtube.com/watch?v={row['video_id']}"
                published_str = row['published_at'].strftime('%Y-%m-%d')

                st.markdown(f"""
                    <div style="border: 1px solid rgba(255,255,255,0.2); border-radius: 10px; padding: 15px; margin-bottom: 15px; background-color: rgba(255,255,255,0.05);">
                        <div style="display: flex; align-items: center;">
                            <iframe width="200" height="110" 
                                    src="https://www.youtube.com/embed/{row['video_id']}" 
                                    frameborder="0" allowfullscreen 
                                    style="margin-right: 20px; border-radius: 10px;">
                            </iframe>
                            <div style="flex: 1;">
                                <h4>{row['video_title']}</h4>
                                <p><strong>Views:</strong> {row['views']:,} | <strong>Likes:</strong> {row['likes']:,}</p>
                                <p><strong>Published:</strong> {published_str}</p>
                                <a href="{video_url}" target="_blank" style="color: #1f77f2;">🔗 Watch on YouTube</a>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ Failed to load videos: {e}")

  
    
    with tab4:
        st.subheader("📊 Channel Video Analytics")
        
        # Convert to DataFrame again if needed
        df_final['published_at'] = pd.to_datetime(df_final['published_at'])

        st.markdown("### 📈 Video Uploads Over Time")
        uploads_per_month = df_final.groupby(df_final['published_at'].dt.to_period('M')).size()
        
        fig1, ax1 = plt.subplots(figsize=(10, 4))
        uploads_per_month.plot(kind='bar', ax=ax1, color='skyblue')
        ax1.set_title("Video Uploads Per Month")
        ax1.set_xlabel("Month")
        ax1.set_ylabel("Number of Videos")
        st.pyplot(fig1)

        st.markdown("### 🔝 Top 10 Most Viewed Videos")
        if 'views' in df_final.columns:
            top_videos = df_final.sort_values(by='views', ascending=False).head(10)
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            sns.barplot(y='video_title', x='views', data=top_videos, ax=ax2, palette='viridis')
            ax2.set_title("Top 10 Most Viewed Videos")
            ax2.set_xlabel("Views")
            ax2.set_ylabel("Video Title")
            st.pyplot(fig2)
        else:
            st.warning("Views data not available for videos.")

        st.markdown("### 📆 Upload Frequency by Day of Week")
        df_final['day_of_week'] = df_final['published_at'].dt.day_name()
        uploads_by_day = df_final['day_of_week'].value_counts().reindex(
            ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        )

        fig3, ax3 = plt.subplots()
        sns.barplot(x=uploads_by_day.index, y=uploads_by_day.values, ax=ax3, palette='coolwarm')
        ax3.set_title("Uploads by Day of the Week")
        ax3.set_ylabel("Number of Videos")
        ax3.set_xticklabels(ax3.get_xticklabels(), rotation=45)
        st.pyplot(fig3)

        st.markdown("### 📅 Heatmap: Views by Publish Date")
        if 'views' in df_final.columns:
            heatmap_df = df_final[['published_at', 'views']].copy()
            heatmap_df['date'] = heatmap_df['published_at'].dt.date
            daily_views = heatmap_df.groupby('date')['views'].sum().reset_index()

            # Pivot the data into calendar-like format
            daily_views['day'] = daily_views['date'].apply(lambda d: d.day)
            daily_views['month'] = daily_views['date'].apply(lambda d: d.strftime('%b'))
            pivot_table = daily_views.pivot_table(index='day', columns='month', values='views', fill_value=0)

            fig4, ax4 = plt.subplots(figsize=(12, 6))
            sns.heatmap(pivot_table, cmap='YlGnBu', ax=ax4)
            ax4.set_title("Heatmap of Views by Publish Date")
            st.pyplot(fig4)
        else:
            st.warning("Views data not available for heatmap.")


        st.markdown("### 🏷️ Most Popular Video Categories")
        if 'category' in df_final.columns:
            category_counts = df_final['category'].value_counts().head(10)

            fig5, ax5 = plt.subplots(figsize=(10, 5))
            sns.barplot(x=category_counts.values, y=category_counts.index, ax=ax5, palette='Set2')
            ax5.set_title("Top 10 Most Frequent Video Categories")
            ax5.set_xlabel("Number of Videos")
            ax5.set_ylabel("Category")
            st.pyplot(fig5)
        else:
            st.warning("Category data not available for videos.")

        st.markdown("### 🎯 Total Views by Category")
        if 'category' in df_final.columns and 'views' in df_final.columns:
            category_views = (
                df_final.groupby('category')['views']
                .sum()
                .sort_values(ascending=False)
                .head(10)
            )

            fig6, ax6 = plt.subplots(figsize=(10, 5))
            sns.barplot(x=category_views.values, y=category_views.index, ax=ax6, palette='Spectral')
            ax6.set_title("Top 10 Categories by Total Views")
            ax6.set_xlabel("Total Views")
            ax6.set_ylabel("Category")

            # ✅ Format x-axis ticks in Millions
            ax6.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x/1e6:.1f}M'))

            st.pyplot(fig6)
        else:
            st.warning("Either 'category' or 'views' data is missing.")
        #sst.success("✔️ Analytics generated using video data.")



if 'selected_channel' not in st.session_state:
    st.session_state['selected_channel'] = None


with st.sidebar:
    menu = option_menu('YouTube Channel Analysis Dashboard', [
        'Search Channels',
        'Search Videos'
    ],
        default_index=0,
        styles={
            "container": {"padding": "5px", "background-color": "#2C2E30"},
            "icon": {"color": "orange", "font-size": "18px"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px"},
            "nav-link-selected": {"background-color": "#f00606"},
        })


if menu == 'Search Channels':
    st.title('🔍 Search YouTube Channels')
    keyword = st.text_input("Enter keyword to search channels", value="")

    # Create two columns for side-by-side buttons
    col1, col2 = st.columns([1, 1])

    with col1:
        search_clicked = st.button("Search by keyword")

    with col2:
        alt_search_clicked = st.button("Search By channel ID")

    # Separate logic for each button
    if search_clicked:
        max_results = 5
        with st.spinner("Fetching data..."):
            try:
                url = f"http://localhost:8000/channels?keyword={keyword}&max_results={max_results}"
                response = requests.get(url)

                if response.status_code == 200:
                    st.session_state['channels'] = response.json()
                    st.session_state['selected_channel'] = None
                else:
                    st.error(f"Server returned status code {response.status_code}")
                    st.text(f"Response content: {response.text}")
                    st.session_state['channels'] = []
            except Exception as e:
                st.error("Failed to fetch data.")
                st.exception(e)

    if alt_search_clicked:
        # You can modify this block to behave differently later
        st.session_state['channels'] = get_channel_by_id(keyword)
        st.session_state['selected_channel'] = None

    # If a channel is selected, show tabs
    if st.session_state['selected_channel']:
        show_channel_tabs(st.session_state['selected_channel'])

    # If no channel is selected, show search results
    elif 'channels' in st.session_state:
        for ch in st.session_state['channels']:
            render_channel_card(ch)
elif menu == 'Search Videos':
    st.title('🎥 Search YouTube Videos')
    video_input = st.text_input("Enter keyword or video ID to search videos", value="")

    vcol1, vcol2 = st.columns([1, 1])
    with vcol1:
        video_keyword_search = st.button("Search by keyword")

    with vcol2:
        video_id_search = st.button("Search by video ID")

    # Perform search and store in session_state (triggers rerun)
    if video_keyword_search:
        max_results = 5
        try:
            youtube = get_youtube_service()
            request = youtube.search().list(
                q=video_input,
                part="snippet",
                type="video",
                maxResults=max_results
            )
            response = request.execute()
            st.session_state['videos'] = response.get("items", [])
            st.session_state['selected_video'] = None
        except Exception as e:
            st.error("Error fetching videos")
            st.exception(e)

    if video_id_search:
        try:
            youtube = get_youtube_service()
            request = youtube.videos().list(
                id=video_input,
                part="snippet,statistics"
            )
            response = request.execute()
            st.session_state['videos'] = response.get("items", [])
            st.session_state['selected_video'] = None
        except Exception as e:
            st.error("Error fetching video by ID")
            st.exception(e)

    # Render video search results
    if 'videos' in st.session_state and not st.session_state.get('selected_video'):
        for vid in st.session_state['videos']:
            snippet = vid.get("snippet", {})
            title = snippet.get("title", "No title")
            channel_title = snippet.get("channelTitle", "Unknown Channel")
            thumbnail_url = snippet.get("thumbnails", {}).get("medium", {}).get("url", "")
            video_id = vid["id"]["videoId"] if isinstance(vid.get("id"), dict) else vid.get("id")

            with st.container():
                st.image(thumbnail_url, width=320)
                st.subheader(title)
                st.caption(f"📺 Channel: {channel_title}")
                st.markdown(f"[Watch on YouTube](https://www.youtube.com/watch?v={video_id})", unsafe_allow_html=True)

                if st.button(f"View Details", key=f"view_{video_id}"):
                    st.session_state['selected_video'] = video_id  # Set selected video ID

            st.markdown("---")

    # Show selected video details (on next rerun)
    if st.session_state.get('selected_video'):
        with st.spinner("Loading video details..."):
            try:
                youtube = get_youtube_service()
                request = youtube.videos().list(
                    id=st.session_state['selected_video'],
                    part="snippet,statistics"
                )
                response = request.execute()
                video = response["items"][0]

                snippet = video["snippet"]
                stats = video["statistics"]

                st.markdown("## 📊 Video Details")
                st.video(f"https://www.youtube.com/watch?v={st.session_state['selected_video']}")
                st.markdown(f"**Title:** {snippet.get('title')}")
                st.markdown(f"**Channel:** {snippet.get('channelTitle')}")
                st.markdown(f"**Published At:** {snippet.get('publishedAt')}")
                st.markdown(f"**Description:** {snippet.get('description')}")
                st.markdown(f"**Views:** {int(stats.get('viewCount', 0)):,}")
                st.markdown(f"**Likes:** {int(stats.get('likeCount', 0)):,}")
                st.markdown(f"**Comments:** {int(stats.get('commentCount', 0)):,}")
           


                sentiment_model = pipeline("sentiment-analysis")

                # Clean comment text
                def clean_text(text):
                    text = text.lower()
                    text = re.sub(r"http\S+", "", text)
                    text = re.sub(r"[^a-z\s]", "", text)
                    text = re.sub(r"\s+", " ", text).strip()
                    return text

                # Fetch top 100 comments for selected video
                def get_video_comments(video_id):
                    youtube = get_youtube_service()
                    comments = []
                    try:
                        request = youtube.commentThreads().list(
                            part="snippet",
                            videoId=video_id,
                            maxResults=100,
                            textFormat="plainText"
                        )
                        response = request.execute()
                        for item in response["items"]:
                            comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                            comments.append(comment)
                    except Exception as e:
                        st.warning("Failed to fetch comments")
                        st.exception(e)
                    return comments

                # Step 1: Get and clean comments
                comments = get_video_comments(st.session_state['selected_video'])
                cleaned_comments = [clean_text(c) for c in comments if c.strip()]

                if cleaned_comments:
                    st.markdown("## 💬 Comment Analysis")

                    # Step 2: Sentiment analysis
                    with st.spinner("Analyzing sentiment..."):
                        sentiments = sentiment_model(cleaned_comments)

                    df_sentiment = pd.DataFrame({
                        "comment": comments,
                        "sentiment": [s["label"] for s in sentiments],
                        "score": [s["score"] for s in sentiments]
                    })

                    # Display sentiment chart
                    st.markdown("### 📊 Sentiment Distribution")
                    sentiment_counts = df_sentiment["sentiment"].value_counts()
                    st.bar_chart(sentiment_counts)

                    # Show example comments
                    st.markdown("### ✨ Sample Comments")
                    st.dataframe(df_sentiment.head(10))

                else:
                    st.info("No comments found to analyze.")
                if st.button("🔙 Back to Search Results"):
                    st.session_state['selected_video'] = None
                

            except Exception as e:
                st.error("Failed to load video details.")
                st.exception(e)
            




