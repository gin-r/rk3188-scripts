'''Try to find target related GPIO pins for rk3xxx android device. 
It is expected to be started in directory containing GPIO dumps made using  Gormar's gpio_dump_opt.sh.
Which can be found here (page 3) together with other required tools and description:  
http://www.freaktab.com/showthread.php?7021-GPIO-module-to-check-gpios-in-wifi-and-bt-Lets-make-the-wifi-and-BT-work-in-more-devices
'''

import re, argparse
from os import listdir
from os.path import isfile

#
# File format for gpio_dump_opt.sh
# Meaningfull strins are like '160: RK30_PIN0_PA0 = 1'
# gpio_number: gpio_name = onoff_state
# 
LINE_PATTERN = re.compile( '([0-9]+): ([^ ]+) = ([01])' )

# GPIO name dictionary
names = None

# Command line arguments parsed
args = None

def v( s ):
	if args.verbose:
		print( s )

def load_state( fname ):
	''' Loads GPIO state from named file.'''

	f = open( fname )

	#
	# File format for gpio_dump_opt.sh
	# Meaningfull strins are like '160: RK30_PIN0_PA0 = 1'
	# gpio_number: gpio_name = onoff_state
	# 
	lp = re.compile('([0-9]+): ([^ ]+) = ([01])')

	state = {}

	for l in f:
		res = LINE_PATTERN.match(l)
		if(res):
			n, name, onoff = int(res.group(1)), res.group(2), int(res.group(3))
			state[n] = onoff
	f.close()
	return state

def load_names( fname ):
	''' Loads GPIO names from named file.'''
	v( 'Loading names from file ' + fname   )
	f = open( fname )
	names = {}
	for l in f:
		res = LINE_PATTERN.match(l)
		if(res):
			n, name, onoff = int(res.group(1)), res.group(2), int(res.group(3))
			names[n] = name
	f.close()
	return names

def load_states( prefix ):
	''' Loads state sets and GPIO names from files. Returns states, names.'''
	global names

	fp = re.compile('.*' + prefix + '([01]).*')
	states = [[],[]]
	for fname in listdir('.') :
		if isfile( fname ):
			res = fp.match(fname)
			if( res ):
				n = int(res.group(1))
				v( 'Loading file ' + fname + ' target ' + prefix + ' state ' + str(n) )
				state = load_state( fname )
				v( str(len(state)) + ' GPIO states read successfully'   )
				states[n].append( state )
				if names is None :
					names = load_names( fname )
	check_states(states)
	return states
	
def check_states( states ):
	ng = -1
	nums = None
	for ss in states:
		if len(ss) == 0:
			print('Error: Not all required state files present')
			exit(1)
		for s in ss:
			if ng >= 0:
				if len(s) != ng:
					print('Error: Different number of GPIOs in files')
					exit(1)
				if s.keys() != nums:
					print('Error: Different sets of GPIOs in files')
					exit(1)
			else:
			 ng = len(s)
			 nums = s.keys()

			
def find_wrong( ss ):
	'''Find GPIOS which change it's state. ss should be list of states with the same target pin on/off state.'''
	wrong = []
	for key, onoff in  ss[0].items(): 
		for s in ss[1:]:
			if s[key] != onoff:
				wrong.append(key)
	return wrong
		
def find_01( s0, s1):
	'''Find GPIOS which change state from 0 to 1.'''
	ok = []
	for key in s0.keys():
		if s0[key] == 0 and s1[key] == 1:
			ok.append(key) 
	return ok

def find_10( s0, s1):
	'''Find GPIOS which change state from 1 to 1.0'''
	ok = []
	for key in s0.keys():
		if s0[key] == 1 and s1[key] == 0:
			ok.append(key) 
	return ok


def gpios( states0, states1, tr_from = 0 ):
	'''Find GPIO pins given states0 where target is off and states1 where target is on.'''
	if( tr_from == 0 ):
		tr = find_01(states0[0], states1[0])
	else:
		tr = find_10(states0[0], states1[0])
	wrong = find_wrong( states0 ) + find_wrong( states1 )
	return set(tr) - set(wrong) 
	
def print_gpios(l, names):
	''' Print GPIOS from list l, using names dictionary.'''
	for g in l:
		print(g, names[g])	

#
#
#	

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('targets', metavar='target', nargs='*', default=['w','b'],
                   help='Target marks to process. Default w b.')
parser.add_argument('-v', dest='verbose', action='store_const',
                   const=True, default=False,
                   help='Print verbose output')
parser.add_argument('-1', dest='output_10', action='store_const',
                   const=True, default=False,
                   help='Output 1->0 transition in addition to 0->1')
args = parser.parse_args()

v('Processing targets ' + str(args.targets))

# Transition direction marker
if not(args.output_10) :
	# Print none if only one direction required
	mrk01 = ''
	mrk10 = None
else:
	mrk01 = ' 0->1'
	mrk10 = ' 1->0'


for prefix in  args.targets:
	states = load_states(prefix)

	gpios_ok = gpios( states[0], states[1] )
	print( '== ' + prefix + mrk01 + ' ==' )
	print_gpios( gpios_ok, names )

	if args.output_10:
		gpios_ok = gpios( states[0], states[1], 1 )
		print( '== ' + prefix + mrk10 + ' ==' )
		print_gpios( gpios_ok, names )


