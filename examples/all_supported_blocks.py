from math import floor, ceil
from numpy import broadcast
from boiga import *

project = Project()

cat = project.new_sprite("Scratch Cat")
cat.add_costume("scratchcat", "examples/assets/scratchcat.svg", center=(48, 50))

a = cat.new_var("a")
b = cat.new_var("b")
c = cat.new_var("c")

mylist = cat.new_list("mylist")

cat.on_receive("hello", [
	Say("ok"),
])

@cat.proc_def()
def my_custom_block(locals, a, b, c: bool): return [
	If (c) [
		locals.result <= a + b
	]
]

cat.on_flag([
	# ================= MOTION ====================

	#MoveSteps(10),
	#TurnDegreesCW(15),
	#TurnDegreesCCW(15),

	#GoTo(Position.Random),
	#GoTo(Position.Mouse),
	SetXYPos(0, 0),
	#GlideTo(),
	#GlideToXYPos(),

	#PointInDirection(),
	#PointTowards(),

	ChangeXPos(10),
	SetXPos(0),
	ChangeYPos(10),
	SetYPos(0),

	#IfOnEdgeBounce(),

	#SetRotationStyle(),

	Say(GetXPos()),
	Say(GetYPos()),
	Say(GetDirection()),


	# ================= LOOKS ====================

	#SayForDuration("Hello", 1),
	Say("Hello!"),
	#ThinkForDuration("Hmm...", 1),
	#Think("Hmm..."),

	SetCostume("scratchcat"),
	#NextCostume(),
	#SetBackdrop(),
	#NextBackdrop(),

	#ChangeSizeBy(),
	SetSize(100),

	ChangeEffect(Effects.Color, 25),
	SetEffect(Effects.Color, 0),
	#ClearEffects(),

	Hide(),
	Show(),

	#GoToLayer(),
	#GoForwardsLayers(),
	#GoBackwardsLayers(),

	Say(CostumeNumber()),
	#CostumeName(),
	#BackdropNumber(),
	#BackdropName(),

	#GetSize(),


	# ================= SOUNDS ====================

	#PlaySoundUntilDone(),
	#StartSound(),
	#StopAllSounds(),

	#ChangeSoundEffect(),
	#SetSoundEffect(),
	#ClearSoundEffects(),

	#ChangeVolumeBy(),
	#SetVolumeTo(),

	#GetVolume(),


	# ================= EVENTS ====================

	BroadcastAndWait("hello"),
	#Broadcast("hello"),


	# ================= CONTROL ====================

	Wait(1),

	Repeat (10) [
		Say("foo"), # TODO: allow empty body?
	],

	If (Literal(1) == 2) [
		Forever [
			Say("foo"), # TODO: allow empty body?
		],
	],

	If (Literal(1) == 1) [
		Say("foo"), # TODO: allow empty body?
	].Else [
		Say("bar"), # TODO: allow empty body?
	],

	#WaitUntil(Literal(1) == 1),

	RepeatUntil (Literal(1) == 1) [
		Say("foo"), # TODO: allow empty body?
	],

	#StopAll(),
	#StopThisScript(),
	#StopOtherScriptsInSprite(),

	#CreateClone(),
	#DeleteThisClone(),


	# ================= SENSING ====================

	Say(Touching("edge")),
	Say(TouchingColour(LiteralColour("#FF0000"))),
	#Say(ColourTouchingColour(LiteralColour("#0000FF"), LiteralColour("#FF0000")))
	#Say(DistanceTo()),

	AskAndWait("What's the answer?"),
	Say(Answer()),

	#Say(KeyPressed("a")),
	Say(MouseDown()),
	Say(MouseX()),
	Say(MouseY()),

	#SetDragMode(DragMode.DRAGGABLE),

	#Say(Loudness()),

	#Say(Timer()),
	#ResetTimer(),

	#GetProperty("backdrop #", "Stage");

	#GetCurrent("year"),

	Say(DaysSince2k()),

	#Say(Username()),


	# ================= OPERATORS ====================

	Say(a + b),
	Say(a - b),
	Say(a * b),
	Say(a / b),

	Say(pickrandom(1, 10)),

	Say(a > b),
	Say(a < b),
	Say(a == b),
	Say((a == a).AND(b == b)),
	Say((a == a).OR(b == b)),
	Say((a == a).NOT()),

	Say(Literal("apple").join("banana")),
	Say(Literal("apple")[0]),
	Say(Literal("apple").item(1)),  #  1-index alternative to the above
	Say(Literal("apple").len()),
	#Say(Literal("apple").contains("a")),

	Say(a % b),
	Say(round(a)),

	Say(abs(a)),
	Say(floor(a)),
	Say(ceil(a)),
	Say(a.sqrt()),
	Say(a.sin()),
	Say(a.cos()),
	#Say(a.tan()),
	#Say(a.asin()),
	#Say(a.acos()),
	Say(a.atan()),
	Say(a.log()),
	Say(a.log10()),
	Say(a ** b),


	# ================= VARIABLES ====================

	a <= 1,
	a.changeby(1),
	#a.show(),
	#a.hide(),

	mylist.append("thing"),

	mylist.delete_at(0),
	mylist.delete_at1(1), #  1-index alternative to the above

	mylist.delete_all(),

	#mylist.insert_at(0, "thing"),
	#mylist.insert_at1(1, "thing"), #  1-index alternative to the above

	mylist[0] <= "thing",
	mylist.item(1) <= "thing", #  1-index alternative to the above

	Say(mylist[0]),
	Say(mylist.item(1)), #  1-index alternative to the above

	Say(mylist.index("thing")),
	Say(mylist.index1("thing")), #  1-index alternative to the above

	#Say(mylist.contains("thing")),

	#mylist.show(),
	#mylist.hide(),


	# ================= CUSTOM BLOCKS ====================

	my_custom_block(a, b, a == a),
	my_custom_block(a, b, a == a).inline(),


	# ================= MUSIC ====================

	PlayDrum(Drums.SnareDrum, 0.25),
	RestFor(0.25),
	PlayNote(60, 0.25),
	SetInstrument(Instruments.Piano),
	SetTempo(60),
	ChangeTempoBy(10),
	Say(GetTempo()),


	# ================= PEN ====================

	EraseAll(),
	Stamp(),
	PenDown(),
	PenUp(),
	SetPenColour(LiteralColour("#ff0000")),
	#ChangePenEffect("color", 10),
	SetPenParam("color", 10),
	#ChangePenSizeBy(1),
	SetPenSize(10),
])


cat.on_press("a", [
	Say("a"),
])

project.save("examples/out/Boiga Examples: All Blocks.sb3")
