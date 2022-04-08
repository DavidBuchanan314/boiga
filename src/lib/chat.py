from boiga.codegen import Project
from boiga.ast import *

from .chacha20_csprng import CSPRNG
from .x25519 import X25519
from .utils import Utils


class Chat():
	def __init__(self, cat):
		overlay = cat.project.new_sprite("Overlay")
		overlay.add_costume(f"overlay", open(f"../assets/overlay.svg", "rb").read(), "svg")

		for codepoint in range(0x20, 0x7e):
			costume_data = open(f"../assets/IBM_{codepoint}.png", "rb").read()
			cat.add_costume(f"IBM_{chr(codepoint)}", costume_data, "png")

		chatlog = cat.new_list("chatlog", [])

		FONT_WIDTH = 9
		FONT_HEIGHT = 18

		#stdout = project.stage.new_list("stdout", [], monitor=[0, 0, 480-2, 292])

		@cat.proc_def("draw_text [message]")
		def draw_text(locals, message): return [
			locals.i[1:message.len()] >> [
				SetCostume(Literal("IBM_").join(message[locals.i])),
				Stamp(),
				ChangeXPos(FONT_WIDTH),
			]
		]

		MARGIN_LEFT = 64
		MARGIN_RIGHT = MARGIN_LEFT
		PADDING = 6
		SMALL_RADIUS = 6
		@cat.proc_def("draw_bubble_left [y] [width] [height]")
		def draw_bubble_left(locals, y, width, height): return [
			# BUBBLE OUTLINE
			SetPenColour(0x2D478F),
			SetPenSize(FONT_HEIGHT + PADDING*2),

			# outer rectangle
			SetXYPos(-240+MARGIN_LEFT, y - (height-1) * FONT_HEIGHT),
			PenDown(),
			ChangeXPos(width * FONT_WIDTH),
			SetYPos(y),
			ChangeXPos(width * -FONT_WIDTH),
			SetYPos(y - (height-1) * FONT_HEIGHT),

			# lower-left corner
			SetPenSize(SMALL_RADIUS),
			ChangeXPos(-PADDING-SMALL_RADIUS),
			ChangeYPos(-PADDING-SMALL_RADIUS),
			ChangeXPos(+PADDING+SMALL_RADIUS),

			# inner rectangle
			SetXYPos(-240+MARGIN_LEFT, y - (height-1) * FONT_HEIGHT),
			SetPenSize(FONT_HEIGHT + (PADDING-1)*2),
			SetPenColour(0x4D97FF),
			ChangeXPos(width * FONT_WIDTH),
			SetYPos(y),
			ChangeXPos(width * -FONT_WIDTH),
			SetYPos(y - (height-1) * FONT_HEIGHT),

			# inner lower-left corner
			SetPenSize(SMALL_RADIUS-2),
			ChangeXPos(-PADDING-SMALL_RADIUS),
			ChangeYPos(-PADDING-SMALL_RADIUS),
			ChangeXPos(+PADDING+SMALL_RADIUS),

			# fill-in
			PenUp(),
			SetPenSize(FONT_HEIGHT),
			locals.i[1:height-1] >> [
				SetXYPos(-240+MARGIN_LEFT, y - locals.i * FONT_HEIGHT),
				PenDown(),
				ChangeXPos(width * FONT_WIDTH),
				PenUp(),
			],
		]

		@cat.proc_def("draw_bubble_right [y] [width] [height]")
		def draw_bubble_right(locals, y, width, height): return [
			# BUBBLE OUTLINE
			SetPenColour(0x999999),
			SetPenSize(FONT_HEIGHT + PADDING*2),

			# outer rectangle
			SetXYPos(240 - MARGIN_RIGHT, y - (height-1) * FONT_HEIGHT),
			PenDown(),
			ChangeXPos(width * -FONT_WIDTH),
			SetYPos(y),
			ChangeXPos(width * FONT_WIDTH),
			SetYPos(y - (height-1) * FONT_HEIGHT),

			# lower-left corner
			SetPenSize(SMALL_RADIUS),
			ChangeXPos(+PADDING+SMALL_RADIUS),
			ChangeYPos(-PADDING-SMALL_RADIUS),
			ChangeXPos(-PADDING-SMALL_RADIUS),

			# inner rectangle
			SetXYPos(240 - MARGIN_LEFT, y - (height-1) * FONT_HEIGHT),
			SetPenSize(FONT_HEIGHT + (PADDING-1)*2),
			SetPenColour(0xe0e0e0),
			ChangeXPos(width * -FONT_WIDTH),
			SetYPos(y),
			ChangeXPos(width * FONT_WIDTH),
			SetYPos(y - (height-1) * FONT_HEIGHT),

			# inner lower-left corner
			SetPenSize(SMALL_RADIUS-2),
			ChangeXPos(+PADDING+SMALL_RADIUS),
			ChangeYPos(-PADDING-SMALL_RADIUS),
			ChangeXPos(-PADDING-SMALL_RADIUS),

			# fill-in
			PenUp(),
			SetPenSize(FONT_HEIGHT),
			locals.i[1:height-1] >> [
				SetXYPos(240 - MARGIN_LEFT, y - locals.i * FONT_HEIGHT),
				PenDown(),
				ChangeXPos(width * -FONT_WIDTH),
				PenUp(),
			],
		]

		@cat.proc_def("render [scrolly]")
		def render(locals, scrolly): return [
			EraseAll(),

			locals.i <= math.floor(scrolly/-FONT_HEIGHT) - 1,

			IF (locals.i < 1) [
				locals.i <= 1
			],

			# scan upwards until first ""
			repeatuntil (chatlog[locals.i] == Literal("")) [
				locals.i.changeby(-1)
			],

			repeatuntil ((locals.i > chatlog.len()-1).OR( locals.i > (math.floor((scrolly-360)/-FONT_HEIGHT) - 5) )) [
				# find bubble height
				locals.i.changeby(1),
				locals.thisheight <= 0,
				locals.longestline <= 2,
				repeatuntil (chatlog[locals.i] == Literal("")) [
					IF (chatlog[locals.i].len() > locals.longestline) [
						locals.longestline <= chatlog[locals.i].len()
					],
					locals.thisheight.changeby(1),
					locals.i.changeby(1)
				],

				locals.i <= locals.i - locals.thisheight,
				IF (chatlog[locals.i][0] == ">") [
					draw_bubble_left(Literal(150) - ((locals.i-1) * FONT_HEIGHT) - scrolly, locals.longestline-2, locals.thisheight),

					repeatn (locals.thisheight) [
						SetXYPos(-240+MARGIN_LEFT - 4, Literal(150 + 7) - ((locals.i-1) * FONT_HEIGHT) - scrolly),
						draw_text(chatlog[locals.i]),
						locals.i.changeby(1)
					],
				],
				IF (chatlog[locals.i][0] == "<") [
					draw_bubble_right(Literal(150) - ((locals.i-1) * FONT_HEIGHT) - scrolly, locals.longestline-2, locals.thisheight),

					repeatn (locals.thisheight) [
						SetXYPos(Literal(240-MARGIN_LEFT - 4 + FONT_WIDTH*2) - chatlog[locals.i].len() * FONT_WIDTH, Literal(150 + 7) - ((locals.i-1) * FONT_HEIGHT) - scrolly),
						draw_text(chatlog[locals.i]),
						locals.i.changeby(1)
					],
				],

			]

		]

		velocity = cat.new_var("velocity")
		scrollpos = cat.new_var("scrollpos")
		scrolltarget = cat.new_var("scrolltarget")

		ACCEL = 0.3
		DAMPING = 0.6
		MIN_SCROLL = -10

		def get_max_scroll():
			return chatlog.len() * FONT_HEIGHT - 260


		@cat.proc_def("gui_loop", turbo=False)
		def gui_loop(locals): return [
			forever([

				# mouse drag scrolling
				IF (MouseDown()) [
					IF (locals.prevmouse == "true", [
						scrollpos <= locals.prevscrollpos + (MouseY() - locals.prevmousey),
						scrolltarget <= scrollpos
					]).ELSE([
						locals.prevscrollpos <= scrollpos,
						locals.prevmousey <= MouseY()
					]),
				],
				locals.prevmouse <= MouseDown(),

				# fancy bounce effect when scroll limits hit
				locals.max_scroll <= get_max_scroll(),
				IF (locals.max_scroll < MIN_SCROLL) [
					locals.max_scroll <= MIN_SCROLL
				],
				IF (scrolltarget < MIN_SCROLL) [
					IF (MouseDown(), [
						scrollpos <= (scrollpos - MIN_SCROLL) * 0.3 + MIN_SCROLL,
						scrolltarget <= scrollpos
					]).ELSE([
						scrolltarget <= MIN_SCROLL
					]),
				],
				IF (scrolltarget > locals.max_scroll) [
					IF (MouseDown(), [
						scrollpos <= (scrollpos - locals.max_scroll) * 0.3 + locals.max_scroll,
						scrolltarget <= scrollpos
					]).ELSE([
						scrolltarget <= locals.max_scroll
					]),
				],

				# update velocity physics
				velocity <= (velocity + (scrolltarget - scrollpos) * ACCEL) * DAMPING,
				scrollpos <= scrollpos + velocity,
				IF ((velocity < 0.01).AND(abs(scrolltarget - scrollpos) < 1)) [
					velocity <= 0,
					scrollpos <= scrolltarget
				],

				# actually render
				render(Literal(0)-math.floor(scrollpos)),
			])
		]

		cat.on_press("up arrow", [
			scrollpos.changeby(-15),
			scrolltarget <= scrollpos,
			velocity <= 0
		])

		cat.on_press("down arrow", [
			scrollpos.changeby(15),
			scrolltarget <= scrollpos,
			velocity <= 0
		])

		@cat.proc_def("new_message [sender] [message]")
		def new_message(locals, sender, message): return [
			locals.word <= "",
			locals.line <= "",
			locals.i <= 0,
			locals.firstspace <= "true",
			chatlog.append(""),

			repeatn (message.len()+1) [
				IF ((locals.i == message.len()).OR(message[locals.i] == " ").OR(message[locals.i] == "¶"), [ # end of a word
					IF ((locals.line.len() + locals.word.len()) < 32, [ # we can add the word to the current line
						IF (locals.firstspace == "true", [
							locals.line <= locals.word,
							locals.firstspace <= "false",
						]).ELSE([
							locals.line <= locals.line.join(" ").join(locals.word),
						])
					]).ELSE([ # start a new line
						#chatlog.append(sender.join(locals.line)),
						#locals.line <= "",
						IF (locals.word.len() > 32, [
							IF (locals.firstspace == "false") [
								locals.word <= Literal(" ").join(locals.word),
							],
							locals.j[:locals.word.len()] >> [
								IF (locals.line.len() > 31) [
									chatlog.append(sender.join(locals.line)),
									locals.line <= "",
								],
								locals.line <= locals.line.join(locals.word[locals.j]),
							],
						]).ELSE([
							chatlog.append(sender.join(locals.line)),
							locals.line <= locals.word
						]),
					]),
					IF (message[locals.i] == "¶") [
						chatlog.append(sender.join(locals.line)),
						locals.line <= "",
						locals.firstspace <= "true",
					],
					locals.word <= ""
				]).ELSE([ # keep building the current word
					locals.word <= locals.word.join(message[locals.i])
				]),

				locals.i.changeby(1)
			],

			IF (locals.line.len() > 0) [
				chatlog.append(sender.join(locals.line)),
			],

			scrolltarget <= get_max_scroll(),
		]

		@cat.proc_def("init_chat")
		def init_chat(locals): return [
			Hide(),
			PenUp(),
			EraseAll(),

			velocity <= 0,
			scrollpos <= MIN_SCROLL,
			scrolltarget <= scrollpos,

			chatlog.delete_all(),
		]

		#self.chatlog = chatlog
		self.init = init_chat
		self.new_message = new_message
		self.gui_loop = gui_loop

if __name__ == "__main__":
	project = Project(template="../test_files/Scratch Project.sb3")

	cat = project.new_sprite("Sprite1")
	chat = Chat(cat)

	cat.on_flag([
		chat.init(),
		chat.new_message(">", "Hello, world!¶This is a test of my amazing word-wrapping library."),

		chat.gui_loop(),
	])

	cat.on_flag([
		chat.new_message(">", "Foobar"),
		Wait(1),

		chat.new_message("<", "barfoo"),

		forever([
			AskAndWait(),
			chat.new_message("<", Answer()),
			Wait(1),
			chat.new_message(">", Literal("You said: ").join(Answer())),
		])
	])

	project.save("../test.sb3", execute=False)
