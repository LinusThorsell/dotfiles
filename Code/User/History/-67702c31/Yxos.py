# -*- coding: utf-8 -*-

import db
from db import Base
import plug

from sqlalchemy import Table, Column, Integer, Unicode, Sequence, ForeignKey, UnicodeText, DateTime, Boolean, select, func, String, UniqueConstraint, join, and_
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property

# association table for CourseBooking <-> WorkoutBooking
coursebooking_workoutbooking = Table('coursebooking_workoutbooking', Base.metadata,
	Column('coursebooking_id', Integer, ForeignKey('coursebooking.id')),
	Column('workoutbooking_id', Integer, ForeignKey('workoutbooking.id'))
)

# association table for Course <-> Workout
course_workout = Table('course_workout', Base.metadata,
	Column('course_id', Integer, ForeignKey('course.id')),
	Column('workout_id', Integer, ForeignKey('workout.id'))
)

# association table for Staff <-> Course
staff_course = Table('staff_course', Base.metadata,
	Column('staff_id', Integer, ForeignKey('user.id')),
	Column('course_id', Integer, ForeignKey('course.id'))
)

# association table for Resource <-> Course
resource_course = Table('resource_course', Base.metadata,
	Column('staff_id', Integer, ForeignKey('user.id')),
	Column('course_id', Integer, ForeignKey('course.id'))
)

# association table for Course <-> SystemTag
course_systemtag = Table('course_systemtag', Base.metadata,
	Column('course_id', Integer, ForeignKey('course.id')),
	Column('systemtag_id', Integer, ForeignKey('systemtag.id'))
)

# association table for CourseBooking <-> Payment
coursebooking_payment = Table('coursebooking_payment', Base.metadata,
	Column('coursebooking_id', Integer, ForeignKey('coursebooking.id')),
	Column('payment_id', Integer, ForeignKey('payment.id'))
)

# association table for Site <-> CourseCategory
site_coursecategory = Table('site_coursecategory', Base.metadata,
	Column('site_id', Integer, ForeignKey('site.id')),
	Column('coursecategory_id', Integer, ForeignKey('coursecategory.id'))
)

# association table for Site <-> Course
site_course = Table('site_course', Base.metadata,
	Column('site_id', Integer, ForeignKey('site.id')),
	Column('course_id', Integer, ForeignKey('course.id'))
)

class CourseCategory(Base, plug.db.CRUDBase, plug.db.GetItem):
	name = Column(Unicode(60))
	order = Column(Integer)
	show = Column(Boolean)
	active = Column(Boolean, default=True)
	sites = relationship('Site', secondary=site_coursecategory)
	sort = Column(String(10), default='created')	 # created, name, startTime, endTime
	imagekey = Column(String(40))
	description = Column(UnicodeText)

	@classmethod
	def addInternal(cls, c, performer):
		if not c.get('sites'):
			c['sites'] = [db.Site.main().id]

		return super(CourseCategory, cls).addInternal(c, performer)

	@classmethod
	def getPermission(cls):
		return dict(add='Schedule handling', get='Show schedule', change='Schedule handling', remove='Schedule handling')

	@classmethod
	def getRequiredModules(cls):
		return 'Courses'

class Course(Base, plug.db.CRUDBase, plug.db.GetItem):
	category_id = Column(Integer, ForeignKey('coursecategory.id'))
	category = relationship('CourseCategory', uselist=False, foreign_keys=[category_id])

	product_id = Column(Integer, ForeignKey('trainingcardtype.id'))
	product = relationship('TrainingCardType', uselist=False, backref=backref('course', uselist=False), foreign_keys=[product_id])

	longdescription = Column(UnicodeText)
	firstBookingTime = Column(DateTime)
	lastBookingTime = Column(DateTime)
	canCancel = Column(Boolean)
	startTime = Column(DateTime)
	endTime = Column(DateTime)
	space = Column(Integer)
	sites = relationship('Site', secondary=site_course)
	canBookForOthers = Column(Boolean) # DEPRECATED
	canBookFor = Column(String(12), default="self") # self, others, self+others, others+self
	refundProducts = Column(Boolean)
	url = Column(String(100))
	staffs = relationship('User', secondary=staff_course)
	resources = relationship('User', secondary=resource_course)

	workouts = relationship('Workout', secondary=course_workout, backref=backref('courses'))

	paybackTraningcard_id = Column(Integer, ForeignKey('trainingcardtype.id'))
	paybackTraningcard = relationship('TrainingCardType', uselist=False, foreign_keys=[paybackTraningcard_id])

	_json = Column(plug.db.JsonType)
	included_products = plug.db.VirtualColumn('included_products')
	included_products_amount = plug.db.VirtualColumn('included_products_amount')
	additional_products = plug.db.VirtualColumn('additional_products')
	questions = plug.db.VirtualColumn('questions')
	lastCancelTime = plug.db.VirtualColumn('lastCancelTime')
	cancelRules = plug.db.VirtualColumn('cancelRules')

	tags = relationship('SystemTag', secondary=course_systemtag)

	@hybrid_property
	def bookingscount(self):
		return len(db.not_removed(self.bookings))

	@bookingscount.expression
	def bookingscount(cls):
		return select([func.count(CourseBooking.id)]).where(and_(cls.id == CourseBooking.course_id, CourseBooking.removed == None)).label('bookingscount')

	@hybrid_property
	def reservationscount(self):
		return len(lfilter(lambda r: not r.expired(), self.reservations))

	# A calculated value of how many places there are left to book
	# Takes the total space value, reduces with number of bookings and reservations
	# Returns None if there is unlimited space
	@hybrid_property
	def spaceLeft(self):
		if self.space is None:
			return None
		res = max(0, self.space - self.bookingscount - self.reservationscount)
		for w in self.workouts:
			if w.space != None:
				res = min(res, w.spaceLeft())
		return res

	def getExtraData(self, res):
		res['spaceLeft'] = self.spaceLeft

	@hybrid_property
	def tagstext(self):
		return ', '.join(lmap(lambda x: x.name, self.tags or []))

	@tagstext.expression
	def tagstext(cls):
		j = join(db.SystemTag, course_systemtag, db.SystemTag.id == course_systemtag.c.systemtag_id)
		return select([func.group_concat(db.SystemTag.name)]).select_from(j).where(cls.id == course_systemtag.c.course_id).label('tagstext')

	@hybrid_property
	def watcherscount(self):
		return len(db.not_removed(self.watchers))

	@watcherscount.expression
	def watcherscount(cls):
		return select([func.count(CourseWatcher.id)]).where(and_(CourseWatcher.course_id == cls.id, CourseWatcher.removed == None)).label('watcherscount')

	@classmethod
	def getPermission(cls):
		return dict(add='Schedule handling', get='Show schedule', change='Schedule handling', remove='Schedule handling')

	@classmethod
	def getRequiredModules(cls):
		return 'Courses'

	def _getData(self):
		res = super(Course, self)._getData()
		res['staffs'] = lmap(lambda x: x._getMiniData(), db.not_removed(self.staffs))
		res['resources'] = lmap(lambda x: x._getMiniData(), db.not_removed(self.resources))
		res['tags'] = lmap(lambda x: x._getData(), self.tags)
		return res

	@classmethod
	def change(cls, apiData, c):
		with plug.db.commit_block():
			course = super(Course, cls).change(apiData, c)

			options = None
			if 'options' in c:
				options = c['options']

			if isinstance(options, dict) and not options.get('dontUpdate'):
				now = plug.date.now()
				futureWorkouts = lfilter(lambda w: w.startTime >= now, course.workouts)
				for workout in futureWorkouts:
					if options.get('updateStaffs'):
						workout.staffs = course.staffs

					if options.get('updateResources'):
						workout.resources = course.resources

				if futureWorkouts:
					db.Workout.update_resource_allocation(futureWorkouts, force=True)
					db.sendToChangeQueue('workout', futureWorkouts, 'change')

			return course

	@classmethod
	def addInternal(cls, c, performer):
		t = dict(type='course')
		t.update(c['product'])

		if not c.get('sites'):
			c['sites'] = [db.Site.main().id]

		product = db.TrainingCardType.addInternal(t, performer)
		db.session.flush()
		c['product_id'] = product.id
		if not c.get('paybackTraningcardsBool'):
			c['paybackTraningcard_id'] = None
		del c['product']

		return super(Course, cls).addInternal(c, performer)

	@classmethod
	def changeInternal(cls, c, performer):
		import db, myutil
		course = db.session.query(Course).options(db.joinedload('bookings')).get(c['id'])
		spaceIncreased = False
		if 'space' in c:
			space = c['space']
			usedSpace = course.bookingscount + course.reservationscount
			if space is not None and space < usedSpace:
				raise db.InvalidInputException('Already have more bookings')
			if (space != course.space and course.space is not None) and (space is None or space > course.space):
				spaceIncreased = True
			if not 'product' in c:
				c['product'] = {}
			if not c.get('paybackTraningcardsBool'):
				c['paybackTraningcard_id'] = None

		# No payback card was set - but is now
		# Find all bookings and change their cards
		if not course.paybackTraningcard and c.get('paybackTraningcard_id') and len(course.workouts):
			for booking in db.not_removed(course.bookings):
				paybackcard = db.TrainingCard.addInternal(user_id=booking.user.id, cardtype_id=c.get('paybackTraningcard_id'), validFromDate=course.startTime, price=0, validToDate=course.endTime, performer=performer,trainingsLeft=0, nocommit=True)
				for w in course.workouts:
					wb = myutil.find(w.bookings, lambda wb: wb.user_id == booking.user_id)
					if wb and not wb.trainingcard:
						wb.trainingcard = paybackcard

		if 'workouts' in c:
			to_add = []
			to_remove = []
			old_workouts = course.workouts
			workouts = db.getListFromObject(c, 'workouts', db.Workout)
			for w in workouts:
				if w not in old_workouts and w.startTime >= plug.date.now():
					to_add.append(w)
			for w in old_workouts:
				if w not in workouts and w.startTime >= plug.date.now():
					to_remove.append(w)

			for workout in to_add:
				for booking in db.not_removed(course.bookings):
					if not workout.hasBooking(booking.user):
						paybackcard = booking.get_paybackcard()
						if paybackcard:
							wb = db.WorkoutBooking.addInternal(workout=workout, member_id=booking.user.id, card=paybackcard, performer=performer, nocommit=True, skip_card_limits=True)
						else:
							wb = db.WorkoutBooking.addInternal(workout=workout, member_id=booking.user.id, use_card=False, performer=performer, nocommit=True)
						booking.bookings.append(wb)
			for workout in to_remove:
				for booking in db.not_removed(course.bookings):
					wb = myutil.find_where(booking.bookings, dict(workout_id=workout.id))
					if wb:
						db.WorkoutBooking.removeInternal(wb, performer=performer, nocommit=True)

		res = super(Course, cls).changeInternal(c, performer)
		if spaceIncreased:
			plug.course.notifyCourseWatchers(course)
		return res

	@classmethod
	def getChangableChildKeys(cls):
		tprops = ['name', 'price', 'vat', 'imagekey', 'account', 'costcenter_id', 'product_category_id', 'product_webshop_category_id', 'methods', 'description', 'requireMembership', 'barcode', 'customerCanBuy']
		return lmap(lambda x: 'product.' + x, tprops)

	@classmethod
	def getRelationships(cls):
		return lfilter(lambda rel: rel.name != 'reservations', super(Course, cls).getRelationships())

	@classmethod
	def getRelationshipConfig(cls):
		return {
			'bookings': {
				'getresult': 'id',
				'getresultfilter': 'removed'
			},
			'watchers': {
				'getresult': 'full',
				'getresultfilter': 'removed'
			},
			'category': {
				'getresult': 'id',
				'getresultfilter': 'removed'
			},
			'product': {
				'getresult': 'id',
				'getresultfilter': 'removed'
			},
			'sites': {
				'getresult': 'id',
				'getresultfilter': 'removed'
			},
			'workouts': {
				'getresult': 'id'
			}
		}


class CourseBooking(Base, plug.db.CRUDBase, plug.db.GetItem):
	course_id = Column(Integer, ForeignKey('course.id'))
	course = relationship('Course', uselist=False, backref=backref('bookings'))
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship('User', uselist=False, foreign_keys=[user_id])
	booker_id = Column(Integer, ForeignKey('user.id'))
	booker = relationship('User', uselist=False, foreign_keys=[booker_id])

	bookings = relationship('WorkoutBooking', secondary=coursebooking_workoutbooking)
	payments = relationship('Payment', secondary=coursebooking_payment)

	_json = Column(plug.db.JsonType)
	additional_products = plug.db.VirtualColumn('additional_products')
	answers = plug.db.VirtualColumn('answers')
	loyaltypoints_id = Column(Integer, ForeignKey('loyaltypoints.id'))
	cancelRules = plug.db.VirtualColumn('cancelRules')
	variants_for_included_products = plug.db.VirtualColumn('variants_for_included_products')

	@classmethod
	def getUserData(cls, user_id):
		bookings = db.session.query(CourseBooking).filter(CourseBooking.user_id == user_id).options(db.joinedload_all('course.product')).all()
		res = []
		for b in bookings:
			d = {}
			d['Created'] = b.created
			d['Course'] = b.course.product.name
			if b.answers:
				d['Answers'] = b.answers
			res.append(d)

		return res

	@classmethod
	def getPermission(cls):
		return dict(add='Workout booking', get='Schedule handling', change='Workout booking', remove='Workout booking')

	@classmethod
	def getRequiredModules(cls):
		return 'Courses'

	# FIXME: Instead try to avoid getting circular
	def _getData(self):
		res = super(CourseBooking, self)._getData()
		res['course'] = dict(id=self.course.id, product=self.course.product, additional_products=self.course.additional_products, questions=self.course.questions, cancelRules=self.cancelRules, variants_for_included_products=self.variants_for_included_products)
		return res

	@classmethod
	def addInternal(cls, c, performer, nocommit=False):
		cb = super(CourseBooking, cls).addInternal(c, performer, nocommit)
		if db.Module.has('LoyaltyPoints'):
			# Check if booking should give loyalty points
			if cb.course.loyaltypointactivities:
				plug.loyaltypoints.check_loyaltypoint_terms(cb.user.id, performer=performer, booking=cb)
		return cb

	@classmethod
	def getRelationshipConfig(cls):
		return {
			'payments': {
				'getresult': 'full'
			}
		}

	def get_paybackcard(self):
		for b in self.bookings:
			if b.trainingcard:
				return b.trainingcard

class CourseWatcher(Base, plug.db.CRUDBase, plug.db.GetItem):
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship('User', uselist=False, foreign_keys=[user_id])
	course_id = Column(Integer, ForeignKey('course.id'))
	course = relationship('Course', uselist=False, backref=backref('watchers'))
	mail = Column(Boolean)
	sms = Column(Boolean)
	hash = Column(String(32))

	def _getData(self):
		return dict(id=self.id, user_id=self.user_id, course_id=self.course_id, mail=self.mail, sms=self.sms)

@plug.on('migrate')
def migration(argv):
	import db
	CourseCategory.__table__.create(db.engine, checkfirst=True)
	Course.__table__.create(db.engine, checkfirst=True)
	CourseBooking.__table__.create(db.engine, checkfirst=True)
	coursebooking_workoutbooking.create(db.engine, checkfirst=True)
	course_workout.create(db.engine, checkfirst=True)
	course_systemtag.create(db.engine, checkfirst=True)
	staff_course.create(db.engine, checkfirst=True)
	resource_course.create(db.engine, checkfirst=True)
	coursebooking_payment.create(db.engine, checkfirst=True)
	plug.db.ensure_column(Course.space)
	site_coursecategory.create(db.engine, checkfirst=True)
	site_course.create(db.engine, checkfirst=True)
	plug.db.ensure_column(CourseCategory.sort)
	plug.db.ensure_column(Course.paybackTraningcard_id)
	plug.db.ensure_column(CourseBooking.booker_id)
	plug.db.ensure_column(Course.canCancel)
	plug.db.ensure_column(Course.firstBookingTime)
	plug.db.ensure_column(Course.canBookForOthers)
	plug.db.ensure_column(Course.refundProducts)
	plug.db.ensure_table(CourseWatcher, engine=db.engine)
	plug.db.ensure_column(Course.url)
	plug.db.ensure_column(CourseWatcher.hash)
	plug.db.ensure_column(CourseCategory.imagekey)
	plug.db.ensure_column(CourseCategory.description)
	plug.db.ensure_column(Course.canBookFor)

@plug.migrate_once
def migrate_course_site():
    import db

    main_site = db.Site.main()

    for category in db.session.query(CourseCategory).all():
    	if not category.sites:
        	category.sites = [main_site]

    for course in db.session.query(Course).all():
    	if not course.sites:
        	course.sites = [main_site]

@plug.migrate_once
def oldsortincoursecategory():
	filter = (CourseCategory.sort == None)
	for coursecategory in CourseCategory.getInternal(filter=filter):
		coursecategory.sort = 'created'

@plug.migrate_once
def set_booker_20210326():
	for booking in db.session.query(CourseBooking).filter(CourseBooking.booker_id == None):
		booking.booker_id = booking.user_id

@plug.migrate_once
def remove_stock_20210328():
	for course in db.session.query(Course).all():
		if course.product:
			course.product.stock = None

@plug.migrate_once
def firstBookingTime_20210329():
	for course in db.session.query(Course).filter(Course.firstBookingTime == None).all():
		course.firstBookingTime = course.created

@plug.migrate_once
def seturl_20210409():
	for course in db.session.query(Course).filter(Course.url == None).all():
		course.url = 'https://' + db.gymname + '/member#/coursebook/' + str(course.id)

@plug.migrate_once
def setcanbookfor_20210914():
	for course in db.session.query(Course).all():
		course.canBookFor = 'self+others' if course.canBookForOthers else 'self'
