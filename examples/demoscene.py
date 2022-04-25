from random import randint
from PIL import Image
import io

from boiga import *

project = Project()

project.stage.add_costume("black", b"""\
<svg xmlns="http://www.w3.org/2000/svg">
    <rect x="-240" y="-180" width="480" height="360" fill="#000" />
</svg>\
""", "svg")

main = project.new_sprite("Main")

main.add_costume("black", b"""\
<svg xmlns="http://www.w3.org/2000/svg">
    <rect x="-240" y="-180" width="480" height="360" fill="#000" />
</svg>\
""", "svg")

for codepoint in range(0x20, 0x7f):
	main.add_costume(f"IBM_{chr(codepoint)}", f"examples/assets/IBM_{codepoint}.png")

px_on = Image.open("examples/assets/scanline_on.png")
px_off = Image.open("examples/assets/scanline_off.png")
NBITS = 8
PXSZ = 3
for i in range(0, 1<<NBITS):
	#im = Image.new("RGB", (NBITS*PXSZ, 1*PXSZ), (10, 10, 10))
	im = Image.new("RGBA", (NBITS, 1), (10, 10, 10, 0))
	for bit in range(NBITS):
		if (i>>bit)&1 :
			im.putpixel((bit, 0), (40, 140, 40, 40))
			#im.paste(px_on, (bit*PXSZ, 0))
		else:
			im.putpixel((bit, 0), (10, 10, 10, 40))
			#im.paste(px_off, (bit*PXSZ, 0))

	buf = io.BytesIO()
	#im = im.resize((NBITS*2*PXSZ, 1*2*PXSZ), Image.NEAREST)
	im.save(buf, format="PNG")
	main.add_costume(f"BITS_{i:0{NBITS}b}", buf.getvalue(), "png")
	

CHAINLEN = 40
LINKLEN = 40
HISTLEN = 35
DECAY = 0.88
XOFFSET = 150
YOFFSET = 100
xpoints = main.new_list("xpoints", [XOFFSET]*CHAINLEN)
ypoints = main.new_list("ypoints", [YOFFSET]*CHAINLEN)
xhist = main.new_list("xhist", [XOFFSET]*CHAINLEN*HISTLEN)
yhist = main.new_list("yhist", [YOFFSET]*CHAINLEN*HISTLEN)

framectr = main.new_var("framectr", 0)
f0 = main.new_var("f0")
framestart = main.new_var("framestart")
lasthistupdate = main.new_var("lasthistupdate")
lastrainupdate = main.new_var("lastrainupdate")
dt = main.new_var("dt")

def coefscale(n, coef, offset):
	return (n-offset)*coef+offset

@main.proc_def()
def render(locals):
	coef = locals.coef
	i = locals.i
	histi = locals.histi
	initcoef = locals.initcoef

	def setcolour():
		return SetPenColour(RGBA(0, ((Literal(1)-coef)*0xff).__floor__(), ((Literal(1)-coef)*0x60).__floor__(), (coef * 0xff).__floor__() ))

	return [
	#EraseAll(),
	SetCostume("black"),
	SetEffect("ghost", 30),
	SetXYPos(0,0),
	Stamp(),
	SetPenSize(1),
	SetPenColour(RGBA(0x00, 0xd0, 0x00, 0x40)),
	
	initcoef <= 1.0,
	Repeat (Literal(4)-(framectr-lasthistupdate)) [
		initcoef <= initcoef * DECAY**0.5,
	],

	coef <= initcoef,
	histi[:CHAINLEN*HISTLEN:CHAINLEN] >> [
		setcolour(),
		SetXYPos(
			coefscale(xhist[histi], coef, XOFFSET),
			coefscale(yhist[histi], coef, YOFFSET)
		),
		PenDown(),
		i[1:CHAINLEN] >> [
			SetXYPos(
				coefscale(xhist[histi + i], coef, XOFFSET),
				coefscale(yhist[histi + i], coef, YOFFSET)
			),
		],
		PenUp(),
		coef <= coef * DECAY
	],
	i[:CHAINLEN] >> [
		coef <= initcoef,
		SetXYPos(
			coefscale(xhist[i], coef, XOFFSET),
			coefscale(yhist[i], coef, YOFFSET),
		),
		coef <= coef * DECAY,
		PenDown(),
		histi[CHAINLEN:CHAINLEN*HISTLEN:CHAINLEN] >> [
			setcolour(),
			SetXYPos(
				coefscale(xhist[histi + i], coef, XOFFSET),
				coefscale(yhist[histi + i], coef, YOFFSET),
			),
			coef <= coef * DECAY
		],
		PenUp(),
	],
]

@main.proc_def()
def update_trail_physx(locals, t): return [
	locals.amplitude <= (t/-7).sin() * (t/5).sin() * 800,
	xpoints[0] <= (t/2).sin()*locals.amplitude + (t*2).sin() * 20,
	ypoints[0] <= (t/2).cos()*locals.amplitude + (t*2).cos() * 20,
	locals.i[1:CHAINLEN] >> [
		locals.dx <= xpoints[locals.i]-xpoints[locals.i-1],
		locals.dy <= ypoints[locals.i]-ypoints[locals.i-1],
		locals.dist <= (locals.dx*locals.dx+locals.dy*locals.dy).sqrt(),
		xpoints[locals.i] <= xpoints[locals.i-1] + locals.dx * (Literal(LINKLEN)/locals.dist),
		ypoints[locals.i] <= ypoints[locals.i-1] + locals.dy * (Literal(LINKLEN)/locals.dist),
	],
]

@main.proc_def()
def update_trail_hist(locals, spicefactor): return [
	locals.i[:CHAINLEN] >> [
		xhist.delete_at(0),
		yhist.delete_at(0),
		xhist.append(xpoints[locals.i] + pickrandom(-1, 1) * spicefactor),
		yhist.append(ypoints[locals.i] + pickrandom(-1, 1) * spicefactor),
	]
]

import random
rainy = main.new_var("rainy")
rain_msg = main.new_var("rain_msg", "")
rainoffset = main.new_list("rainoffset", [random.randint(0, 100) for _ in range(30)])
rainchars = "abcdefg$%!&<>:@\"*().,^"
@main.proc_def()
def render_matrix(locals, msg): return [
	SetSize(200),
	locals.i[:30] >> [
		SetEffect("brightness", 50),
		locals.j[:5] >> [
			SetEffect("ghost", locals.j*(100/5)),
			SetCostume(Literal("IBM_").join(Literal(rainchars)[pickrandom(0, len(rainchars)-1)])),
			locals.x <= locals.i*16-240,
			locals.y <= ((((rainy + rainoffset[locals.i] + locals.j)*24) % (360+24))-180),
			SetXYPos(locals.x, locals.y),
			If (((locals.x < Literal(-8)-(msg.len()*8)).OR(locals.x >  (msg.len()*8)-(16-8))).OR((locals.y < -16+24).OR(locals.y > 16+24))) [
				Stamp(),
			],
			SetEffect("brightness", 0),
		]
	],
	SetEffect("ghost", 0),
	SetEffect("brightness", 20),
	locals.i[:msg.len()] >> [
		SetXYPos((locals.i*16)-(msg.len()*8), 24),
		SetCostume(Literal("IBM_").join(msg[locals.i])),
		Stamp(),
	],
	SetEffect("brightness", 0),
	If (framectr - lastrainupdate > 1) [
		rainy.changeby(-0.5),
		lastrainupdate <= framectr,
	]
]

def typestring(locals, startctr, msg, ticks_per_char):
	msg = ensure_expression(msg)
	return [
		If ((framectr > startctr-1).AND(framectr < (msg.len()*ticks_per_char+startctr))) [
			rain_msg <= "",
			locals.i[:(framectr - startctr)//ticks_per_char+1] >> [
				rain_msg <= rain_msg.join(msg[locals.i]),
			]
		]
	]

@main.proc_def()
def update_matrix(locals): return [
	typestring(locals, 60*4, "Greetings, FieldFX 2022!", 4),
	typestring(locals, 60*10, "You are now entering...", 8),
	typestring(locals, 60*15, "THE MEOWTRIX", 4),
]

STEPSIZE = 10
@main.proc_def()
def update(locals):
	millis_start = locals.millis_start
	millis_prev = locals.millis_prev
	i = locals.i
	
	return [
	millis_start <= millis_now,
	i[:STEPSIZE] >> [
		update_trail_physx(millis_start + i/((millis_start-millis_prev)*STEPSIZE)),
	],
	If (framectr-lasthistupdate > 3) [
		update_trail_hist(((millis_start*0.5).sin()+1)*5),
		lasthistupdate <= framectr,
	],
	millis_prev <= millis_start,
]

logo = Image.open("examples/assets/scratchlogo.png").convert("L")
TEXW, TEXH = logo.size
tex = main.new_list("texture", list(logo.getdata()))

def calcpx(locals, value):
	for i in range(NBITS):
		value = value.join((tex[
			(((locals.rcos*(locals.px+locals.xstep*(NBITS-1-i)) - locals.rspy))%TEXW) + \
			(((locals.rsin*(locals.px+locals.xstep*(NBITS-1-i)) + locals.rcpy).__floor__())%TEXH)*TEXW # pickrandom(0, (locals.xstep-1)*locals.zoom*150)
		] > pickrandom(1, 254)) * 1)
	return value

@main.proc_def()
def render_rotozoom(locals, ticks): return [
	locals.starttime <= millis_now,
	If (locals.firstrun != "true") [
		EraseAll(),
		locals.tilt <= 0.0,
		locals.roto <= 0.0,
		locals.zoom <= 0.33,
		locals.camx <= 0.0,
		locals.velocity <= 0.0,
		locals.firstrun <= "true",
		locals.intro_done <= "false",
	],
	#SetXYPos(0, 0),
	#SetEffect("brightness", 0),
	#SetEffect("ghost", 90),
	#SetCostume("black"),
	#Stamp(),
	#SetCostume("IBM_A"),

	SetSize(200*PXSZ),
	SetEffect("ghost", 0),
	SetEffect("brightness", -30),
	SetXYPos(-240, 180-70),
	If (locals.intro_done == "true") [
		ChangeEffect("color", dt/15),
	].Else[
		If (ticks > 120) [
			locals.tilt <= (ticks-120)/100,
			If (locals.tilt > 1.0) [
				locals.tilt <= 1.0
			]
		],

		If (ticks > 240) [
			locals.velocity <= (ticks-240)/240,
			If (locals.velocity > 1.0) [
				locals.velocity <= 1.0,
				locals.intro_done <= "true"
			]
		],
	],

	If (ticks > 60*45) [
		Repeat (10) [
			locals.x <= pickrandom(0, tex.len()-50),
			tex[locals.x+locals.i] <= 255,
			locals.i[1:50] >> [
				tex[locals.x+locals.i] <= 0,
			]
		]
	],

	locals.roto.changeby((dt/(1000/60*2)) * locals.velocity),
	locals.zoom <= ((millis_now/25).sin()*locals.velocity+1.4)*0.30,
	locals.camx.changeby((dt/locals.zoom)*0.05*locals.velocity),

	locals.rsin <= locals.roto.sin() / locals.zoom,
	locals.rcos <= locals.roto.cos() / locals.zoom,
	locals.py <= -100,
	Repeat (220//PXSZ) [
		SetXPos(-240),
		locals.rspy <= locals.rsin*locals.py + locals.camx,
		locals.rcpy <= locals.rcos*locals.py + 60,
		locals.xstep <= locals.py*-0.006*locals.tilt+1,
		locals.px <= locals.xstep * -70,
		Repeat (480//(PXSZ*NBITS)) [
			SetCostume(calcpx(locals, Literal("BITS_"))),
			Stamp(),
			ChangeXPos(NBITS*PXSZ),
			locals.px.changeby(locals.xstep * NBITS)
		],
		ChangeYPos(-PXSZ),
		locals.py.changeby(locals.xstep*(Literal(1.0)+locals.tilt)),
		ChangeEffect("brightness", 0.7),
	],
]

ROTOZOOM_START = 60*20*0

main.on_flag([
	Hide(),
	rainy <= 0,
	#framectr <= 0,
	lasthistupdate <= 0,
	lastrainupdate <= 0,
	render_rotozoom.firstrun <= "false",
	rain_msg <= "",
	f0 <= millis_now,
	Forever [
		framectr <= ((millis_now-f0)/(1000/60)).__floor__(),
		dt <= millis_now - framestart,
		framestart <= millis_now,
		If (framectr < ROTOZOOM_START) [
			render(),
			render_matrix(rain_msg),
			update_matrix(),
			update(),
		].Else [
			render_rotozoom(framectr-ROTOZOOM_START),
		],
	]
])

project.save("examples/out/Boiga Examples: Demoscene.sb3")
