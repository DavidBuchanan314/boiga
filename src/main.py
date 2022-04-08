from boiga.codegen import Project
from boiga.ast import *

from lib.chacha20_csprng import CSPRNG
from lib.x25519 import X25519
from lib.utils import Utils
from lib.chat import Chat

project = Project(template="../test_files/Scratch Project.sb3")

cat = project.new_sprite("Sprite1")
utils = Utils(cat)
csprng = CSPRNG(cat, utils)
x25519 = X25519(cat)
chat = Chat(cat)

cat.on_flag([
	chat.init(),
	chat.new_message(">", "Hello, world!¶This is a test of my amazing word-wrapping library."),

	chat.gui_loop(),
])

X25519_SERVER_PUB = "24998f25f90e20ed9b9b66da7fb47b4b06eff37d5909de4fe51c151ba0394851"
X25519_CLIENT_PRIV = cat.new_var("X25519_CLIENT_PRIV")
X25519_CLIENT_PUB = cat.new_var("X25519_CLIENT_PUB")

X25519_SHARED_SECRET = cat.new_var("X25519_SHARED_SECRET")

cat.on_flag([
	chat.new_message(">", "Initialising CSPRNG... (gathering entropy)"),
	Wait(0),
	csprng.rng_init(),
	chat.new_message(">", "Generating X25519 keypair..."),
	Wait(0),

	csprng.rng_get_hex(32),
	X25519_CLIENT_PRIV <= csprng.rng_get_hex.hex_out,

	chat.new_message(">", Literal("Privkey: ").join(X25519_CLIENT_PRIV)),
	Wait(0),

	x25519.scalarmult(X25519_CLIENT_PRIV, x25519.BASE_POINT),
	X25519_CLIENT_PUB <= x25519.scalarmult.out_hex,

	chat.new_message(">", Literal("Pubkey: ").join(X25519_CLIENT_PUB)),
	Wait(0),

	x25519.scalarmult(X25519_CLIENT_PRIV, X25519_SERVER_PUB),
	X25519_SHARED_SECRET <= x25519.scalarmult.out_hex,

	chat.new_message(">", Literal("Shared secret: ").join(X25519_SHARED_SECRET)),
	Wait(0),

	forever([
		AskAndWait(),
		chat.new_message("<", Answer()),
		Wait(1),
		chat.new_message(">", Literal("You said: ").join(Answer())),
	])
])

project.save("../test.sb3", execute=False)
