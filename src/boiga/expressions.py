from . import ast
from .utils import gen_uid

def serialise_expression(sprite, expression, parent, shadow=False):
	if not issubclass(type(expression), ast.Expression):
		raise Exception(f"Cannot serialise {expression!r} as a expression")
	
	blocks_json = sprite.blocks_json

	uid = gen_uid()
	if type(expression) is ast.BinaryOp:
		opmap = {
			"+": ("operator_add", "NUM"),
			"-": ("operator_subtract", "NUM"),
			"*": ("operator_multiply", "NUM"),
			"/": ("operator_divide", "NUM"),
			"<": ("operator_lt", "OPERAND"),
			">": ("operator_gt", "OPERAND"),
			"==": ("operator_equals", "OPERAND"),
			"&&": ("operator_and", "OPERAND"),
			"||": ("operator_or", "OPERAND"),
			"join": ("operator_join", "STRING"),
			"%": ("operator_mod", "NUM"),
			"[]": ("operator_letter_of", "LETTER"),
			"random": ("operator_random", "FROM")
		}
		if expression.op in opmap:
			opcode, argname = opmap[expression.op]
			serialiser = sprite.serialise_bool if expression.op in ["&&", "||"] else sprite.serialise_arg
			
			an1 = argname+"1"
			an2 = argname+"2"

			# TODO: encode this nicely in the table above...
			if expression.op == "[]":
				an1 = "LETTER"
				an2 = "STRING"
			elif expression.op == "random":
				an1 = "FROM"
				an2 = "TO"

			blocks_json[uid] = {
				"opcode": opcode,
				"next": None,
				"parent": parent,
				"inputs": {
					an1: serialiser(expression.lval, uid),
					an2: serialiser(expression.rval, uid),
				},
				"fields": {},
				"shadow": False,
				"topLevel": False,
			}
			return uid
	elif type(expression) is ast.ListIndex:
		blocks_json[uid] = {
			"opcode": "data_itemoflist",
			"next": None,
			"parent": parent,
			"inputs": {
				"INDEX": sprite.serialise_arg(expression.index, uid)
			},
			"fields": {
				"LIST": [
					expression.list.name,
					expression.list.uid
				]
			},
			"shadow": False,
			"topLevel": False,
		}
		return uid
	elif type(expression) is ast.ListItemNum:
		blocks_json[uid] = {
			"opcode": "data_itemnumoflist",
			"next": None,
			"parent": parent,
			"inputs": {
				"ITEM": sprite.sprite.serialise_arg(expression.item, uid)
			},
			"fields": {
				"LIST": [
					expression.list.name,
					expression.list.uid
				]
			},
			"shadow": False,
			"topLevel": False,
		}
		return uid
	elif type(expression) is ast.UnaryOp:
		if expression.op == "!":
			blocks_json[uid] = {
				"opcode": "operator_not",
				"next": None,
				"parent": parent,
				"inputs": {
					"OPERAND": sprite.serialise_bool(expression.value, uid),
				},
				"fields": {},
				"shadow": False,
				"topLevel": False,
			}
			return uid
		elif expression.op == "len":
			blocks_json[uid] = {
				"opcode": "operator_length",
				"next": None,
				"parent": parent,
				"inputs": {
					"STRING": sprite.serialise_arg(expression.value, uid),
				},
				"fields": {},
				"shadow": False,
				"topLevel": False,
			}
			return uid
		elif expression.op == "floor":
			blocks_json[uid] = {
				"opcode": "operator_mathop",
				"next": None,
				"parent": parent,
				"inputs": {
					"NUM": sprite.serialise_arg(expression.value, uid),
				},
				"fields": {
					"OPERATOR": ["floor", None]
				},
				"shadow": False,
				"topLevel": False,
			}
			return uid
		elif expression.op == "ceil":
			blocks_json[uid] = {
				"opcode": "operator_mathop",
				"next": None,
				"parent": parent,
				"inputs": {
					"NUM": sprite.serialise_arg(expression.value, uid),
				},
				"fields": {
					"OPERATOR": ["ceiling", None]
				},
				"shadow": False,
				"topLevel": False,
			}
			return uid
		elif expression.op == "abs":
			blocks_json[uid] = {
				"opcode": "operator_mathop",
				"next": None,
				"parent": parent,
				"inputs": {
					"NUM": sprite.serialise_arg(expression.value, uid),
				},
				"fields": {
					"OPERATOR": ["abs", None]
				},
				"shadow": False,
				"topLevel": False,
			}
			return uid
		elif expression.op == "round":
			blocks_json[uid] = {
				"opcode": "operator_mathop",
				"next": None,
				"parent": parent,
				"inputs": {
					"NUM": sprite.serialise_arg(expression.value, uid),
				},
				"fields": {
					"OPERATOR": ["round", None]
				},
				"shadow": False,
				"topLevel": False,
			}
			return uid
		elif expression.op == "listlen":
			blocks_json[uid] = {
				"opcode": "data_lengthoflist",
				"next": None,
				"parent": parent,
				"inputs": {},
				"fields": {
					"LIST": [expression.value.name, expression.value.uid],
				},
				"shadow": False,
				"topLevel": False,
			}
			return uid
	
	elif type(expression) is ast.ProcVar:
		blocks_json[uid] = {
			"opcode": "argument_reporter_string_number",
			"next": None,
			"parent": parent,
			"inputs": {},
			"fields": {
				"VALUE": [expression.name, None]
			},
			"shadow": shadow,
			"topLevel": False
		}
		return uid
	
	elif type(expression) is ast.ProcVarBool:
		blocks_json[uid] = {
			"opcode": "argument_reporter_boolean",
			"next": None,
			"parent": parent,
			"inputs": {},
			"fields": {
				"VALUE": [expression.name, None]
			},
			"shadow": shadow,
			"topLevel": False
		}
		return uid
	
	elif type(expression) is ast.DaysSince2k:
		blocks_json[uid] = {
			"opcode": "sensing_dayssince2000",
			"next": None,
			"parent": parent,
			"inputs": {},
			"fields": {},
			"shadow": shadow,
			"topLevel": False
		}
		return uid
	
	elif type(expression) is ast.Answer:
		blocks_json[uid] = {
			"opcode": "sensing_answer",
			"next": None,
			"parent": parent,
			"inputs": {},
			"fields": {},
			"shadow": shadow,
			"topLevel": False
		}
		return uid
	
	elif type(expression) is ast.MouseDown:
		blocks_json[uid] = {
			"opcode": "sensing_mousedown",
			"next": None,
			"parent": parent,
			"inputs": {},
			"fields": {},
			"shadow": shadow,
			"topLevel": False
		}
		return uid
	
	elif type(expression) is ast.MouseX:
		blocks_json[uid] = {
			"opcode": "sensing_mousex",
			"next": None,
			"parent": parent,
			"inputs": {},
			"fields": {},
			"shadow": shadow,
			"topLevel": False
		}
		return uid
	
	elif type(expression) is ast.MouseY:
		blocks_json[uid] = {
			"opcode": "sensing_mousey",
			"next": None,
			"parent": parent,
			"inputs": {},
			"fields": {},
			"shadow": shadow,
			"topLevel": False
		}
		return uid
	
	elif type(expression) is ast.CostumeNumber:
		blocks_json[uid] = {
			"opcode": "looks_costumenumbername",
			"next": None,
			"parent": parent,
			"inputs": {},
			"fields": {
				"NUMBER_NAME": ["number", None]
			},
			"shadow": shadow,
			"topLevel": False
		}
		return uid

	raise Exception(f"Unable to serialise expression {expression!r}")
