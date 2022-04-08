import random

_SOUP = '!#%()*+,-./:;=?@[]^_`{|}~' + \
	       'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'

def gen_uid():
	return "".join(random.choices(_SOUP, k=20))

