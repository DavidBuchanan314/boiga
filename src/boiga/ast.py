import math


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
	
	def __abs__(self):
		return UnaryOp("abs", self)
	
	def __rshift__(self, other):
		if not type(other) is int:
			raise Exception("Can only rshift by constant (for now)")
		return self // (1 << other)
	
	def __lshift__(self, other):
		if not type(other) is int:
			raise Exception("Can only lshift by constant (for now)")
		return self * (1 << other)
	
	def __and__(self, other):
		if not type(other) is int:
			raise Exception("Can only AND with constant (for now)")
		is_low_mask = (other & (other + 1) == 0)
		if not is_low_mask:
			raise Exception("AND can only be used to mask off low bits, for now")
		return self % (other + 1)
	
	def __getitem__(self, other):
		return BinaryOp("[]", ensure_expression(other+1).simplified(), self)

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
		self.lval = self.lval.simplified()
		self.rval = self.rval.simplified()
		if type(self.lval) is Literal and type(self.rval) is Literal:
			if self.op in ["+", "-", "+", "-", "%"] and type(self.lval.value) == type(self.rval.value):
				#print("simplifying")
				return Literal(eval(f"{self.lval.value!r} {self.op} {self.rval.value!r}"))
		
		# special case: chained addition
		# TODO: some nicer way to express this?
		# ((foo + a) + b)  =>  (foo + a+b)
		if self.op == "+" and type(self.rval) is Literal and type(self.lval) is BinaryOp and self.lval.op == "+" and type(self.lval.rval) is Literal:
			#print("simplifying")
			val = self.rval.value + self.lval.rval.value
			if val == 0:
				return self.lval.lval
			return BinaryOp("+", self.lval.lval, val)
		
		# ((foo - a) + b)  =>  (foo + b-a)
		if self.op == "+" and type(self.rval) is Literal and type(self.lval) is BinaryOp and self.lval.op == "-" and type(self.lval.rval) is Literal:
			#print("simplifying")
			val = self.rval.value - self.lval.rval.value
			if val == 0:
				return self.lval.lval
			return BinaryOp("+", self.lval.lval, val)

		return self


class UnaryOp(Expression):
	def __init__(self, op, value):
		self.op = op
		self.value = ensure_expression(value)

		if op == "!":
			self.type = "bool"
	
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

	def len(self):
		return UnaryOp("listlen", self)
	
	def index(self, other):
		return ListItemNum(self, other) - 1

	def __repr__(self):
		return f"ListVar({self.sprite.name}: {self.name})"
	
	def __getitem__(self, index):
		return ListIndex(self, (ensure_expression(index)+1).simplified())

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

class DaysSince2k(Expression):
	def __init__(self):
		pass

class MouseDown(Expression):
	type = "bool"
	def __init__(self):
		pass

class MouseX(Expression):
	def __init__(self):
		pass

class MouseY(Expression):
	def __init__(self):
		pass

class CostumeNumber(Expression):
	def __init__(self):
		pass

class Statement():
	def __init__(self, op, **args):
		self.op = op
		self.args = args
	
	def __repr__(self):
		return f"Statement({self.op}, {self.args!r})"

class IfStatement(Statement):
	def __init__(self, condition, then):
		super().__init__("control_if", CONDITION=ensure_expression(condition), SUBSTACK=then)
	
	def ELSE(self, do=None):
		if do is None:
			return getitem_hack(self.ELSE)
		return IfElseStatement(self.args["CONDITION"], self.args["SUBSTACK"], do)

class IfElseStatement(Statement):
	def __init__(self, condition, then, elsedo):
		super().__init__("control_if_else", CONDITION=ensure_expression(condition), SUBSTACK=then, SUBSTACK2=elsedo)

class Wait(Statement):
	def __init__(self, duration):
		super().__init__("control_wait", DURATION=ensure_expression(duration))

class AskAndWait(Statement):
	def __init__(self, prompt=""):
		self.op = "sensing_askandwait"
		self.prompt = ensure_expression(prompt)

class Answer(Expression):
	def __init__(self):
		pass

# MOTION

class SetXYPos(Statement):
	def __init__(self, x, y):
		super().__init__("motion_gotoxy",
			X=ensure_expression(x),
			Y=ensure_expression(y))

class ChangeXPos(Statement):
	def __init__(self, x):
		super().__init__("motion_changexby",
			DX=ensure_expression(x))

class SetXPos(Statement):
	def __init__(self, x):
		super().__init__("motion_setx",
			X=ensure_expression(x))

class ChangeYPos(Statement):
	def __init__(self, y):
		super().__init__("motion_changeyby",
			DY=ensure_expression(y))

class SetYPos(Statement):
	def __init__(self, y):
		super().__init__("motion_sety",
			Y=ensure_expression(y))

# END MOTION

# LOOKS

class Show(Statement):
	def __init__(self):
		self.op = "looks_show"

class Hide(Statement):
	def __init__(self):
		self.op = "looks_hide"

class SetEffect(Statement):
	def __init__(self, effect, value):
		super().__init__("looks_seteffectto",
			EFFECT=ensure_expression(effect),
			VALUE=ensure_expression(value))

class SetCostume(Statement):
	def __init__(self, costume):
		super().__init__("looks_switchcostumeto",
			COSTUME=ensure_expression(costume))

# END LOOKS

# PEN

class EraseAll(Statement):
	def __init__(self):
		self.op = "pen_clear"

class Stamp(Statement):
	def __init__(self):
		self.op = "pen_stamp"

class PenDown(Statement):
	def __init__(self):
		self.op = "pen_penDown"

class PenUp(Statement):
	def __init__(self):
		self.op = "pen_penUp"

# correct spellings only!
class SetPenColour(Statement):
	def __init__(self, colour):
		if type(colour) is int and colour < 0x1000000:
			colour = LiteralColour(f"#{colour:06x}")
		elif type(colour) is not LiteralColour:
			colour = ensure_expression(colour)+0 # TODO: only add zero if it's not an expression to begin with
		super().__init__("pen_setPenColorToColor", COLOR=colour)

def RGBA(r, g, b, a):
	return r << 16 | g << 8 | b | a << 24

def RGB(r, g, b):
	return RGBA(r, g, b, 0)

class SetPenSize(Statement):
	def __init__(self, size):
		super().__init__("pen_setPenSizeTo", SIZE=ensure_expression(size))

 # END PEN


class ProcDef(Statement):
	def __init__(self, proto):
		self.op = "procedures_definition"
		self.proto = proto
	
	def __call__(self, *args):
		if len(args) != len(self.proto.vars):
			raise Exception(f"{self!r} expects {len(self.proto.vars)} args, {len(args)} given")
		
		return ProcCall(self.proto, args)
	
	def __getattr__(self, attr):
		varname = self.proto.fmt + ":" + attr
		return self.proto.sprite.new_var(varname)

	def __repr__(self):
		return f"ProcDef({self.proto!r})"

class ProcProto(Statement):
	def __init__(self, sprite, fmt, uid, turbo=True):
		self.op = "procedures_prototype"
		self.sprite = sprite
		self.uid = uid
		self.fmt = fmt
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
	def __init__(self, proc, args, turbo=True):
		self.proc = proc
		args = list(map(ensure_expression, args))

		for arg, argtype in zip(args, proc.argtypes):
			if argtype == "bool" and arg.type != "bool":
				raise Exception("Cannot pass non-boolean expression to boolean proc arg")
		
		super().__init__("procedures_call", PROC=proc.uid, ARGS=args)


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


# user-facing API

def on_flag(substack=None):
	return [Statement("event_whenflagclicked")] + substack


def on_press(key, substack=None):
	# TODO: use enum for key, check the argument is actually an enum field
	return [Statement("event_whenkeypressed", KEY_OPTION=str(key))] + substack


def forever(do=None):
	if do is None:
		return getitem_hack(forever)
	return Statement("control_forever", SUBSTACK=do)


def repeatn(times, body=None):
	if body is None:
		return getitem_hack(repeatn, times)
	return Statement("control_repeat", TIMES=ensure_expression(times), SUBSTACK=body)

def repeatuntil(cond, body=None):
	if body is None:
		return getitem_hack(repeatuntil, cond)
	return Statement("control_repeat_until", CONDITION=ensure_expression(cond), SUBSTACK=body)

def getitem_hack(fn, *args):
	class GetitemHack():
		def __init__(self, *args):
			self.args = args
		
		def __getitem__(self, then):
			if type(then) != tuple:
				then = [then]
			return fn(*self.args, list(then))
	
	return GetitemHack(*args)

def IF(condition, then=None):
	if then is None:
		return getitem_hack(IF, condition)
	return IfStatement(condition, then)


def pickrandom(a, b):
	return BinaryOp("random", a, b)

# sugar (turns out it's not so easy to seperate sugar from core AST...)

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

def sumchain(arr):
	result = arr[0]
	for i in arr[1:]:
		result += i
	return result

millis_now = DaysSince2k() * 86400000



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
