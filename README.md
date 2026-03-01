# Movie Recommender System

Streamlit app that recommends similar movies from `movies.pkl` and fetches posters from TMDB.

## Local Run

1. Install dependencies:

```powershell
.\.venv\Scripts\pip install -r requirements.txt
```

2. Configure TMDB API key in `.streamlit/secrets.toml`:

```toml
TMDB_API_KEY="your_tmdb_api_key_here"
```

3. Start app:

```powershell
.\.venv\Scripts\streamlit run app.py
```

## Deploy To Streamlit Community Cloud

1. Push this project to a GitHub repository.
2. Open `https://share.streamlit.io` and create a new app.
3. Select your repo/branch and set main file path to `app.py`.
4. In Streamlit app settings, add secret:

```toml
TMDB_API_KEY="your_tmdb_api_key_here"
```

5. Save and redeploy.
