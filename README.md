# Movie Recommender System

Streamlit app that recommends similar movies from `movies.pkl` and fetches posters from TMDB.

## Local Run

1. Install dependencies:

```powershell
.\.venv\Scripts\pip install -r requirements.txt
```

2. Configure TMDB API key in `.streamlit/secrets.toml`:

```toml
TMDB_API_KEY="7775650bb3bdc769d21b089ee2a33d90"
```

> **Note:** the deployed app will not show any posters unless the key is
> correctly provided.  If you see the same image repeated for multiple
> recommendations it's usually due to duplicate TMDB IDs in the dataset –
> we now drop duplicates automatically, but make sure you regenerate your
> pickle if you update the data.

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
TMDB_API_KEY="7775650bb3bdc769d21b089ee2a33d90"
```

5. Save and redeploy.
