import math


def _ensure_expression(value):
	if issubclass(type(value), Expression):
		return value
	if type(value) in [str, int, float]:
		return Literal(value)
	raise Exception(f"Can't interpret {value!r} as Expression")


class Expression():
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
	
	#def __ne__(self, other):
	#	return BinaryOp("!=", self, other)
	
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
	
	def __repr__(self):
		return f"{self.op}({self.value!r})"


class Var(Expression):
	def __init__(self, sprite, name, uid):
		self.sprite = sprite
		self.name = name
		self.uid = uid
	
	def __le__(self, other):
		other = _ensure_expression(other)
		return Statement("data_setvariableto", VARIABLE=self, VALUE=other)
	
	def __repr__(self):
		return f"Var({self.sprite.name}: {self.name})"


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
		return Statement("data_replaceitemoflist", LIST=self.list, INDEX=self.index+1, ITEM=other)
	
	def __repr__(self):
		return f"{self.list!r}[{self.index!r}]"




class Statement():
	def __init__(self, op, **args):
		self.op = op
		self.args = args


def on_flag(substack):
	return [Statement("event_whenflagclicked")] + substack

def forever(do):
	return Statement("control_repeat", SUBSTACK=do)

def iff(condition, then, otherwise=[]):
	if not otherwise:
		return Statement("control_if", CONDITION=condition, SUBSTACK=then)
	else:
		assert(False) # TODO
		return Statement("control_ifelse") #XXX: is this the correct name?

if __name__ == "__main__":
	print(math.floor((Var("foo") + 7 + 3) * 5) == Literal(3) / 5)
	print(List("bar")[5])
	print(Literal(3) + 4)
	print(Literal(123) >> 2)
	print(Literal(1234123) & 0xFF)
	print(Literal(5) > 7)
	#List("foo")[5] = 123
