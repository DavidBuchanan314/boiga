from boiga.codegen import Project
from boiga.ast import *

from lib.chacha20_csprng import CSPRNG
from lib.x25519 import X25519
from lib.chacha20 import ChaCha20
from lib.chachapoly1305 import ChaChaPoly1305
from lib.utils import Utils
from lib.chat import Chat
from lib.blake2s import BLAKE2s

project = Project()

cat = project.new_sprite("Sprite1")
utils = Utils(cat)
csprng = CSPRNG(cat, utils)
x25519 = X25519(cat, utils)
blake2s = BLAKE2s(cat, utils)
chacha20 = ChaCha20(cat, utils)
chachapoly1305 = ChaChaPoly1305(cat, chacha20, utils)
chat = Chat(cat, utils)

cat.on_flag([
	chat.init(),
	chat.new_message(">", "Hello, world!¶This is a test of my amazing word-wrapping library."),
	chat.gui_loop(),
])

X25519_SERVER_PUB = cat.new_var("X25519_SERVER_PUB", "24998f25f90e20ed9b9b66da7fb47b4b06eff37d5909de4fe51c151ba0394851")

x25519_client_priv = cat.new_var("x25519_client_priv")
x25519_client_pub = cat.new_var("x25519_client_pub")
x25519_shared_secret = cat.new_var("x25519_shared_secret")
session_key = cat.new_var("session_key")
session_id = cat.new_var("session_id")

DETERMINISTIC = True
DETERMINISTIC_KEY = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
DETERMINISTIC_SESSID = "c001d00d"

cat.on_flag([
	chat.new_message(">", "Initialising CSPRNG... (gathering entropy)"),
	chat.wait_for_animation(),

	csprng.rng_init(),
	chat.new_message(">", "Generating X25519 keypair..."),
	chat.wait_for_animation(),

	csprng.rng_get_hex(32),
	x25519_client_priv <= DETERMINISTIC_KEY if DETERMINISTIC else csprng.rng_get_hex.hex_out,

	chat.new_message(">", Literal("Privkey: ").join(x25519_client_priv)),
	chat.wait_for_animation(),

	x25519.scalarmult(x25519_client_priv, x25519.BASE_POINT),
	x25519_client_pub <= x25519.scalarmult.out_hex,

	chat.new_message(">", Literal("Pubkey: ").join(x25519_client_pub)),
	chat.wait_for_animation(),

	x25519.scalarmult(x25519_client_priv, X25519_SERVER_PUB),
	x25519_shared_secret <= x25519.scalarmult.out_hex,

	chat.new_message(">", Literal("Shared secret: ").join(x25519_shared_secret)),
	chat.wait_for_animation(),

	blake2s.hash(x25519_shared_secret.join(x25519_client_pub).join(X25519_SERVER_PUB)),
	session_key <= blake2s.hash.hex_out,

	chat.new_message(">", Literal("Session key: ").join(session_key)),
	chat.wait_for_animation(),

	csprng.rng_get_hex(4),
	session_id <= DETERMINISTIC_SESSID if DETERMINISTIC else csprng.rng_get_hex.hex_out,

	chachapoly1305.encrypt(session_key, "00000000c001d00d00000000", "07526574723069640000000000000000000000000000000000000000000000000000000000000000000000000000"),

	chat.new_message(">", Literal("Encrypted: ").join(x25519_client_pub).join(session_id).join("00000000").join(chachapoly1305.encrypt.ct_out).join(chachapoly1305.encrypt.tag_out)),
	chat.wait_for_animation(),

	Forever [
		AskAndWait(),
		chat.new_message("<", Answer()),
		Wait(1),
		chat.new_message(">", Literal("You said: ").join(Answer())),
	]
])

project.save("../test.sb3", execute=False)
