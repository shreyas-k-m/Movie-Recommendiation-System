import streamlit_authenticator as stauth
import streamlit as st
import pandas as pd
import requests
import pickle
import time 
from pathlib import Path
from streamlit_extras.badges import badge
from streamlit_option_menu import option_menu

from PIL import Image
im = Image.open('video.png')
st.set_page_config(page_title="Movie Recommender System App",page_icon = im)

import base64
def add_bg_from_local(image_file):
    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url(data:image/{"gif"};base64,{encoded_string.decode()});
        background-size: cover
    }}
    </style>
    """,
    unsafe_allow_html=True
    )
add_bg_from_local('wallpaper_login.gif')

# --- USER AUTHENTICATION ---
names = ["Admin_Login"]
usernames = ["admin"]

# load hashed passwords
file_path = Path(__file__).parent / "hashed_pw.pkl"
with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)

authenticator = stauth.Authenticate(names, usernames, hashed_passwords,
    "movies_dashboard", "abcdef", cookie_expiry_days=30)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status == False:
    st.error("Username/password is incorrect")

if authentication_status == None:
    st.warning("Please enter your username and password")

if authentication_status:
    
    selected = option_menu(None, ["Home", "Popularity", "Content", 'Collaborative'], 
        icons=['house', 'fire', "camera-reels", 'people-fill'], 
        menu_icon="cast", default_index=0, orientation="horizontal")

    if selected == "Home":
        st.title("Movie Recommendation System")
        st.write("Welcome to Movie Recommendation System! We help you discover movies you'll love.")

        st.header("Popularity-Based Recommendations")
        st.write("Looking for trending or popular movies? Our popularity-based recommendation system "
             "suggests movies that are currently trending or highly rated by a large number of users. "
             "These recommendations are great for finding crowd-pleasers.")
        
        st.header("Content-Based Recommendations")
        st.write("Prefer movies similar to your favorite ones? Our content-based recommendation system "
             "analyzes movie content (such as genre, director, actors) and suggests movies with similar "
             "attributes to those you've enjoyed. This method is perfect for personalized recommendations "
             "based on your unique taste.")
        
        st.header("Collaborative Filtering")
        st.write("Want recommendations based on user behavior? Our collaborative filtering recommendation "
             "system leverages the preferences and behaviors of users similar to you to suggest movies "
             "you might like. It's a powerful approach to discovering new favorites.")
        
        st.write("Get started by selecting one of the recommendation methods from the Menu bar. Happy movie watching!")

        authenticator.logout('Logout','main')
        
        badge(type="github", name="shreyas-k-m/Movie-Recommendiation-System")

    if selected == "Popularity":
        @st.cache_data
        def load_movie_data():
            return pd.read_pickle('popular.pkl')
        movies_df = load_movie_data()

        st.title('Top 50 Popular Movies')
        st.write("Explore the top 50 popular movies with details on the number of ratings and average ratings.")

        top_50_movies = movies_df[['title', 'num_ratings', 'avg_ratings']].head(50)

        column_names = {
            'title': 'Title',
            'num_ratings': 'No. Of Ratings',
            'avg_ratings': 'Average Ratings'
        }

        top_50_movies = top_50_movies.rename(columns=column_names)
        top_50_movies.index = range(1, 51)

        st.table(top_50_movies)
        st.line_chart(top_50_movies[['No. Of Ratings', 'Average Ratings']])

    if selected == "Content":
        st.title('Content Based Recommendations')
        st.write("Discover movies with similar attributes to those you like, such as genre actor and director.")

        @st.cache_data
        def fetch_poster(movie_id):
            url = "https://api.themoviedb.org/3/movie/{}?api_key=1aa68f108039b9d064664fb1e01c5e7a&language=en-US".format(movie_id)
            data = requests.get(url)
            data = data.json()
            poster_path = data['poster_path']
            full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
            return full_path
        
        def recommend(movie):
            movie_index = movies[movies['title'] == movie].index[0]
            distances = similarity[movie_index]
            movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

            recommended_movies = []
            recommended_movie_posters = []

            for i in movies_list:
                # fetch the movie poster
                movie_id = movies.iloc[i[0]].movie_id
                recommended_movies.append(movies.iloc[i[0]].title)
                recommended_movie_posters.append(fetch_poster(movie_id))

            return recommended_movies,recommended_movie_posters
        
        movies_dict = pickle.load(open('movies_content.pkl','rb'))
        movies = pd.DataFrame(movies_dict)
        similarity = pickle.load(open('similarity_content.pkl','rb'))

        selected_movie_name = st.selectbox(
            "Type or select a movie from the dropdown",
            movies['title'].values
        )
        if st.button('Show Recommendation'):
            with st.spinner('Wait for it...'):
                time.sleep(1.5)
            st.success('Done!', icon="✅")
            names,posters = recommend(selected_movie_name)

            #display with the columns
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.markdown(names[0],)
                st.divider()
                st.image(posters[0],use_column_width='auto')
            with col2:
                st.markdown(names[1],)
                st.divider()
                st.image(posters[1],use_column_width='auto')
            with col3:
                st.markdown(names[2],)
                st.divider()
                st.image(posters[2],use_column_width='auto')
            with col4:
                st.markdown(names[3],)
                st.divider()
                st.image(posters[3],use_column_width='auto')
            with col5:
                st.markdown(names[4],)
                st.divider()
                st.image(posters[4],use_column_width='auto')

    if selected == "Collaborative":
        st.title("Collaborative Filtering Recommendations")
        st.write("Find movies similar to your selected one in terms of user ratings and preferences.")
        
        pt = pickle.load(open('pt_collaborative.pkl', 'rb'))
        similarity_scores = pickle.load(open('similarity_collaborative.pkl', 'rb'))
        movies = pickle.load(open('movies_collaborative.pkl', 'rb'))

        available_movie_titles = pt.index.values
        selected_movie = st.selectbox("Type or select a movie from the dropdown", available_movie_titles)

        def recommend(movie_name):
            matching_indices = [i for i, name in enumerate(pt.index) if movie_name in name]

            if matching_indices:
                index = matching_indices[0]
                similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[1:6]
                recommended_movies = [pt.index[i[0]] for i in similar_items]
                return recommended_movies
            else:
                return []
            
        if st.button("Show Recommendation"):
            with st.spinner('Wait for it...'):
                time.sleep(1.5)
            st.success('Done!', icon="✅")
            recommended_movies = recommend(selected_movie)

            if recommended_movies:
                st.subheader("Recommended Movies:")
                for i, movie in enumerate(recommended_movies):
                    st.write(f"{i + 1}. {movie}")
            else:
                st.warning("Movie not found in the dataset.")

    def add_bg_from_local(image_file):
        with open(image_file, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
        st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url(data:image/{"jpg"};base64,{encoded_string.decode()});
            background-size: cover
        }}
        </style>
        """,
        unsafe_allow_html=True
        )
    add_bg_from_local('wallpaper_home.jpg')

hide_default_format = """
       <style>
       #MainMenu {visibility: hidden;}
       footer {visibility: hidden;}
       header {visibility: hidden;}
       </style>
       """
st.markdown(hide_default_format, unsafe_allow_html=True)
