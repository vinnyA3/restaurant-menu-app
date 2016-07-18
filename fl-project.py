from flask import Flask, render_template, url_for, request, redirect, flash, jsonify
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItems

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind = engine)
session = DBSession()

#API Endpoint
@app.route('/restaurants/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	items = session.query(MenuItems).filter_by(restaurant_id = restaurant.id).all()
	return jsonify(MenuItems = [i.serialize for i in items])


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
		flash('New menu item created!')
		return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
	else:
		return render_template('newmenuitem.html', restaurant_id = restaurant_id)


@app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/edit/', methods=['GET','POST'])
def editMenuItems(restaurant_id, menu_id):
	edited_item = session.query(MenuItems).filter_by(id = menu_id).one()
	if request.method == 'POST':
		if request.form['name']:
			edited_name = request.form['name']
		edited_item.name = edited_name
		session.add(edited_item)
		session.commit()
		flash('Item edit successful!')
		return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))

	else:
		# get the restaurantmenu
		return render_template('editmenuitem.html', restaurant_id = restaurant_id, menu_id = menu_id, item = edited_item)


@app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/delete/', methods=['GET','POST'])
def deleteMenuItems(restaurant_id, menu_id):
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
