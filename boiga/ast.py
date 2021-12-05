import math


def _ensure_expression(value):
	if issubclass(type(value), Expression):
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


class BinaryOp(Expression):
	def __init__(self, op, lval, rval):
		self.op = op
		self.lval = _ensure_expression(lval)
		self.rval = _ensure_expression(rval)

		if op in [">", "<", "==", "&&", "||"]:
			self.type = "bool"
	
	def __repr__(self):
		#return f"BinaryOp({self.op!r}, {self.lval!r}, {self.rval!r})"
		return f"({self.lval!r} {self.op} {self.rval!r})"
	
	def simplified(self):
		self.lval = self.lval.simplified()
		self.rval = self.rval.simplified()
		if type(self.lval) is Literal and type(self.rval) is Literal:
			if self.op in ["+", "-", "+", "-", "%"] and type(self.lval.value) == type(self.rval.value):
				return Literal(eval(f"{self.lval.value!r} {self.op} {self.rval.value!r}"))
		return self


class UnaryOp(Expression):
	def __init__(self, op, value):
		self.op = op
		self.value = _ensure_expression(value)

		if op == "!":
			self.type = "bool"
	
	def __repr__(self):
		return f"{self.op}({self.value!r})"


class Var(Expression):
	def __init__(self, sprite, name, uid):
		self.sprite = sprite
		self.name = name
		self.uid = uid
	
	def __le__(self, other):
		other = _ensure_expression(other)

		# If other is (self+x) or (x+self), optimise to "change by"
		if type(other) is BinaryOp and other.op == "+":
			if other.lval == self:
				return Statement("data_changevariableby", VARIABLE=self, VALUE=other.rval)
			elif other.rval == self:
				return Statement("data_changevariableby", VARIABLE=self, VALUE=other.lval)
		
		return Statement("data_setvariableto", VARIABLE=self, VALUE=other)
	
	def __getitem__(self, _slice):
		if type(_slice) is not slice:
			raise Exception("You can't index a non-list variable")
		return VarRangeIterationHack(self, range(_slice.start, _slice.stop, _slice.step))

	def changeby(self, other):
		return Statement("data_changevariableby", VARIABLE=self, VALUE=_ensure_expression(other))

	def __repr__(self):
		return f"Var({self.sprite.name}: {self.name})"

class VarRangeIterationHack():
	def __init__(self, var, range):
		self.var = var
		self.range = range
	
	def __rshift__(self, values):
		return varloop(self.var, self.range, values)

class List(Expression):
	def __init__(self, sprite, name, uid):
		self.sprite = sprite
		self.name = name
		self.uid = uid
	
	def __repr__(self):
		return f"Var({self.sprite.name}: {self.name})"
	
	def __getitem__(self, index):
		return ListIndex(self, index)


class ListIndex(Expression):
	def __init__(self, list_, index):
		self.list = list_
		self.index = _ensure_expression(index)
	
	def __le__(self, other):
		other = _ensure_expression(other)
		return Statement("data_replaceitemoflist", LIST=self.list, INDEX=(self.index+1).simplified(), ITEM=other)
	
	def __repr__(self):
		return f"{self.list!r}[{self.index!r}]"




class Statement():
	def __init__(self, op, **args):
		self.op = op
		self.args = args

class IfStatement(Statement):
	def __init__(self, condition, then):
		super().__init__("control_if", CONDITION=_ensure_expression(condition), SUBSTACK=then)
	
	def ELSE(self, do):
		return IfElseStatement(self.args["CONDITION"], self.args["SUBSTACK"], do)

class IfElseStatement(Statement):
	def __init__(self, condition, then, elsedo):
		super().__init__("control_if_else", CONDITION=_ensure_expression(condition), SUBSTACK=then, SUBSTACK2=elsedo)

class ProcDef(Statement):
	def __init__(self, proto):
		self.op = "procedures_definition"
		self.proto = proto
	
	def __call__(self, *args):
		if len(args) != len(self.proto.vars):
			raise Exception(f"{self!r} expects {len(self.proto.vars)} args, {len(args)} given")
		
		return ProcCall(self.proto, args)
	
	def __repr__(self):
		return f"ProcDef({self.proto!r})"

class ProcProto(Statement):
	def __init__(self, sprite, fmt, uid):
		self.op = "procedures_prototype"
		self.sprite = sprite
		self.uid = uid
		self.fmt = fmt

		# quick and dirty parser state machine
		# [square] brackets denote numeric/string args, <triangle> brackets denote bool args
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
	def __init__(self, proc, args):
		self.proc = proc
		args = list(map(_ensure_expression, args))

		for arg, argtype in zip(args, proc.argtypes):
			if argtype == "bool" and arg.type != "bool":
				raise Exception("Cannot pass non-boolean expression to boolean proc arg")
		
		super().__init__("procedures_call", PROC=proc.uid, ARGS=args)


class ProcVar(Expression):
	def __init__(self, sprite, procproto, name, uid):
		self.sprite = sprite
		self.procproto = procproto
		self.name = name
		self.uid = uid
	
	def __repr__(self):
		return f"ProcVar({self.procproto.fmt!r}: {self.name})"

class ProcVarBool(Expression):
	def __init__(self, sprite, procproto, name, uid):
		self.type = "bool"
		self.sprite = sprite
		self.procproto = procproto
		self.name = name
		self.uid = uid
	
	def __repr__(self):
		return f"ProcVarBool({self.procproto.fmt!r}: {self.name})"

# user-facing API

def on_flag(substack):
	return [Statement("event_whenflagclicked")] + substack


def forever(do):
	return Statement("control_forever", SUBSTACK=do)


def repeatn(times, body):
	return Statement("control_repeat", TIMES=_ensure_expression(times), SUBSTACK=body)


def IF(condition, then):
	return IfStatement(condition, then)

# sugar

def varloop(var, _range, body): return [
	var <= _range.start,
	repeatn(len(_range),
		body + 
		[ var <= var + _range.step ]
	)
]






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