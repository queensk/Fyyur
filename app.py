#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from distutils.log import error
from email.policy import default
import json
from os import abort
from sre_parse import State
from unicodedata import name
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, session, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import  Migrate
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:queens@localhost:5432/fyyurmusicalvenue'
migrations=Migrate(app, db)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__='Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    seeking_talent = db.Column(db.Boolean(), default=False)
    seeking_description = db.Column(db.String())
    website = db.Column(db.String(500))
    shows = db.relationship('Show', backref='Venue', lazy=True)
    
    def __repr__(self):
      return f'<Venue {self.id} {self.name} {self.city} {self.state} {self.address} {self.phone} {self.image_link} {self.facebook_link} {self.genres} {self.seeking_talent} {self.seeking_description} {self.website} {self.website}, {self.shows}>'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120), index=True)
    state = db.Column(db.String(120), index=True)
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean(), default=False)
    seeking_description = db.Column(db.String())
    website = db.Column(db.String(500))
    shows = db.relationship('Show', backref='Artist', lazy=True)
    
    def __repr__(self):
      return f'<Artist {self.id} {self.name}, {self.shows}>'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show (db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
    start_time = db.Column(db.DateTime, default=datetime.utcnow())
   
    def __repr__(self):
      return f'<Show {self.id} {self.artist_id} {self.venue_id} {self.start_time}>'
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  try:
    data = []
    places = Venue.query.distinct("city", "state")
    for place in places:
        # print(place.city, place.state)
        city = place.city
        state = place.state
        venues = []
        for venue in Venue.query.filter_by(city=city, state=state):
            upcoming_shows = db.session.query(
                Show).filter_by(venue_id=venue.id).count()
            # print(type(upcoming_shows), "good")
            venues.append({
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": upcoming_shows
            })
        data.append({
            "city": city,
            "state": state,
            "venues": venues
        })

    return render_template('pages/venues.html', areas=data)
  except:
    flash("error, no venues available")
    return redirect(url_for('index'))

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  try:
    search_term = request.form.get('search_term', '')
    search_result = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
    count = len(search_result)
    response={
      "count": count,
      "data": search_result
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))
  except:
    flash('There was an error in the search')
    return redirect(url_for('venues'))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  try:
    venue_data = Venue.query.get(venue_id)
    data = []
    past_shows_count = len(db.session.query(Show).join(Venue).filter(
        Show.artist_id == venue_data.id).filter(str(Show.start_time) < str(datetime.now())).all())
    upcoming_shows_count = len(db.session.query(Show).join(Venue).filter(
        Show.venue_id == venue_data.id).filter(str(Show.start_time) > str(datetime.now())).all())
    
    data.append({
        "id": venue_data.id,
        "name": venue_data.name,
        "genres": venue_data.genres,
        "city": venue_data.city,
        "state": venue_data.state,
        "phone": venue_data.phone,
        "website": venue_data.website,
        "facebook_link": venue_data.facebook_link,
        "seeking_talent": venue_data.seeking_talent,
        "image_link": venue_data.image_link,
        "address": venue_data.address,
        "past_shows_count": past_shows_count,
        "upcoming_shows_count": upcoming_shows_count

    })

    data = list(filter(lambda d: d['id'] ==venue_id, data))[0]
    return render_template('pages/show_venue.html', venue=data)
  except:
    flash('There was an error in showing the venue')
    return redirect(url_for('venues'))

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  try:
    new_venue = Venue(
      name = request.form.get('name'),
      city = request.form.get('city'),
      state = request.form.get('state'),
      address = request.form.get('address'),
      phone = request.form.get('phone'),
      facebook_link = request.form.get('facebook_link'),
      image_link = request.form.get('image_link'),
      website = request.form .get('wesite'),
      seeking_talent = request.form.get('seeking_talent'=='True'),
      seeking_description = request.form.get('seeking_description')
    )
    db.session.add(new_venue)
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  # on successful db insert, flash success
  if not error:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  else:
    flash('An error occurred. Venue ' + new_venue.name + ' could not be added')
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  try:
    Venue.query.filter_by(id=venue_id).delete()
    Show.query.filter_by(venue_id=venue_id).delete()
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
    if error:
      flash('When delete, an error occurred')
      return redirect(url_for('index'))
    else:
      flash('Venue deleted successfully')
    return redirect(url_for('index'))

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  try:
    data= Artist.query.all()
    return render_template('pages/artists.html', artists=data)
  except:
    flash('An error occurred when displaying artists')
    return redirect(url_for('index'))

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  try:
    search_term = request.form.get('search_term', '')

    artist_data = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()

    response = {
      "count": len(artist_data),
      "data": artist_data
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))
  except:
    flash('An error occurred in the Artist search')
    return redirect(url_for('artists'))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id

    data =[]
    artist_data=Artist.query.get(artist_id)
    print(artist_data)
    past_shows_dict = db.session.query(Show).join(Artist).filter(
        Show.artist_id == artist_id).filter(
            str(Show.start_time) < str(datetime.now())
    ).all()

    upcomming_shows_dict = db.session.query(Show).join(Artist).filter(
        Show.artist_id == artist_id).filter(
            str(Show.start_time) > str(datetime.now())
    ).all()
    upcoming_shows = []
    past_shows = []
    for index in range(0, len(upcomming_shows_dict)):

      venue_id = upcomming_shows_dict[index].venue_id
      start_time = upcomming_shows_dict[index].start_time

      venues = db.session.query(Venue).get(venue_id)

      venue_name = venues.name
      venue_image_link = venues.image_link

      upcoming_shows.append(
        {
          "venue_id": venue_id,
          "venue_name": venue_name,
          "venue_image_link": venue_image_link,
          "start_time": str(start_time)
        })
    for i in range(0, len(past_shows_dict)):

        venue_id = past_shows_dict[i].venue_id
        start_time = past_shows_dict[i].start_time
        venues = session.query(Venue).get(venue_id)

        venue_name = venues.name
        venue_image_link = venues.image_link

        past_shows.append(
          {
            "venue_id": venue_id,
            "venue_name": venue_name,
            "venue_image_link": venue_image_link,
            "start_time": str(start_time)
          })

    data = {
        "id": artist_id,
        "name": artist_data.name,
        "genres": artist_data.genres,
        "city": artist_data.city,
        "state": artist_data.state,
        "phone": (artist_data.phone[:3]+'-'+artist_data.phone[3:6]+'-'+artist_data.phone[6:]),
        "website": artist_data.website,
        "facebook_link": artist_data.facebook_link,
        "seeking_venue": artist_data.seeking_venue,
        "seeking_description": artist_data.seeking_description,
        "image_link": artist_data.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows)
    }

    return render_template('pages/show_artist.html', artist=data)
  
    flash('an error occurred in showing artist')
    return redirect(url_for('index'))
#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist_data = Artist.query.filter_by(id=artist_id).first()

  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist_data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    artist_data = Artist.query.filter_by(id==artist_id).first()

    artist_data.name = request.form.get('name')
    artist_data.city = request.form.get('city')
    artist_data.state = request.form.get('state')
    artist_data.phone = request.form.get('phone')
    artist_data.gernes = request.form.get('gernes')
    artist_data.facebook_link = request.form.get('facebook_link')
    artist_data.website = request.form.get('website')
    artist_data.image_link = request.form.get('image_link')
    artist_data.seeking_venue = request.form.get('seeking_venue')== True
    artist_data.seeking_description = request.form.get('seeking_description')
    db.session.commit()
  except:
    db.session.rollback()
    flash('An error occurred when submiting edits')
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue_data = Venue.query.filter_by(id=venue_id).first()   
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue_data)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  try:
    venue_data=Venue.query.filter_by(venue_id)

    venue_data.name=request.form.get('name'),
    venue_data.genres=request.form.get('genres'),
    venue_data.address=request.form.get('address'),
    venue_data.city=request.form.get('city'),
    venue_data.state=request.form.get('state'),
    venue_data.phone=request.form.get('phone'),
    venue_data.website=request.form.get('website'),
    venue_data.facebook_link=request.form.get('facebook_link'),
    venue_data.seeking_talent=request.form.get('seeking_talent'),
    venue_data.seeking_description=request.form.get('seeking_description'),
    venue_data.image_link=request.form.ger('image_link')

    db.session.commit()
  except:
    db.session.rollback()
    flash('An error occurred when editting venues')
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  try:
    new_artist=Artist(
      name=request.form.get('name'),
      city=request.form.get('city'),
      state=request.form.get('state'),
      phone=request.form.get('phone'),
      gender=request.form.get('gender'),
      facebook_link=request.form.get('facebook_link'),
      image_link=request.form.get('image_link'),
      website=request.form.get('website'),
      seeking_venue=request.form.get('seeking_venue'),
      seeking_description=request.form.get('seeking_description')
    )
    db.session.add(new_artist)
    db.seddion.commit()
  except:
    error=True
    db.session.rollback()
  finally:
    db.session.close()
  # on successful db insert, flash success
  if not error:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  else:
    flash('There was an error when crating ' + new_artist.name)
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  try:
    data = []
    shows = Show.query.join(Artist, Artist.id == Show.artist_id).join(Venue, Venue.id == Show.venue_id).all()
    print(shows)
    for show in shows:
      venue_id = show.venue_id
      artist_id = show.artist_id
      obj_venue = db.session.query(Venue).get(venue_id)
      obj_artist = db.session.query(Artist).get(artist_id)

      data.append({
          "venue_id": show.venue_id,
          "venue_name": obj_venue.name,
          "artist_id": show.artist_id,
          "artist_name": obj_artist.name,
          "artist_image_link": obj_artist.image_link,
          "start_time": str(show.start_time)
      })

    return render_template('pages/shows.html', shows=data)
  except:
    flash('an erroe occurred, when desplaing list of shows')
    return redirect(url_for('index'))

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  error=False
  try:
    show = Show(
      artist_id=request.form.get('artist_id'),
      venue_id=request.form.get('venue_id'),
      start_time=request.form.get('start_time')
    )
    db.session.add(show)
    db.session.commit()
  # on successful db insert, flash success
    flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  except:
    error=True
    db.session.rollback()
    flash('An error occurred while adding show')
  finally:
    db.session.close()
    return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=3000)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
