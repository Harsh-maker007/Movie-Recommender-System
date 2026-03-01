import math
import os
import pickle

import requests
import streamlit as st


@st.cache_data
def load_movies():
    with open("movies.pkl", "rb") as file:
        movies_df = pickle.load(file)
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
        key = st.secrets.get("TMDB_API_KEY", "")
    except Exception:
        key = ""
    if not key:
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
            for i, movie in enumerate(recommendations):
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
