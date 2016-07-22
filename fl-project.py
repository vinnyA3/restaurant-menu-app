from flask import Flask, render_template, url_for, request, redirect, flash, jsonify
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItems, User

# new imports
from flask import session as login_session
import random, string

# imports for OAuth
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

# declare client id by referenceing client secrets file
CLIENT_ID = json.loads(
	open('client_secret.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind = engine)
session = DBSession()

# create state token to prevent request forgery
# Store it in the session for later validation
@app.route('/login')
def showLogin():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) \
					for x in range(32))
	login_session['state'] = state
	return render_template("login.html", STATE = state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameters'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	code = request.data

	try:
		# upgrade the authorization code into a credentials object
		oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(code)
	except FlowExchangeError:
		response = make_response(json.dumps('Failed to upgrade the authorization code'),
							401)
		response.headers['Content-Type'] = 'application/json'
		return response
	# check that the access token is valid
	# debug
	print credentials.access_token
	access_token = credentials.access_token
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
	h = httplib2.Http()
	result = json.loads(h.request(url, 'GET')[1])
	# if there was an error in the access token info, abort mission!
	if result.get('error') is not None:
		response = make_response(json.dumps(result.get('error')), 500)
		reponse.headers['Content-Type'] = 'application/json'

	# verify that the access token is used for intended use
	gplus_id = credentials.id_token['sub']
	if result['user_id'] != gplus_id:
		response = make_response(
			json.dumps("Token's user ID does not match given user ID.", 401))
		response.headers['Content-Type'] = 'application/json'
		return response
	# Verify that the access token is valid for this application
	if result['issued_to'] != CLIENT_ID:
		response = make_response(
			json.dumps("Token's client id does not match the application"))
		response.headers['Content-Type'] = 'application/json'
		return response
	# check to see if the user is already logged in
	stored_credentials = login_session.get('credentials')
	stored_gplus_id = login_session.get('gplus_id')
	if stored_credentials is not None and gplus_id == stored_gplus_id:
		response = make_response(json.dumps('Current user is logged in'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Store the access token in the session for later use
	login_session['credentials'] = credentials.access_token
	login_session['gplus_id'] = gplus_id

	# get the user info
	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {'access_token': credentials.access_token, 'alt': 'json'}
	answer = requests.get(userinfo_url, params=params)

	data = answer.json()

	login_session['username'] = data['name']
	login_session['picture'] = data['picture']
	login_session['email'] = data['email']
	output = ''
	output += '<h1>Welcome, '
	output += login_session['username']
	output += '!</h1>'
	output += '<img src="'
	output += login_session['picture']
	output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
	flash("you are now logged in as %s" % login_session['username'])
	print "done!"
	return output

# DISCONNECT - revoke current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
	# only disconnect a connected user
	access_token = login_session['credentials']
	print 'access token: %s' % access_token
	print 'username is: %s' % login_session['username']
	if access_token is None:
		response = make_response(json.dumps('Current user not connected', 401))
		response.headers['Content-Type'] = 'application/json'
		return response
	# Execute HTTP GET request to revoke the current token
	url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
	h = httplib2.Http()
	print h.request(url, 'GET')
	result = h.request(url, 'GET')[0]

	if result['status'] == '200':
		# reset the user's session
		del login_session['credentials']
		del login_session['gplus_id']
		del login_session['username']
		del login_session['email']
		del login_session['picture']

		response = make_response(json.dumps('Successfully disconnected.'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response
	else:
		response = make_response(json.dumps('Failed to revoke user token.'), 400)
		response.headers['Content-Type'] = 'application/json'
		return response


#API Endpoint
@app.route('/restaurants/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	items = session.query(MenuItems).filter_by(restaurant_id = restaurant.id).all()
	return jsonify(MenuItems = [i.serialize for i in items])


@app.route('/')
@app.route('/restaurants')
def allRestaurants():
	# get the restaurants from the database
	restaurants = session.query(Restaurant).all()
	# render the template
	return render_template('allrestaurants.html', restaurants = restaurants)

@app.route('/restaurants/new', methods=['GET','POST'])
def newRestaurant():
	# check if the user is not logged in
	if 'username' not in login_session:
		return redirect('/login')

	if request.method == 'POST':
		if request.form['name'] != '':
			newRestaurant = Restaurant(name = request.form['name'])
			session.add(newRestaurant)
			session.commit()
			flash('Restaurant added!')
			return redirect(url_for('allRestaurants'))
		else:
			flash('Restaurant not added. Did you type in a name?')
			return redirect(url_for('allRestaurants'))
	else:
		return render_template('newrestaurant.html')

@app.route('/restaurants/<int:restaurant_id>/')
def restaurantMenu(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	items = session.query(MenuItems).filter_by(restaurant_id = restaurant.id)
	return render_template('menu.html', restaurant = restaurant, items = items)


@app.route('/restaurant/<int:restaurant_id>/new/', methods=['GET','POST'])
def newMenuItem(restaurant_id):
	# check if the user is logged in
	if 'username' not in login_session:
		return redirect('/login')

	if request.method == 'POST':
		itemName = request.form['name']
		itemCourse = request.form['course']
		itemPrice = request.form['price']
		itemDescription = request.form['description']
		newItem = MenuItems(name = itemName, course = itemCourse, price = itemPrice,
						restaurant_id = restaurant_id, description = itemDescription)

		session.add(newItem)
		session.commit()
		flash('New menu item created!')
		return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
	else:
		return render_template('newmenuitem.html', restaurant_id = restaurant_id)


@app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/edit/', methods=['GET','POST'])
def editMenuItems(restaurant_id, menu_id):
	# check if the user is logged in
	if 'username' not in login_session:
		return redirect('/login')

	edited_item = session.query(MenuItems).filter_by(id = menu_id).one()
	if request.method == 'POST':

		editName = request.form['name'] if request.form['name'] != '' else edited_item.name
		editCourse = request.form['course'] if request.form['course'] != '' else edited_item.course
		editPrice = request.form['price'] if request.form['price'] != '' else edited_item.price
		editDescription = request.form['description'] if request.form['description'] != '' else edited_item.description

		edited_item.name = editName
		edited_item.course = editCourse
		edited_item.price = editPrice
		edited_item.description = editDescription
		session.add(edited_item)
		session.commit()
		flash('Item edit successful!')
		return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))

	else:
		# get the restaurantmenu
		return render_template('editmenuitem.html', restaurant_id = restaurant_id, menu_id = menu_id, item = edited_item)


@app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/delete/', methods=['GET','POST'])
def deleteMenuItems(restaurant_id, menu_id):
	# check if the user is logged in
	if 'username' not in login_session:
		return redirect('/login')

	item_to_delete = session.query(MenuItems).filter_by(id = menu_id).one()
	if request.method == 'POST':
		session.delete(item_to_delete)
		session.commit()
		flash('Item deleted!')
		return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))

	else:
		return render_template('deleteitem.html', restaurant_id = restaurant_id, menu_id = menu_id, item = item_to_delete)


if __name__ == "__main__":
	app.secret_key = 'supersecrethere'
	app.debug = True
	app.run(host = '127.0.0.1', port = 8080)
