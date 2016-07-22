import sys

from sqlalchemy import Column, ForeignKey, Integer, String

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship

from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
	__tablename__ = 'users'
	name = Column(String(80), nullable=False)
	email = Column(String, nullable=False)
	picture = Column(String)
	id = Column(Integer, primary_key=True)

class Restaurant(Base):
	__tablename__ = "restaurant"
	name = Column(String(80), nullable = False)
	id = Column(Integer, primary_key = True)
	user_id = Column(Integer, ForeignKey('users.id'))
	user = relationship(User)


class MenuItems(Base):
	__tablename__ = "menu_item"
	name = Column(String(80), nullable = False)
	id = Column(Integer, primary_key = True)
	course = Column(String(250))
	description = Column(String(250))
	price = Column(String(8))
	restaurant_id = Column(Integer, ForeignKey('restaurant.id'))
	restaurant = relationship(Restaurant)
	user_id = Column(Integer, ForeignKey('users.id'))
	user = relationship(User)

	@property
	def serialize(self):
		# return object data in serializeable format
		return {
			'name' : self.name,
			'description' : self.description,
			'id' : self.id,
			'price' : self.price,
			'course' : self.course
		}



####### EOF #######
engine = create_engine(
	'sqlite:///restaurantmenuwithusers.db'
)

Base.metadata.create_all(engine)
