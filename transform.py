import pandas as pd

def channel_transform(channel: dict) -> pd.DataFrame:
  
    # Add avg_views field
    if channel.get('video_count', 0):
        channel['avg_views'] = round(channel['view_count'] / channel['video_count'])
    else:
        channel['avg_views'] = 0

    # Convert to DataFrame
    df_channel = pd.DataFrame([channel])

    # Process publish date
    df_channel['published_at'] = df_channel['published_at'].astype(str).str[0:10]
    df_channel['published_at'] = pd.to_datetime(df_channel['published_at']).dt.date

    # Drop unnecessary columns
    if 'thumbnail' in df_channel.columns:
        df_channel = df_channel.drop(columns=['thumbnail'])

    return df_channel


def video_transform(videos: list, channel: dict) -> pd.DataFrame:
    df=pd.DataFrame(videos)
    df2=df.copy()
    df2['video_id']=df2['video_id'].astype('string')
    df2['video_id']='https://youtube.com/watch?v='+df2['video_id']
    df2['title']=df2['title'].astype('string')
    df2['published_at']=df2['published_at'].astype('string')
    df2['published_at']=df2['published_at'].str[0:10]
    df3=pd.DataFrame(df2['video_id'].copy())
    df3['video_id']=df3['video_id'].str[28:]
    df2=df2.rename(columns={'video_id':'url'})
    df_final=pd.concat([df2,df3],axis=1)
    df_final['channel_id']=channel['channel_id']
    df_final['channel_name']=channel['title']
    df_final['published_at'] = pd.to_datetime(df_final['published_at'])
    df_final['title'] = df_final['title'].astype(str)
    df_final['url'] = df_final['url'].astype(str)
    df_final['video_id'] = df_final['video_id'].astype(str)
    df_final['channel_id'] = df_final['channel_id'].astype(str)
    df_final['channel_name'] = df_final['channel_name'].astype(str)
    df_final=df_final.rename(columns={'title':'video_title'})

    return df_final