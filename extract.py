from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
import json
import pandas as pd
import requests
import streamlit as st
import re
import nltk
from nltk.corpus import stopwords
from transformers import pipeline
from bertopic import BERTopic
API_URL = "https://yt-analytics-dashboard.onrender.com"
api_key = 'AIzaSyDuU1qaxesSqxUVVWgLZObVddbPD57AmB8'
youtube = build('youtube', 'v3', developerKey=api_key)
def get_top_channels_by_keyword(keyword, max_results=5):
    # Step 1: Search for channels by keyword
    search_response = youtube.search().list(
        part='snippet',
        q=keyword,
        type='channel',
        maxResults=max_results
    ).execute()

    channels_data = []

    for item in search_response['items']:
        snippet = item['snippet']
        channel_id = snippet['channelId']

        # Step 2: Fetch channel statistics + metadata
        channel_response = youtube.channels().list(
            part='snippet,statistics',
            id=channel_id
        ).execute()

        if channel_response['items']:
            channel_info = channel_response['items'][0]
            stats = channel_info['statistics']
            snippet_info = channel_info['snippet']

            # Step 3: Append formatted dict to list
            channel_dict = {
                'channel_id': channel_id,
                'title': snippet_info.get('title'),
                'description': snippet_info.get('description'),
                'published_at': snippet_info.get('publishedAt'),
                'country': snippet_info.get('country', 'N/A'),
                'subscriber_count': int(stats.get('subscriberCount', 0)),
                'video_count': int(stats.get('videoCount', 0)),
                'view_count': int(stats.get('viewCount', 0)),
                'channel_url': f"https://www.youtube.com/channel/{channel_id}",
                'thumbnail': snippet_info.get('thumbnails', {}).get('default', {}).get('url', '')
            }
            
            channel_dict['published_at']=channel_dict['published_at'][0:10]
            if(channel_dict['video_count']):
                channel_dict['avg_views']=round(channel_dict['view_count']/channel_dict['video_count'])
            channels_data.append(channel_dict)

    return channels_data





def get_channel_metadata_by_keyword(keyword):
    # Step 1: Search for the channel by keyword
    search_response = youtube.search().list(
        part='snippet',
        q=keyword,
        type='channel',
        maxResults=1
    ).execute()

    if not search_response['items']:
        print("❌ No channel found.")
        return None

    channel_id = search_response['items'][0]['snippet']['channelId']

    # Step 2: Get channel statistics and metadata
    channel_response = youtube.channels().list(
        part='snippet,statistics',
        id=channel_id
    ).execute()

    if not channel_response['items']:
        print("❌ Channel data could not be retrieved.")
        return None

    channel = channel_response['items'][0]
    snippet = channel['snippet']
    stats = channel['statistics']

    metadata = {
        'channel_id': channel_id,
        'title': snippet.get('title'),
        'description': snippet.get('description'),
        'published_at': snippet.get('publishedAt'),
        'country': snippet.get('country', 'N/A'),
        'subscriber_count': int(stats.get('subscriberCount', 0)),
        'video_count': int(stats.get('videoCount', 0)),
        'view_count': int(stats.get('viewCount', 0)),
        'channel_url': f"https://www.youtube.com/channel/{channel_id}"
    }
    return metadata

def get_uploads_playlist_id(channel_id):
    """Call FastAPI to get uploads playlist ID"""
    response = requests.get(f"{API_URL}/uploads_playlist_id/{channel_id}")
    if response.status_code == 200:
        return response.json()['uploads_playlist_id']
    else:
            #st.error(f"Error fetching uploads playlist: {response.text}")
        return None
def get_all_videos_from_playlist(playlist_id):
    """Call FastAPI to get all videos from the playlist"""
    response = requests.get(f"{API_URL}/all_videos/{playlist_id}")
    if response.status_code == 200:
        return response.json()
    else:
        #st.error(f"Error fetching videos: {response.text}")
        return []


def get_channel_by_id(id):
    # Step 1: Fetch channel statistics + metadata
    channel_response = youtube.channels().list(
        part='snippet,statistics',
        id=id
    ).execute()

    if not channel_response['items']:
        return None  # Channel not found

    channel_info = channel_response['items'][0]
    stats = channel_info['statistics']
    snippet_info = channel_info['snippet']

    # Step 2: Build and return the channel dictionary
    channel_dict = {
        'channel_id': id,
        'title': snippet_info.get('title'),
        'description': snippet_info.get('description'),
        'published_at': snippet_info.get('publishedAt')[0:10],
        'country': snippet_info.get('country', 'N/A'),
        'subscriber_count': int(stats.get('subscriberCount', 0)),
        'video_count': int(stats.get('videoCount', 0)),
        'view_count': int(stats.get('viewCount', 0)),
        'channel_url': f"https://www.youtube.com/channel/{id}",
        'thumbnail': snippet_info.get('thumbnails', {}).get('default', {}).get('url', '')
    }

    if channel_dict['video_count']:
        channel_dict['avg_views'] = round(channel_dict['view_count'] / channel_dict['video_count'])

    return [channel_dict]

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

