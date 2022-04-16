import math
from . import ast_core as core
from .ast_core import repeatn, repeatuntil, ensure_expression, Literal, LiteralColour

# MOTION

class SetXYPos(core.Statement):
	def __init__(self, x, y):
		super().__init__("motion_gotoxy",
			X=ensure_expression(x),
			Y=ensure_expression(y))

class ChangeXPos(core.Statement):
	def __init__(self, x):
		super().__init__("motion_changexby",
			DX=ensure_expression(x))

class SetXPos(core.Statement):
	def __init__(self, x):
		super().__init__("motion_setx",
			X=ensure_expression(x))

class ChangeYPos(core.Statement):
	def __init__(self, y):
		super().__init__("motion_changeyby",
			DY=ensure_expression(y))

class SetYPos(core.Statement):
	def __init__(self, y):
		super().__init__("motion_sety",
			Y=ensure_expression(y))

# END MOTION

# LOOKS

class Show(core.Statement):
	def __init__(self):
		self.op = "looks_show"

class Hide(core.Statement):
	def __init__(self):
		self.op = "looks_hide"

class SetEffect(core.Statement):
	def __init__(self, effect, value):
		super().__init__("looks_seteffectto",
			EFFECT=ensure_expression(effect),
			VALUE=ensure_expression(value))

class SetCostume(core.Statement):
	def __init__(self, costume):
		super().__init__("looks_switchcostumeto",
			COSTUME=ensure_expression(costume))

# END LOOKS

# BEGIN SOUND

# END SOUND

# EVENTS

def on_flag(substack=None):
	return [core.Statement("event_whenflagclicked")] + substack


def on_press(key, substack=None):
	# TODO: use enum for key, check the argument is actually an enum field
	return [core.Statement("event_whenkeypressed", KEY_OPTION=str(key))] + substack

# END EVENTS

# BEGIN CONTROL

class Wait(core.Statement):
	def __init__(self, duration):
		super().__init__("control_wait", DURATION=ensure_expression(duration))

def forever(do=None):
	if do is None:
		return core.getitem_hack(forever)
	return core.Statement("control_forever", SUBSTACK=do)

def IF(condition, then=None):
	if then is None:
		return core.getitem_hack(IF, condition)
	return core.IfStatement(condition, then)

# END CONTROL

# BEGIN SENSING

class DaysSince2k(core.Expression):
	def __init__(self):
		pass

class MouseDown(core.Expression):
	type = "bool"
	def __init__(self):
		pass

class MouseX(core.Expression):
	def __init__(self):
		pass

class MouseY(core.Expression):
	def __init__(self):
		pass

class CostumeNumber(core.Expression):
	def __init__(self):
		pass

class AskAndWait(core.Statement):
	def __init__(self, prompt=""):
		self.op = "sensing_askandwait"
		self.prompt = ensure_expression(prompt)

class Answer(core.Expression):
	def __init__(self):
		pass

# END SENSING

# BEGIN OPERATORS

def pickrandom(a, b):
	return core.BinaryOp("random", a, b)

# END OPERATORS

# BEGIN PEN

class EraseAll(core.Statement):
	def __init__(self):
		self.op = "pen_clear"

class Stamp(core.Statement):
	def __init__(self):
		self.op = "pen_stamp"

class PenDown(core.Statement):
	def __init__(self):
		self.op = "pen_penDown"

class PenUp(core.Statement):
	def __init__(self):
		self.op = "pen_penUp"

# correct spellings only!
class SetPenColour(core.Statement):
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

class SetPenSize(core.Statement):
	def __init__(self, size):
		super().__init__("pen_setPenSizeTo", SIZE=ensure_expression(size))

 # END PEN

# misc helpers

def sumchain(arr):
	result = arr[0]
	for i in arr[1:]:
		result += i
	return result

millis_now = DaysSince2k() * 86400000
