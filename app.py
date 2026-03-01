import math
import os
import pickle

import requests
import streamlit as st


@st.cache_data
def load_movies():
    """Load movie data and remove any duplicate TMDB IDs.

    The dataset coming from `movies.pkl` contains a handful of rows
    with the same ``id`` value.  When the recommender returns movies
    that share the same TMDB identifier the poster lookup will always
    return the same image which makes the Streamlit app look broken
    (all of the posters are identical).  To avoid that issue we drop
    duplicate ``id`` values right after loading.  This keeps the first
    occurrence of each movie and preserves the existing index which
    the recommendation logic relies on.
    """

    with open("movies.pkl", "rb") as file:
        movies_df = pickle.load(file)

    # there are a few duplicates in the pickle (same TMDB id used more than once)
    # dropping them prevents repeated posters on the UI
    movies_df = movies_df.drop_duplicates(subset="id")

    return movies_df


def build_tag_sets(tags_series):
    return [set(str(tags).split()) for tags in tags_series]


def recommend(movie_title, movies_df, tag_sets, top_n=5):
    matches = movies_df.index[movies_df["title"] == movie_title].tolist()
    if not matches:
        return []

    selected_idx = matches[0]
    selected_tags = tag_sets[selected_idx]

    scores = []
    for idx, tags in enumerate(tag_sets):
        if idx == selected_idx:
            continue
        if not selected_tags or not tags:
            score = 0.0
        else:
            overlap = len(selected_tags.intersection(tags))
            score = overlap / math.sqrt(len(selected_tags) * len(tags))
        scores.append((score, idx))

    scores.sort(reverse=True, key=lambda item: item[0])
    top_indexes = [idx for score, idx in scores[:top_n] if score > 0]
    recommended = movies_df.iloc[top_indexes][["id", "title"]]
    return recommended.to_dict("records")


def get_tmdb_api_key():
    try:
        key = st.secrets["TMDB_API_KEY"]
    except (KeyError, FileNotFoundError):
        key = os.getenv("TMDB_API_KEY", "")
    return key


@st.cache_data
def fetch_poster(movie_id, api_key):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {"api_key": api_key, "language": "en-US"}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get("poster_path")
        if poster_path:
            return f"https://image.tmdb.org/t/p/w500{poster_path}"
    except requests.RequestException:
        return None
    return None


def main():
    st.title("Movie Recommender System")

    movies = load_movies()
    titles = movies["title"].values
    tag_sets = build_tag_sets(movies["tags"])
    selected_movie = st.selectbox("Select a movie", titles)

    if st.button("Recommend"):
        recommendations = recommend(selected_movie, movies, tag_sets)
        if recommendations:
            st.subheader("Top Recommendations")
            tmdb_api_key = get_tmdb_api_key()

            if not tmdb_api_key:
                st.info("Set `TMDB_API_KEY` in Streamlit secrets or environment to show posters.")

            cols = st.columns(5)
            # even though we dropped duplicates when loading, make sure we
            # never display the same TMDB id twice in the UI; otherwise the
            # user will see identical posters for different titles.
            seen_ids = set()
            filtered = []
            for movie in recommendations:
                if movie["id"] in seen_ids:
                    continue
                seen_ids.add(movie["id"])
                filtered.append(movie)

            for i, movie in enumerate(filtered):
                title = movie["title"]
                movie_id = movie["id"]
                poster_url = fetch_poster(movie_id, tmdb_api_key) if tmdb_api_key else None
                with cols[i % 5]:
                    if poster_url:
                        st.image(poster_url, use_container_width=True)
                    st.caption(title)
        else:
            st.warning("No recommendations found for this title.")


if __name__ == "__main__":
    main()
