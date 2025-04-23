import json

from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, TextAreaField
from wtforms.validators import DataRequired, NumberRange
import requests
import os
from dotenv import load_dotenv

'''
Red underlines? Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from requirements.txt for this project.
'''
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

# CREATE DB
class Base(DeclarativeBase):
    pass

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies-collection.db"
db = SQLAlchemy(model_class=Base)
db.init_app(app)

tmdb_search_endpoint = "https://api.themoviedb.org/3/search/movie"
tmdb_get_endpoint =  "https://api.themoviedb.org/3/movie/"
tmdb_image_endpoint = "https://image.tmdb.org/t/p/original/"
tmdb_key = os.getenv("TMDB_API_KEY")

# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

with app.app_context():
    db.create_all()

# with app.app_context():
#     new_movie = Movie(
#         title="Phone Booth",
#         year=2002,
#         description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#         rating=7.3,
#         ranking=10,
#         review="My favourite character was the caller.",
#         img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
#     )
#     db.session.add(new_movie)
#     db.session.commit()


# FORM
class AddForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")

class EditForm(FlaskForm):
    rating = FloatField("Your Rating Out of of 10 e.g. 7.5",
                        validators=[ DataRequired(),
                                    NumberRange(min=0, max=10)
                                    ]
                        )
    review = TextAreaField("Your Review", validators=[ DataRequired()], render_kw={'style': 'width: 300px'} )
    submit = SubmitField('Done')

@app.route("/")
def home():
    movies = db.session.execute(db.select(Movie).order_by(Movie.rating)).scalars().all()
    for i in range(len(movies)):
        movies[i].ranking = len(movies) - i

    db.session.commit()
    return render_template("index.html", movies=movies)

@app.route("/edit/movie/<int:id>", methods=["GET", "POST"])
def edit_rating(id):
    movie = db.session.execute(db.select(Movie).where(Movie.id == id)).scalar()
    rating_form = EditForm(obj=movie)

    if rating_form.validate_on_submit():
        print(request.form["review"])
        movie.rating = rating_form.rating.data
        movie.review = rating_form.review.data
        db.session.commit()
        return redirect(url_for("home"))

    return render_template("edit.html", form=rating_form )

@app.route("/delete/movie/<int:id>")
def delete_movie(id):
    movie = db.one_or_404(db.select(Movie).filter_by(id=id))
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/add/movie", methods=["GET", "POST"])
def add_movie():
    add_form = AddForm()

    if add_form.validate_on_submit():
        movie_title = add_form.title.data
        response = requests.get(tmdb_search_endpoint, params={
            "api_key": tmdb_key,
            "query": movie_title
        })
        data = response.json()["results"]
        return render_template("select.html", search=data)

    return render_template("add.html", form=add_form)

@app.route("/find/movie")
def find_movie():
    movie_api_id = request.args.get("id")

    if movie_api_id:
        response = requests.get(f"{tmdb_get_endpoint}{movie_api_id}", params={
                "api_key": tmdb_key,
            })
        data = response.json()
        new_movie = Movie(
            title = data["title"],
            year = data["release_date"].split("-")[0],
            img_url = f"{tmdb_image_endpoint}{data['poster_path']}",
            description = data["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()

        return redirect(url_for("edit_rating", id=new_movie.id))

if __name__ == '__main__':
    app.run(debug=True)
