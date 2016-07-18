from flask import Flask, render_template, url_for, request, redirect
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItems

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind = engine)
session = DBSession()

@app.route('/')
@app.route('/restaurants/<int:restaurant_id>/')
def restaurantMenu(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	items = session.query(MenuItems).filter_by(restaurant_id = restaurant.id)
	return render_template('menu.html', restaurant = restaurant, items = items)


@app.route('/restaurant/<int:restaurant_id>/new/', methods=['GET','POST'])
def newMenuItem(restaurant_id):
	if request.method == 'POST':
		newItem = MenuItems(name = request.form['name'], restaurant_id = restaurant_id)
		session.add(newItem)
		session.commit()
		return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
	else:
		return render_template('newmenuitem.html', restaurant_id = restaurant_id)


@app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/edit/', methods=['GET','POST'])
def editMenuItems(restaurant_id, menu_id):
	edited_item = session.query(MenuItems).filter_by(id = menu_id).one()
	# get the restaurantmenu
	return render_template('editmenuitem.html', restaurant_id = restaurant_id, menu_id = menu_id, item = edited_item)

@app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/delete/')
def deleteMenuItems(restaurant_id, menu_id):
	return "page to delete a menu item!"


if __name__ == "__main__":
	app.debug = True
	app.run(host = '127.0.0.1', port = 8080)
