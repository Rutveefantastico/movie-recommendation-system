import streamlit as st
import pickle
import requests
import json
import os

API_KEY = "c3a0b6d49eda84036a35651edf5b5e84"

# ================= UI STYLE ================= #

st.markdown("""
<style>

/* PAGE BACKGROUND */

body {
    background: linear-gradient(to bottom,#0f0f0f,#141414);
    color: white;
}

/* NAVBAR */

.navbar {
    position: sticky;
    top: 0;
    display: flex;
    gap: 15px;
    background: #111;
    padding: 12px 20px;
    border-radius: 12px;
    margin-bottom: 20px;
}

.nav-item {
    color: white;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 500;
    background: #1f1f1f;
    transition: 0.3s;
}

.nav-item:hover {
    background: blue;
    transform: scale(1.05);
}

/* SEARCH BOX */

input {
    background-color:#1e1e1e !important;
    color:white !important;
    border-radius:10px !important;
}

/* MOVIE CARD */

.movie-card {
    background:#1a1a1a;
    border-radius:15px;
    padding:10px;
    text-align:center;
    transition:0.3s;
}

.movie-card:hover {
    transform:scale(1.05);
    box-shadow:0px 0px 15px rgba(229,9,20,0.6);
}

/* POSTER IMAGE */

.movie-poster {
    border-radius:12px;
}

/* BUTTON STYLE */

.stButton>button {
    background-color:black;
    color:lightyellow;
    border:none;
    border-radius:8px;
    padding:8px 16px;
    font-weight:bold;
}

.stButton>button:hover {
    background-color:#ff2a2a;
}

/* WATCHLIST BOX */

.watchlist-box{
    background:#1b1b1b;
    padding:15px;
    border-radius:10px;
    margin-top:10px;
}

</style>



""", unsafe_allow_html=True)

st.markdown(
"""
<h1 style='text-align:center;color:lightgreen;font-size:45px'>
📽️ Movie Recommendation System
</h1>
""",
unsafe_allow_html=True
)

# ================= USER STORAGE ================= #

USER_FILE = "users.json"

if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        json.dump({}, f)

def load_users():
    with open(USER_FILE) as f:
        return json.load(f)

def save_users(data):
    with open(USER_FILE, "w") as f:
        json.dump(data, f)

users = load_users()

# ================= LOGIN SYSTEM ================= #

st.sidebar.title("👤 User Account")

menu = st.sidebar.selectbox("Menu", ["Login", "Signup"])

if menu == "Signup":

    new_user = st.sidebar.text_input("Username")
    new_pass = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Create Account"):

        if new_user not in users:
            users[new_user] = {"password": new_pass, "watchlist": []}
            save_users(users)
            st.sidebar.success("Account Created")
        else:
            st.sidebar.warning("User already exists")

if menu == "Login":

    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):

        if username in users and users[username]["password"] == password:

            st.session_state.user = username
            st.sidebar.success("Logged In")

        else:
            st.sidebar.error("Invalid credentials")

if "user" not in st.session_state:
    st.warning("Please login to use recommendations")
    st.stop()

current_user = st.session_state.user

# ================= FILTER BAR ================= #

st.markdown("### ⭐ Filters")

c1,c2,c3,c4,c5 = st.columns(5)

with c1:
    language = st.selectbox("Language",
    ["All","English","Hindi","Spanish","Korean","Japanese"])

with c2:
    genre = st.selectbox("Genre",
    ["All","Action","Comedy","Drama","Horror","Sci-Fi","Romance"])

with c3:
    year = st.selectbox("Year",
    ["All","2024","2023","2022","2021","2020"])

with c4:
    ott = st.selectbox("OTT",
    ["All","Netflix","Amazon Prime","Disney+","HBO"])

with c5:
    tv_series = st.selectbox("TV Series",
    ["All","Popular","Top Rated","Trending"])


# ================= LOAD MODEL ================= #

movies = pickle.load(open("movies.pkl","rb"))

import zipfile
import os

if not os.path.exists("similarity.pkl"):
    with zipfile.ZipFile("similarity.zip", "r") as zip_ref:
        zip_ref.extractall()

similarity = pickle.load(open("similarity.pkl","rb"))

# ================= TMDB DETAILS ================= #

def fetch_details(movie_id):

    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}"
    data = requests.get(url).json()

    poster = "https://image.tmdb.org/t/p/w500" + data["poster_path"]
    rating = data["vote_average"]

    return poster, rating

# ================= TRAILER ================= #

def get_trailer(movie_id):

    url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={API_KEY}"
    data = requests.get(url).json()["results"]

    for video in data:
        if video["type"] == "Trailer":
            return "https://www.youtube.com/watch?v=" + video["key"]

    return None

# ================= TRENDING ================= #

def get_trending():

    url = f"https://api.themoviedb.org/3/trending/movie/week?api_key={API_KEY}"
    data = requests.get(url).json()["results"]

    posters = []
    titles = []

    for movie in data[:10]:
        posters.append("https://image.tmdb.org/t/p/w500" + movie["poster_path"])
        titles.append(movie["title"])

    return posters, titles

# ================= SEARCH ================= #

st.subheader("🔍 Search Movie")

movie_name = st.selectbox(
    "Choose Movie",
    movies["title"].values
)

# ================= RECOMMEND ================= #

def recommend(movie):

    movie_index = movies[movies["title"] == movie].index[0]
    distances = similarity[movie_index]

    movies_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:11]

    names = []
    posters = []
    ratings = []
    trailers = []

    for i in movies_list:

        movie_id = movies.iloc[i[0]].movie_id

        poster, rating = fetch_details(movie_id)
        trailer = get_trailer(movie_id)

        names.append(movies.iloc[i[0]].title)
        posters.append(poster)
        ratings.append(rating)
        trailers.append(trailer)

    return names, posters, ratings, trailers

# ================= TRENDING SECTION ================= #

st.write("## 🔥 Trending Movies")

trend_posters, trend_titles = get_trending()

cols = st.columns(5)

for i in range(5):
    with cols[i]:
        st.image(trend_posters[i])
        st.caption(trend_titles[i])

cols = st.columns(5)

for i in range(5, 10):
    with cols[i-5]:
        st.image(trend_posters[i])
        st.caption(trend_titles[i])

# ================= RECOMMEND BUTTON ================= #

if st.button("🎞️ Recommend"):

    names, posters, ratings, trailers = recommend(movie_name)

    st.session_state.names = names
    st.session_state.posters = posters
    st.session_state.ratings = ratings
    st.session_state.trailers = trailers

# ================= SHOW RECOMMENDATIONS ================= #

if "names" in st.session_state:

    st.write("## 🍿Recommended Movies")

    names = st.session_state.names
    posters = st.session_state.posters
    ratings = st.session_state.ratings
    trailers = st.session_state.trailers

    cols = st.columns(5)

    for i in range(5):

        with cols[i]:

            st.markdown(f"""
            <div class="movie-card">
            <img class="movie-poster" src="{posters[i]}" width="180">
            <h4>{names[i]}</h4>
            <p>⭐ {ratings[i]}</p>
            </div>
            """, unsafe_allow_html=True)
            

            if trailers[i]:
                st.video(trailers[i])

            if st.button("🎟️ Add to Watchlist", key=f"watch{i}"):

                if names[i] not in users[current_user]["watchlist"]:

                    users[current_user]["watchlist"].append(names[i])
                    save_users(users)

                    st.success(f"{names[i]} added!")

                    st.rerun()

    cols = st.columns(5)

    for i in range(5, 10):

        with cols[i-5]:

            st.markdown(f"""
            <div class="movie-card">
            <img class="movie-poster" src="{posters[i]}" width="180">
            <h4>{names[i]}</h4>
            <p>⭐ {ratings[i]}</p>
            </div>
            """, unsafe_allow_html=True)

            if trailers[i]:
                st.video(trailers[i])

            if st.button("🎟️ Add to Watchlist", key=f"watch{i}"):

                if names[i] not in users[current_user]["watchlist"]:

                    users[current_user]["watchlist"].append(names[i])
                    save_users(users)

                    st.success(f"{names[i]} added!")

                    st.rerun()

# ================= WATCHLIST ================= #

st.subheader("📜 Your Watchlist")

watchlist = users[current_user]["watchlist"]

if len(watchlist) == 0:
    st.info("Your watchlist is empty")

else:

    for i, movie in enumerate(watchlist):

        col1, col2 = st.columns([4,1])

        with col1:
            st.write("🎬", movie)

        with col2:
            if st.button("❌ Remove", key=f"remove_{i}"):

                users[current_user]["watchlist"].remove(movie)
                save_users(users)

                st.success(f"{movie} removed from watchlist")

                st.rerun()