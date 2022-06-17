import math

from . import ast_core as core
from .ast_core import ensure_expression, Literal, LiteralColour

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

class SetCostume(core.Statement):
	def __init__(self, costume):
		if type(costume) is str:
			costume = core.Costume(costume)
		super().__init__("looks_switchcostumeto",
			COSTUME=costume)

class Say(core.Statement):
	def __init__(self, msg):
		super().__init__("looks_say",
			MESSAGE=ensure_expression(msg))

class SetEffect(core.Statement):
	def __init__(self, effect, value):
		super().__init__("looks_seteffectto",
			EFFECT=str(effect), # TODO: assert is str?
			VALUE=ensure_expression(value))

class ChangeEffect(core.Statement):
	def __init__(self, effect, change):
		super().__init__("looks_changeeffectby",
			EFFECT=str(effect), # TODO: assert is str?
			CHANGE=ensure_expression(change))

class SetSize(core.Statement):
	def __init__(self, size):
		super().__init__("looks_setsizeto",
			SIZE=ensure_expression(size))

class Show(core.Statement):
	def __init__(self):
		self.op = "looks_show"

class Hide(core.Statement):
	def __init__(self):
		self.op = "looks_hide"

# END LOOKS

# BEGIN SOUND

# END SOUND

# EVENTS

def on_flag(substack=None):
	return [core.Statement("event_whenflagclicked")] + substack

def on_receive(event, event_uid, substack=None):
	# TODO: use enum for key, check the argument is actually an enum field
	return [core.Statement("event_whenbroadcastreceived", BROADCAST_OPTION=[str(event), event_uid])] + substack

def on_press(key, substack=None):
	# TODO: use enum for key, check the argument is actually an enum field
	return [core.Statement("event_whenkeypressed", KEY_OPTION=str(key))] + substack

class BroadcastAndWait(core.Statement):
	def __init__(self, event):
		super().__init__("event_broadcastandwait", BROADCAST_INPUT=str(event))

# END EVENTS

# BEGIN CONTROL

class Wait(core.Statement):
	def __init__(self, duration):
		super().__init__("control_wait", DURATION=ensure_expression(duration))

Repeat = core.repeatn

class ForeverHack():
	def __getitem__(self, do):
		if type(do) != tuple:
			do = [do]
		return core.Statement("control_forever", SUBSTACK=list(do))
Forever = ForeverHack()

def If(condition, then=None):
	if then is None:
		return core.getitem_hack(If, condition)
	return core.IfStatement(condition, then)

RepeatUntil = core.repeatuntil

# END CONTROL

# BEGIN SENSING

class AskAndWait(core.Statement):
	def __init__(self, prompt=""):
		self.op = "sensing_askandwait"
		self.prompt = ensure_expression(prompt)

class Answer(core.Expression):
	def __init__(self):
		pass

class MouseDown(core.Expression):
	type = "bool"
	def __init__(self):
		pass

class Touching(core.Expression):
	type = "bool"
	def __init__(self, object):
		self.thing = core.TouchingObjectMenu(object)

class TouchingColour(core.Expression):
	type = "bool"
	def __init__(self, colour):
		self.colour = colour

class MouseX(core.Expression):
	def __init__(self):
		pass

class MouseY(core.Expression):
	def __init__(self):
		pass

class CostumeNumber(core.Expression):
	def __init__(self):
		pass

class DaysSince2k(core.Expression):
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


class SetPenParam(core.Statement):
	def __init__(self, param, value):
		super().__init__("pen_setPenColorParamTo", COLOR_PARAM=core.PenParamMenu(param), VALUE=ensure_expression(value))

def RGBA(r, g, b, a):
	return (ensure_expression(r) << 16) + \
		(ensure_expression(g) << 8) + \
		(ensure_expression(b)) + \
		(ensure_expression(a) << 24)

def RGB(r, g, b):
	return RGBA(r, g, b, 0)

class SetPenSize(core.Statement):
	def __init__(self, size):
		super().__init__("pen_setPenSizeTo", SIZE=ensure_expression(size))

# END PEN

# BEGIN MIDI

class SetInstrument(core.Statement):
	def __init__(self, instrument):
		super().__init__("music_setInstrument", INSTRUMENT=ensure_expression(instrument))
		
class GetInstrument(core.Expression):
	def __init__(self):
		pass
		
class SetInstrumentMIDI(core.Statement):
	def __init__(self, instrument):
		super().__init__("music_midiSetInstrument", INSTRUMENT=ensure_expression(instrument))
		
class SetTempo(core.Statement):
	def __init__(self, tempo):
		super().__init__("music_setTempo", TEMPO=ensure_expression(tempo))
		
class GetTempo(core.Expression):
	def __init__(self):
		pass

class PlayNote(core.Statement):
	def __init__(self, note, beats):
		super().__init__("music_playNoteForBeats", NOTE=ensure_expression(note), BEATS=ensure_expression(beats))
		
class PlayDrum(core.Statement):
	def __init__(self, drum, beats):
		super().__init__("music_playDrumForBeats", DRUM=ensure_expression(drum), BEATS=ensure_expression(beats))
		
class PlayDrumMIDI(core.Statement):
	def __init__(self, drum, beats):
		super().__init__("music_midiPlayDrumForBeats", DRUM=ensure_expression(drum), BEATS=ensure_expression(beats))

# END MIDI

# misc helpers

def sumchain(arr):
	result = arr[0]
	for i in arr[1:]:
		result += i
	return result

millis_now = DaysSince2k() * 86400000

def nop(*args):
	return []
