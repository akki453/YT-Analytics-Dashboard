# main.py (FastAPI backend)
from fastapi import FastAPI, Query,HTTPException
from typing import List, Optional
from pydantic import BaseModel
from googleapiclient.discovery import build
from typing import List
import os
from fastapi.middleware.cors import CORSMiddleware



# Set up YouTube API
api_key = 'Enter your yt-data API key'
youtube = build('youtube', 'v3', developerKey=api_key)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with your Streamlit frontend URL for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Response model
class ChannelInfo(BaseModel):
    channel_id: str
    title: str
    description: str
    published_at: str
    country: str
    subscriber_count: int
    video_count: int
    view_count: int
    avg_views: Optional[int] = None
    channel_url: str
    thumbnail: str


class VideoInfo(BaseModel):
    title: str
    video_id: str
    published_at: str
    views: int
    likes: int
    category: str
def get_category_mapping(region_code="IN") -> dict:
    categories = youtube.videoCategories().list(
        part='snippet',
        regionCode=region_code
    ).execute()

    return {item["id"]: item["snippet"]["title"] for item in categories["items"]}
@app.get("/channels", response_model=List[ChannelInfo])
def get_channels(keyword: str = Query(...), max_results: int = Query(5, le=50)):
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

        channel_response = youtube.channels().list(
            part='snippet,statistics',
            id=channel_id
        ).execute()

        if channel_response['items']:
            channel_info = channel_response['items'][0]
            stats = channel_info['statistics']
            snippet_info = channel_info['snippet']

            channel_dict = {
                'channel_id': channel_id,
                'title': snippet_info.get('title'),
                'description': snippet_info.get('description'),
                'published_at': snippet_info.get('publishedAt', '')[0:10],
                'country': snippet_info.get('country', 'N/A'),
                'subscriber_count': int(stats.get('subscriberCount', 0)),
                'video_count': int(stats.get('videoCount', 0)),
                'view_count': int(stats.get('viewCount', 0)),
                'channel_url': f"https://www.youtube.com/channel/{channel_id}",
                'thumbnail': snippet_info.get('thumbnails', {}).get('default', {}).get('url', '')
            }

            if channel_dict['video_count']:
                channel_dict['avg_views'] = round(channel_dict['view_count'] / channel_dict['video_count'])

            channels_data.append(channel_dict)

    return channels_data


@app.get("/uploads_playlist_id/{channel_id}")
def get_uploads_playlist_id(channel_id: str):
    try:
        request = youtube.channels().list(
            part='contentDetails',
            id=channel_id
        )
        response = request.execute()

        return {
            "uploads_playlist_id": response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to fetch all video details including category
@app.get("/all_videos/{playlist_id}", response_model=List[VideoInfo])
def get_all_videos_from_playlist(playlist_id: str):
    try:
        videos = []
        next_page_token = None
        category_map = get_category_mapping()  # 🔁 Map categoryId to name

        while True:
            request = youtube.playlistItems().list(
                part='snippet',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()

            video_ids = []
            video_snippets = {}

            for item in response['items']:
                snippet = item['snippet']
                video_id = snippet['resourceId']['videoId']
                video_ids.append(video_id)
                video_snippets[video_id] = {
                    'title': snippet['title'],
                    'published_at': snippet['publishedAt']
                }

            # Batch call to get video stats + snippet (for categoryId)
            stats_request = youtube.videos().list(
                part='statistics,snippet',
                id=','.join(video_ids)
            )
            stats_response = stats_request.execute()

            for item in stats_response['items']:
                vid = item['id']
                stats = item['statistics']
                snippet = item['snippet']
                category_id = snippet.get('categoryId', '')
                category_name = category_map.get(category_id, 'Unknown')

                video_info = {
                    'title': video_snippets[vid]['title'],
                    'video_id': vid,
                    'published_at': video_snippets[vid]['published_at'],
                    'views': int(stats.get('viewCount', 0)),
                    'likes': int(stats.get('likeCount', 0)),
                    'category': category_name
                }
                videos.append(video_info)

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

        return videos

    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))
