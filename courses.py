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
'sections.building_code': 'sections', 'walking_time': None, \
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


def process_args(args_from_ui, index, set):
	'''
	Given a dictionary and a value, return the appropriate SQL
	WHILE parameter. In addition, modify the set of strings that contains the 
	tables from which columns are taken, so that it includes every table 
	necessary.

	Input:
		index: a string (e.g. 'terms')
		set: a set of strings

	Output:
		a string
	'''
	if index in ['terms']:
		set.add('catalog_index')
	elif index in ['building', 'walking_time']:
		set.add('gps')
	if index == 'dept':
		return ATTRIBUTES[index] + '.' + index + ' = "' + \
		args_from_ui[index] + '"'
	if index == 'time_start' or index == 'enroll_lower':
		return ATTRIBUTES[index] + '.' + index + \
		' >= ' + str(args_from_ui[index])
	if index == 'time_end' or index == 'enroll_upper':
		return ATTRIBUTES[index] + '.' + index + \
		' <= ' + str(args_from_ui[index])
	if index == 'day':
		l = []
		for i in args_from_ui[index]:
			l.append(ATTRIBUTES[index] + '.' + index + ' = "' + i + '"')
		return '(' + ' OR '.join(l) + ')'
	if index == 'walking_time':
		return None
	if index == 'terms':
		l = []
		terms = args_from_ui[index].split(' ')
		for i in terms:
			l.append('catalog_index.word = "' + i + '"')
		return '(' + ' AND '.join(l) + ')'



def generate_sql(args_from_ui):
	'''
	Generate the SQL search string from the input dictionary.

	Input: 
		args_from_ui: a dictionary

	Output:
		a string
	'''
	str = 'SELECT '
	l_select = []
	output_varibles = output_variable_list(args_from_ui)
	for i in range(0, 10):
		if output_varibles[i]:
			l_select.append(TABLES[i] + '.' + KEYS[i])
	str += ', '.join(l_select) + ' FROM '
	s_from = set(['sections', 'courses', 'meeting_patterns'])
	l_where = []
	for i in args_from_ui:
		l_where.append(process_args(args_from_ui, i, s_from))
	str += ' JOIN '.join(list(s_from))
	str += ' ON courses.course_id = sections.course_id AND ' + \
	'sections.meeting_pattern_id = meeting_patterns.meeting_pattern_id WHERE '
	str += ' AND '.join(l_where)
	return str + ';'


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
	return ([], [])



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
