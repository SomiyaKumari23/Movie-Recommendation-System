import numpy as np
import pandas as pd
import ast
from flask import Flask, request, render_template
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.stem.porter import PorterStemmer
app = Flask(__name__)
credits=pd.read_csv("credits.csv")
movies=pd.read_csv('movies.csv')
movies=movies.merge(credits,on="title")
movies=movies[['movie_id','title','overview','genres','keywords','cast','crew']]
movies.dropna(inplace=True)
# genres of movies is now in list
def convert(obj):
    L=[]
    for i in ast.literal_eval(obj):
        L.append(i['name'])
    return L
movies['genres']=movies['genres'].apply(convert)

#for having top three cast list
def convert3(obj):
    L=[]
    c=0
    for i in ast.literal_eval(obj):
        if c!=3:
            L.append(i['name'])
            c+=1
        else:
            break
    return L
movies['cast']=movies['cast'].apply(convert3)

def fetch_director(obj):
    L=[]
    c=0
    for i in ast.literal_eval(obj):
        if i['job']=='Director':
            L.append(i['name'])
            break
    return L

movies['crew']=movies['crew'].apply(fetch_director)

#converting string into list  "hi i am good" => [hi ,i ,am ,good]
movies['overview']=movies['overview'].apply(lambda x:x.split())
movies['genres']=movies['genres'].apply(lambda x:[i.replace(" ","") for i in x])
movies['keywords']=movies['keywords'].apply(lambda x:[i.replace(" ","") for i in x])
movies['cast']=movies['cast'].apply(lambda x:[i.replace(" ","") for i in x])
movies['crew']=movies['crew'].apply(lambda x:[i.replace(" ","") for i in x])
movies['tags']=movies['overview']+movies['genres']+movies['keywords']+movies['cast']+movies['crew']
new_df=movies[['movie_id','title','tags']]
#["hi","hello"]=hi hello
new_df['tags']=new_df['tags'].apply(lambda x:" ".join(x))
new_df['tags']=new_df['tags'].apply(lambda x:x.lower())

#5000 most common words will be choosen
cv=CountVectorizer(max_features=5000,stop_words='english')
vectors=cv.fit_transform(new_df['tags']).toarray()
ps=PorterStemmer() #nltk class used for loved,loves,loving=> love
def stem(text):
    y=[]
    for i in text.split():
        y.append(ps.stem(i))
    return " ".join(y)

new_df['tags']=new_df['tags'].apply(stem)
#calculating the distances of each movie from every movies
similarity=cosine_similarity(vectors)

def recommend(movie):
    movie_index=new_df[new_df['title']==movie].index[0]
    distances=similarity[movie_index]
    movies_list=sorted(list(enumerate(distances)),reverse=True,key=lambda x:x[1])[1:6]
    recommended_movies = [new_df.iloc[i[0]].title for i in movies_list]
    return recommended_movies
    # for i in movies_list:
    #     print(new_df.iloc[i[0]].title)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend_movies():
    movie = request.form['movie']
    recommendations = recommend(movie)
    return render_template('index.html', recommendations=recommendations, movie=movie)

if __name__ == '__main__':
    app.run(debug=True)