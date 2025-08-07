# 📺 YT-Analytics-Dashboard


A Streamlit-based web app to analyze YouTube videos and channels using the YouTube Data API, sentiment analysis, and more. Gain insights into content performance, audience reactions, and engagement trends.

---

## ✨ Features

### 🎬 Video Analysis
- 🔍 Search by keyword or video ID
- 📊 View video stats: views, likes, comments, etc.
- 💬 Sentiment analysis of top comments
- 📈 Comment trends over time

### 📺 Channel Analysis
- 🔍 Search by channel name or ID
- 👥 Get channel stats: subscribers, total views, video count
- 📅 Analyze publishing frequency and video performance
- 🧠 Discover top content themes and strategies

---

## 🧠 Tech Stack

| Layer         | Tools/Tech Used                             |
|---------------|---------------------------------------------|
| **Frontend**  | Streamlit                                   |
| **Backend**   | Python, YouTube Data API                    |
| **NLP**       | HuggingFace Transformers, BERTopic          |
| **Database**  | Supabase (PostgreSQL + RESTful API)         |
| **Visualization** | Streamlit charts, Matplotlib          |
| **Data Handling** | Pandas                                |

---

## 🗃️ Data Flow Overview

1. **User Input:** Keyword or ID for videos/channels.
2. **YouTube API:** Fetches metadata and comments.
3. **Processing:** Clean text, analyze sentiment, extract topics.
4. **Supabase:** Stores fetched data and analysis results.
5. **UI:** Displays insights through interactive charts and metrics.

---



