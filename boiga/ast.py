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

class GetXPos(core.Expression):
	def __init__(self):
		pass

class GetYPos(core.Expression):
	def __init__(self):
		pass

class GetDirection(core.Expression):
	def __init__(self):
		pass

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

class Effects:
	Color = "color"
	Fisheye = "fisheye"
	Whirl = "whirl"
	Pixelate = "pixelate"
	Mosaic = "mosaic"
	Brightness = "brightness"
	Ghost = "ghost"

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

def StopAll():
	return core.Statement("control_stop", STOP_OPTION="all")

def StopThisScript():
	return core.Statement("control_stop", STOP_OPTION="this script")

def StopOtherScriptsInSprite():
	return core.Statement("control_stop", STOP_OPTION="other scripts in sprite")

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

# BEGIN MUSIC

class Instruments:
	Piano = core.Instrument(1)
	ElectricPiano = core.Instrument(2)
	Organ = core.Instrument(3)
	Guitar = core.Instrument(4)
	ElectricGuitar = core.Instrument(5)
	Bass = core.Instrument(6)
	Pizzicato = core.Instrument(7)
	Cello = core.Instrument(8)
	Trombone = core.Instrument(9)
	Clarinet = core.Instrument(10)
	Saxophone = core.Instrument(11)
	Flute = core.Instrument(12)
	WoodenFlute = core.Instrument(13)
	Bassoon = core.Instrument(14)
	Choir = core.Instrument(15)
	Vibraphone = core.Instrument(16)
	MusicBox = core.Instrument(17)
	SteelDrum = core.Instrument(18)
	Marimba = core.Instrument(19)
	SynthLead = core.Instrument(20)
	SynthPad = core.Instrument(21)

class Drums:
	SnareDrum = core.Drum(1)
	BassDrum = core.Drum(2)
	SideStick = core.Drum(3)
	CrashCymbal = core.Drum(4)
	OpenHiHat = core.Drum(5)
	ClosedHiHat = core.Drum(6)
	Tambourine = core.Drum(7)
	HandClap = core.Drum(8)
	Claves = core.Drum(9)
	WoodBlock = core.Drum(10)
	Cowbell = core.Drum(11)
	Triangle = core.Drum(12)
	Bongo = core.Drum(13)
	Conga = core.Drum(14)
	Cabasa = core.Drum(15)
	Guiro = core.Drum(16)
	Vibraslap = core.Drum(17)
	Cuica = core.Drum(18)

class SetInstrument(core.Statement):
	def __init__(self, instrument):
		if not core.is_expression(instrument):
			instrument = ensure_expression(instrument).join("")
		super().__init__("music_setInstrument", INSTRUMENT=instrument)

class SetTempo(core.Statement):
	def __init__(self, tempo):
		super().__init__("music_setTempo", TEMPO=ensure_expression(tempo))

class ChangeTempoBy(core.Statement):
	def __init__(self, tempo):
		super().__init__("music_changeTempo", TEMPO=ensure_expression(tempo))

class GetTempo(core.Expression):
	def __init__(self):
		pass

class PlayNote(core.Statement):
	def __init__(self, note, beats):
		super().__init__("music_playNoteForBeats", NOTE=ensure_expression(note), BEATS=ensure_expression(beats))

class PlayDrum(core.Statement):
	def __init__(self, drum, beats):
		if not core.is_expression(drum):
			drum = ensure_expression(drum).join("")
		super().__init__("music_playDrumForBeats", DRUM=drum, BEATS=ensure_expression(beats))

class RestFor(core.Statement):
	def __init__(self, beats):
		super().__init__("music_restForBeats", BEATS=ensure_expression(beats))

# END MUSIC

# misc helpers

def sumchain(arr):
	result = arr[0]
	for i in arr[1:]:
		result += i
	return result

millis_now = DaysSince2k() * 86400000

def nop(*args):
	return []
