import math
import operator


def is_expression(value):
	return issubclass(type(value), Expression)


def ensure_expression(value):
	if is_expression(value):
		return value
	if type(value) in [str, int, float]:
		return Literal(value)
	if type(value) is ProcCall:
		raise Exception("Scratch procedure calls cannot be used as expressions!")
	raise Exception(f"Can't interpret {value!r} as Expression")


class Expression():
	type = "generic"

	def __init__(self):
		raise Exception("Expression can't be instantiated directly (Maybe you want a Literal?)")
	
	def __add__(self, other):
		return BinaryOp("+", self, other)
	
	def __sub__(self, other):
		return BinaryOp("-", self, other)
	
	def __neg__(self):
		return Literal(0) - self
	
	def __mul__(self, other):
		return BinaryOp("*", self, other)
	
	def __mod__(self, other):
		return BinaryOp("%", self, other)
	
	def __truediv__(self, other):
		return BinaryOp("/", self, other)
	
	def __floordiv__(self, other):
		return (self / other).__floor__()
	
	def __eq__(self, other):
		return BinaryOp("==", self, other)
	
	def __ne__(self, other):
		return BinaryOp("==", self, other).NOT()
	
	def __gt__(self, other):
		return BinaryOp(">", self, other)
	
	def __lt__(self, other):
		return BinaryOp("<", self, other)
	
	def __floor__(self):
		return UnaryOp("floor", self)
	
	def __ceil__(self):
		return UnaryOp("ceiling", self)

	def __round__(self):
		return UnaryOp("round", self)
	
	def round(self):
		return self.__round__()
	
	def __abs__(self):
		return UnaryOp("abs", self)
	
	def sqrt(self):
		return UnaryOp("sqrt", self)
	
	def sin(self):
		return UnaryOp("sin", self)
	
	def cos(self):
		return UnaryOp("cos", self)

	def atan(self):
		return UnaryOp("atan", self)
	
	def log(self):
		return UnaryOp("ln", self)

	def log10(self):
		return UnaryOp("log", self)
	
	def __pow__(self, other):
		return UnaryOp("e ^", (self.log() * other))
	
	def root(self, other):
		return UnaryOp("e ^", (self.log() / other))
	
	def __rshift__(self, other):
		if type(other) is int:
			return self // (1 << other)
		return self // round(Literal(2) ** other) # exponentiation relies on log, so results need rounding
	
	def __lshift__(self, other):
		if type(other) is int:
			return self * (1 << other)
		return self * round(Literal(2) ** other) # exponentiation relies on log, so results need rounding
	
	def __and__(self, other):
		if not type(other) is int:
			raise Exception("Can only AND with constant (for now)")
		is_low_mask = (other & (other + 1) == 0)
		if not is_low_mask:
			raise Exception("AND can only be used to mask off low bits, for now")
		return self % (other + 1)
	
	def __getitem__(self, other):
		return BinaryOp("[]", ensure_expression(other+1).simplified(), self)

	def item(self, other):
		return BinaryOp("[]", ensure_expression(other), self)

	def len(self):
		return UnaryOp("len", self)

	def join(self, other):
		return BinaryOp("join", self, other)
	
	def simplified(self):
		return self
	
	def OR(self, other):
		return BinaryOp("||", self, other)
	
	def AND(self, other):
		return BinaryOp("&&", self, other)
	
	def NOT(self):
		return UnaryOp("!", self)


class Literal(Expression):
	def __init__(self, value):
		assert(type(value) in [str, int, float])
		self.value = value
	
	def __repr__(self):
		#return f"Literal({self.value!r})"
		return repr(self.value)


class LiteralColour(Expression):
	def __init__(self, value):
		self.value = value

	def __repr__(self):
		return f"LiteralColour({self.value!r})"


class BinaryOp(Expression):
	def __init__(self, op, lval, rval):
		self.op = op
		self.lval = ensure_expression(lval)
		self.rval = ensure_expression(rval)

		if op in [">", "<", "==", "&&", "||"]:
			self.type = "bool"
	
	def __repr__(self):
		return f"BinaryOpExpression({self.lval!r} {self.op} {self.rval!r})"
	
	def simplified(self):
		# todo: don't modify in-place...
		simpler = BinaryOp(self.op, self.lval.simplified(), self.rval.simplified())
		#print(simpler)

		#print("simplifying:", self)
		match simpler:
			case BinaryOp(
				lval=Literal(value=int()|float()),
				op="+"|"-"|"%"|"*"|"/",
				rval=Literal(value=int()|float())
			):
				opmap = {
					"+": operator.add,
					"-": operator.sub,
					"%": operator.mod,
					"*": operator.mul,
					"/": operator.truediv,
				}

				# convert the inputs to floats, to emulate scratch's arithmetic
				value =  opmap[simpler.op](float(simpler.lval.value), float(simpler.rval.value))
				if value == math.floor(value):
					value = int(value) # if we can, convert back to int, to avoid redundant ".0"s in the output
				return Literal(value)
			
			# foo * 1 => foo
			case BinaryOp(op=("*"|"/"), rval=Literal(value=1)):
				return simpler.lval

			# 1 * foo => foo
			case BinaryOp(lval=Literal(value=1), op="*"):
				return simpler.rval

			# foo + 0  =>  foo
			case BinaryOp(op=("+"|"-"), rval=Literal(value=0)):
				return simpler.lval
			
			# 0 + foo  =>  foo
			case BinaryOp(lval=Literal(value=0), op="+"):
				return simpler.rval

			# ((foo + a) + b)  =>  (foo + (a+b))
			case BinaryOp(
				lval=BinaryOp(
					lval=subexpr,
					op=("+"|"-"),
					rval=Literal()
				),
				op=("+"|"-"),
				rval=Literal()
			):
				a = simpler.rval.value if simpler.op == "+" else -simpler.rval.value
				b = simpler.lval.rval.value if simpler.lval.op == "+" else -simpler.lval.rval.value
				val = a + b
				if val == 0:
					return subexpr
				return BinaryOp("+", subexpr, val)

		return simpler


class UnaryOp(Expression):
	def __init__(self, op, value):
		self.op = op
		self.value = ensure_expression(value)

		if op == "!":
			self.type = "bool"
	
	#def simplified(self):
	#	return UnaryOp(self.op, self.value.simplified())

	def __repr__(self):
		return f"UnaryOpExpression({self.op}({self.value!r}))"


class Var(Expression):
	def __init__(self, sprite, name, uid):
		self.sprite = sprite
		self.name = name
		self.uid = uid
	
	def __le__(self, other):
		other = ensure_expression(other)

		# If other is (self+x) or (x+self), optimise to "change by"
		if type(other) is BinaryOp and other.op == "+":
			#print(repr(other))
			if other.lval is self:
				return Statement("data_changevariableby", VARIABLE=self, VALUE=other.rval)
			elif other.rval is self:
				return Statement("data_changevariableby", VARIABLE=self, VALUE=other.lval)
		
		return Statement("data_setvariableto", VARIABLE=self, VALUE=other)
	
	def __getitem__(self, _slice):
		if type(_slice) is not slice:
			#raise Exception("You can't index a non-list variable")
			return super().__getitem__(_slice)

		return VarRangeIterationHack(self, _slice.start, _slice.stop, _slice.step)

	def changeby(self, other):
		return Statement("data_changevariableby", VARIABLE=self, VALUE=ensure_expression(other))

	def __repr__(self):
		return f"Var({self.sprite.name}: {self.name})"

class VarRangeIterationHack():
	def __init__(self, var, start, stop, step):
		self.var = var
		self.start = 0 if start is None else start
		self.stop = stop
		self.step = 1 if step is None else step
	
	def __rshift__(self, values):
		if type(self.start) is int and type(self.stop) is int and type(self.step) is int:
			return varloop(self.var, range(self.start, self.stop, self.step), values)
		else:
			return condvarloop(self.var, self.start, self.stop, self.step, values)

class List(Expression):
	def __init__(self, sprite, name, uid):
		self.sprite = sprite
		self.name = name
		self.uid = uid
	
	def append(self, other):
		return Statement("data_addtolist", LIST=self, ITEM=ensure_expression(other))

	def delete_all(self):
		return Statement("data_deletealloflist", LIST=self)
	
	def delete_at(self, other):
		return Statement("data_deleteoflist", LIST=self, INDEX=(ensure_expression(other)+1).simplified())

	def delete_at1(self, other):
		return Statement("data_deleteoflist", LIST=self, INDEX=ensure_expression(other))

	def len(self):
		return UnaryOp("listlen", self)
	
	def index(self, other):
		return ListItemNum(self, other) - 1

	def index1(self, other):
		return ListItemNum(self, other)

	def __repr__(self):
		return f"ListVar({self.sprite.name}: {self.name})"
	
	def __getitem__(self, index):
		return ListIndex(self, (ensure_expression(index)+1).simplified())
	
	def item(self, one_index):
		return ListIndex(self, one_index)
	
	def contains(self, thing):
		return ListContains(self, thing)

class ListItemNum(Expression):
	def __init__(self, list_, item):
		self.list = list_
		self.item = ensure_expression(item)

class ListIndex(Expression):
	def __init__(self, list_, index):
		self.list = list_
		self.index = ensure_expression(index)
	
	def __le__(self, other):
		other = ensure_expression(other)
		return Statement("data_replaceitemoflist", LIST=self.list, INDEX=self.index, ITEM=other)
	
	def __repr__(self):
		return f"{self.list!r}[{self.index!r}]"

class ListContains(Expression):
	type = "bool"
	def __init__(self, list_, thing):
		self.list = list_
		self.thing = ensure_expression(thing)

class Statement():
	def __init__(self, op, **args):
		self.op = op
		self.args = args
	
	def __repr__(self):
		return f"Statement({self.op}, {self.args!r})"

class ElseHack():
	def __init__(self, condition, then):
		self.condition = condition
		self.then = then
	
	def __getitem__(self, do):
		if type(do) != tuple:
			do = [do]
		return IfElseStatement(self.condition, self.then, list(do))

class IfStatement(Statement):
	def __init__(self, condition, then):
		super().__init__("control_if", CONDITION=ensure_expression(condition), SUBSTACK=then)
		self.Else = ElseHack(condition, then)

class IfElseStatement(Statement):
	def __init__(self, condition, then, elsedo):
		super().__init__("control_if_else", CONDITION=ensure_expression(condition), SUBSTACK=then, SUBSTACK2=elsedo)






class ProcDef(Statement):
	def __init__(self, proto, generator):
		self.op = "procedures_definition"
		self.proto = proto
		self.generator = generator # todo: maybe store generator inside proto?
	
	def __call__(self, *args):
		if len(args) != len(self.proto.vars):
			raise Exception(f"{self!r} expects {len(self.proto.vars)} args, {len(args)} given")
		
		return ProcCall(self, args, self.generator)
	
	def __getattr__(self, attr):
		varname = self.proto.locals_prefix + attr
		return self.proto.sprite.new_var(varname)

	def __repr__(self):
		return f"ProcDef({self.proto!r})"

class ProcProto(Statement):
	def __init__(self, sprite, fmt, uid, locals_prefix, turbo=True):
		self.op = "procedures_prototype"
		self.sprite = sprite
		self.uid = uid
		self.fmt = fmt
		self.locals_prefix = fmt + ":" if locals_prefix is None else locals_prefix
		self.turbo = turbo

		# quick and dirty parser state machine
		# [square] brackets denote numeric/string args, <triangle> brackets denote bool args
		# (does anyone ever actually use bool args?)
		self.argtypes = []
		self.proccode = ""
		self.argnames = []
		mode = "label"
		for char in fmt:
			if mode == "label":
				if char == "[":
					self.argtypes.append("generic")
					self.argnames.append("")
					self.proccode += "%s"
					mode = "strarg"
				elif char == "<":
					self.argtypes.append("bool")
					self.argnames.append("")
					self.proccode += "%b"
					mode = "boolarg"
				else:
					self.proccode += char
			elif mode == "strarg":
				if char == "]":
					mode = "label"
				else:
					self.argnames[-1] += char
			elif mode == "boolarg":
				if char == ">":
					mode = "label"
				else:
					self.argnames[-1] += char
			else:
				raise Exception("Invalid parser state")
		
		#print(self.argtypes, self.proccode, self.argnames)

		# NOTE: codegen will initialise self.vars
		self.vars = []
	
	def __repr__(self):
		return f"ProcProto({self.fmt!r})"


class ProcCall(Statement):
	def __init__(self, proc, args, generator, turbo=True):
		self.procdef = proc # todo: fix these field names lol
		self.proc = proc.proto
		self.argv = list(map(ensure_expression, args))
		self.generator = generator

		for arg, argtype in zip(self.argv, proc.proto.argtypes):
			if argtype == "bool" and arg.type != "bool":
				raise Exception("Cannot pass non-boolean expression to boolean proc arg")
		
		super().__init__("procedures_call", PROC=proc.proto.uid, ARGS=self.argv)
	
	def inline(self):
		return self.generator(self.procdef, *self.argv) # todo use better variable namespacing


class ProcVar(Expression):
	def __init__(self, sprite, procproto, name, uid, uid2):
		self.sprite = sprite
		self.procproto = procproto
		self.name = name
		self.uid = uid
		self.uid2 = uid2
	
	def __repr__(self):
		return f"ProcVar({self.procproto.fmt!r}: {self.name})"

class ProcVarBool(Expression):
	def __init__(self, sprite, procproto, name, uid, uid2):
		self.type = "bool"
		self.sprite = sprite
		self.procproto = procproto
		self.name = name
		self.uid = uid
		self.uid2 = uid2
	
	def __repr__(self):
		return f"ProcVarBool({self.procproto.fmt!r}: {self.name})"


def getitem_hack(fn, *args):
	class GetitemHack():
		def __init__(self, *args):
			self.args = args
		
		def __getitem__(self, then):
			if type(then) != tuple:
				then = [then]
			return fn(*self.args, list(then))
	
	return GetitemHack(*args)

def varloop(var, _range, body): return [
	var <= _range.start,
	repeatn(len(_range),
		body + 
		[ var <= var + _range.step ]
	)
]

# when number of iterations not known at compile-time
def condvarloop(var, start, stop, step, body): return [
	var <= start,
	repeatuntil((var + 1).simplified() > stop,
		body +
		[var.changeby(step)]
	)
]

def repeatn(times, body=None):
	if body is None:
		return getitem_hack(repeatn, times)
	return Statement("control_repeat", TIMES=ensure_expression(times), SUBSTACK=body)

def repeatuntil(cond, body=None):
	if body is None:
		return getitem_hack(repeatuntil, cond)
	return Statement("control_repeat_until", CONDITION=ensure_expression(cond), SUBSTACK=body)

def on_flag(substack=None):
	return [Statement("event_whenflagclicked")] + substack

def on_receive(event, event_uid, substack=None):
	return [Statement("event_whenbroadcastreceived", BROADCAST_OPTION=[str(event), event_uid])] + substack

def on_press(key, substack=None):
	# TODO: use enum for key, check the argument is actually an enum field
	return [Statement("event_whenkeypressed", KEY_OPTION=str(key))] + substack

class MenuExpression(Expression):
	pass

class PenParamMenu(MenuExpression):
	def __init__(self, param):
		self.op = "pen_menu_colorParam"
		self.param = param

# todo: probably need one of these for costume selection
class TouchingObjectMenu(MenuExpression):
	def __init__(self, object):
		self.op = "sensing_touchingobjectmenu"
		self.object = object

class Costume(MenuExpression):
	def __init__(self, costume):
		self.op = "looks_costume"
		self.costumename = costume

class Instrument(MenuExpression):
	def __init__(self, instrument):
		if type(instrument) is not int:
			raise TypeError()
		self.op = "music_menu_INSTRUMENT"
		self.instrument = instrument

class Drum(MenuExpression):
	def __init__(self, drum):
		if type(drum) is not int:
			raise TypeError()
		self.op = "music_menu_DRUM"
		self.drum = drum

if __name__ == "__main__":
	class Sprite():
		name = "Sprite"
	s = Sprite()
	print(math.floor((Var(s, "foo", None) + 7 + 3) * 5) == Literal(3) / 5)
	print(List(s, "bar", None)[5])
	print(Literal(3) + 4)
	print(Literal(123) >> 2)
	print(Literal(1234123) & 0xFF)
	print(Literal(5) > 7)
	#List("foo")[5] = 123
