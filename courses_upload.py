### CS122, Winter 2020: Course search engine: search
###
### Jason Zhang

from math import radians, cos, sin, asin, sqrt
import sqlite3
import os


# Use this filename for the database
DATA_DIR = os.path.dirname(__file__)
DATABASE_FILENAME = os.path.join(DATA_DIR, 'course-info.db')

OUTPUT_ATTRIBUTES = {
'terms': [True, True, False, False, False, False, False, False, False, True],
'dept': [True, True, False, False, False, False, False, False, False, True],
'day': [True, True, True, True, True, True, False, False, False, False],
'time_start': [True, True, True, True, True, True, False, False, False, False],
'time_end': [True, True, True, True, True, True, False, False, False, False],
'walking_time': [True, True, True, True, True, True, True, True, False, False],
'building': [True, True, True, True, True, True, True, True, False, False],
'enroll_lower': [True, True, True, True, True, True, False, False, True, False],
'enroll_upper': [True, True, True, True, True, True, False, False, True, False]
}

ATTRIBUTES = {'dept': 'courses', 'course_num': 'courses',\
'section_num': 'sections', 'day': 'meeting_patterns', \
'time_start': 'meeting_patterns', 'time_end': 'meeting_patterns',\
'building_code': 'sections', 'walking_time': None, \
'enrollment': 'sections', 'title': 'courses'}

KEYS = list(ATTRIBUTES.keys())
TABLES = list(ATTRIBUTES.values())


def output_variable_list(args_from_ui):
	'''
	From the input dictionary, generate the list of variables to output encoded 
	in Boolean form.

	Input:
		args_from_ui: a dictionary

	Output:
		a list of Booleans
	'''
	l = [False, False, False, False, False, False, False, False, False, False]
	for i in args_from_ui:
		l_new = []
		for j in range(0, 10):
			l_new.append(l[j] or OUTPUT_ATTRIBUTES[i][j])
		l = l_new
	return l


def available_buildings(building_code, walking_time):
	'''
	Given the starting building code and a walking time, return the list of 
	buildings that can be reacted within the walking time.

	Input: 
		building_code: string
		walking_time: integer

	Output:
		list of strings
	'''
	db = sqlite3.connect(DATABASE_FILENAME)
	c = db.cursor()
	db.create_function("time_between", 4, compute_time_between)
	st = '''SELECT gps.building_code FROM gps WHERE
	(gps.building_code, ?) in (SELECT a.building_code, b.building_code
	FROM gps AS a JOIN gps AS b
	WHERE a.building_code < b.building_code AND 
	time_between(a.lon, a.lat, b.lon, b.lat) <= ?)
	'''

	r1 = c.execute(st, [building_code, walking_time])
	rf = r1.fetchall()
	return rf

	s2 = \
	'''
	SELECT gps.building_code, gps.lat, gps.lon
	FROM gps
	WHERE gps.building_code = ?;
	'''
	r2 = c.execute(s2, [building_code])
	building_original, lon_original, lat_original = r2.fetchall()[0]
	available = []
	for building in rf:
		dist = compute_time_between(building[1], building[2], \
			lon_original, lat_original)
		if dist <= walking_time:
			available.append(building[0])
	return available


def process_args(args_from_ui, index, set):
	'''
	Given a dictionary and a value, return the appropriate SQL
	WHERE parameter. In addition, modify the set of strings that contains the 
	tables from which columns are taken, so that it includes every table 
	necessary.

	Input:
		index: a string (e.g. 'terms')
		set: a set of strings

	Output:
		a string (the WHERE parameter) and a list of one or more elements
		 (corresponding to ?)
	'''
	if index in ['terms']:
		set.add('catalog_index')
	elif index in ['building', 'walking_time']:
		set.add('gps')
	if index == 'dept':
		return ATTRIBUTES[index] + '.' + index + ' = ?', [args_from_ui[index]]
	if index == 'time_start' or index == 'enroll_lower':
		return ATTRIBUTES[index] + '.' + index + ' >= ?', [args_from_ui[index]]
	if index == 'time_end' or index == 'enroll_upper':
		return ATTRIBUTES[index] + '.' + index + ' <= ?', [args_from_ui[index]]
	if index == 'day':
		l = []
		arg = []
		for i in args_from_ui[index]:
			l.append(ATTRIBUTES[index] + '.' + index + ' = ?')
			arg.append(i)
		return '(' + ' OR '.join(l) + ')', arg
	if index == 'walking_time':
		st = \
		'''(gps.building_code, ?) in (SELECT a.building_code, b.building_code
		FROM gps AS a JOIN gps AS b
		WHERE a.building_code < b.building_code AND 
		time_between(a.lon, a.lat, b.lon, b.lat) <= ?)'''
		return st, [args_from_ui['building'], args_from_ui['walking_time']]
	if index == 'terms':
		st = '(SELECT catalog_index.course_id AS num' + \
		' FROM catalog_index WHERE '
		l = []
		terms = args_from_ui[index].split(' ')
		for i in terms:
			l.append('catalog_index.word = ?')
		st += ' OR '.join(l) + ' GROUP BY catalog_index.course_id' + \
		' HAVING COUNT(*) = ' + str(len(terms)) + ')'
		return 'catalog_index.course_id in ' + st, terms
	if index == 'building':
		return None, None


def generate_sql(args_from_ui):
	'''
	Generate the SQL search string from the input dictionary.

	Input: 
		args_from_ui: a dictionary

	Output:
		a string
	'''
	st = 'SELECT '
	l_select = []
	output_varibles = output_variable_list(args_from_ui)
	for i in range(0, 10):
		if output_varibles[i] and TABLES[i] != None:
			l_select.append(TABLES[i] + '.' + KEYS[i])
	st += ', '.join(l_select) + ' FROM '
	s_from = set(['sections', 'courses', 'meeting_patterns'])
	l_where = []
	args = []
	for i in args_from_ui:
		where_param, element = process_args(args_from_ui, i, s_from)
		if element != None:
			l_where.append(where_param)
			args += element
	st += ' JOIN '.join(list(s_from))
	st += ' ON courses.course_id = sections.course_id AND ' + \
	'sections.meeting_pattern_id = meeting_patterns.meeting_pattern_id WHERE '
	st += ' AND '.join(l_where) + ';'
	return st, args


def find_courses(args_from_ui):
	'''
	Takes a dictionary containing search criteria and returns courses
	that match the criteria.  The dictionary will contain some of the
	following fields:

		- dept a string
		- day a list with variable number of elements
			 -> [''MWF'', ''TR'', etc.]
		- time_start an integer in the range 0-2359
		- time_end an integer in the range 0-2359
		- walking_time an integer
		- enroll_lower an integer
		- enroll_upper an integer
		- building a string
		- terms a string: 'quantum plato']

	Returns a pair: list of attribute names in order and a list
	containing query results.
	'''
	db = sqlite3.connect(DATABASE_FILENAME)
	db.create_function("time_between", 4, compute_time_between)
	c = db.cursor()
	s, args = generate_sql(args_from_ui)
	r = c.execute(s, args)
	rf = r.fetchall()
	if rf == []:
		return ([],[])
	else:
		return (get_header(c), rf)



'''
Helper Function that 

########### auxiliary functions #################
########### do not change this code #############
'''


def compute_time_between(lon1, lat1, lon2, lat2):
	'''
	Converts the output of the haversine formula to walking time in minutes
	'''
	meters = haversine(lon1, lat1, lon2, lat2)

	# adjusted downwards to account for manhattan distance
	walk_speed_m_per_sec = 1.1
	mins = meters / (walk_speed_m_per_sec * 60)

	return mins


def haversine(lon1, lat1, lon2, lat2):
	'''
	Calculate the circle distance between two points
	on the earth (specified in decimal degrees)
	'''
	# convert decimal degrees to radians
	lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

	# haversine formula
	dlon = lon2 - lon1
	dlat = lat2 - lat1
	a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
	c = 2 * asin(sqrt(a))

	# 6367 km is the radius of the Earth
	km = 6367 * c
	m = km * 1000
	return m


def get_header(cursor):
	'''
	Given a cursor object, returns the appropriate header (column names)
	'''
	desc = cursor.description
	header = ()

	for i in desc:
		header = header + (clean_header(i[0]),)

	return list(header)


def clean_header(s):
	'''
	Removes table name from header
	'''
	for i, _ in enumerate(s):
		if s[i] == '.':
			s = s[i + 1:]
			break

	return s


########### some sample inputs #################

EXAMPLE_0 = {'time_start': 930,
			 'time_end': 1500,
			 'day': ['MWF']}

EXAMPLE_1 = {'dept': 'CMSC',
			 'day': ['MWF', 'TR'],
			 'time_start': 1030,
			 'time_end': 1500,
			 'enroll_lower': 20,
			 'terms': 'computer science'}
