from sqlalchemy import create_engine, text
import sqlalchemy.types
import pandas as pd
import urllib.parse
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from urllib.parse import quote_plus

load_dotenv()

user = os.getenv("POSTGRES_USER")
password = quote_plus(os.getenv("POSTGRES_PASSWORD"))  # URL-encode special chars
host = os.getenv("POSTGRES_HOST")
port = os.getenv("POSTGRES_PORT", 5432)
db = os.getenv("POSTGRES_DB")

engine = create_engine(
    f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}'
)

def upload_channel(df_channel):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM channels"))

    df_channel.to_sql(
    'channels',
    engine,
    if_exists='append',   # append to the now-empty table
    index=False,
    dtype={
        'channel_id': sqlalchemy.types.String,
        'title': sqlalchemy.types.String,
        'description': sqlalchemy.types.String,
        'published_at': sqlalchemy.types.Date,
        'country': sqlalchemy.types.String,
        'subscriber_count': sqlalchemy.types.BigInteger,
        'video_count': sqlalchemy.types.BigInteger,
        'view_count': sqlalchemy.types.BigInteger,
        'channel_url': sqlalchemy.types.String,
        'avg_views': sqlalchemy.types.BigInteger
    }
)   
def upload_videos(df_final):
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE videos"))
        conn.commit()

# Then insert new data
    df_final.to_sql('videos', con=engine, if_exists='append', index=False)
