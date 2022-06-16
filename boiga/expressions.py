from . import ast

def serialise_expression(sprite, expression, parent, shadow=False):
	if not issubclass(type(expression), ast.core.Expression):
		raise Exception(f"Cannot serialise {expression!r} as a expression")
	
	blocks_json = sprite.blocks_json

	uid = sprite.gen_uid()
	blocks_json[uid] = {
		"next": None,
		"parent": parent,
		"inputs": {},
		"fields": {},
		"shadow": shadow,
		"topLevel": False,
	}

	# XXX: should round be in here? does it work?
	UNARYMATHOPS = ["abs", "floor", "ceiling", "sqrt", "sin", "cos", "tan",
		"asin", "acos", "atan", "ln", "log", "e ^", "10 ^", "round"]

	if type(expression) is ast.core.BinaryOp:
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

			out = {
				"opcode": opcode,
				"inputs": {
					an1: serialiser(expression.lval, uid),
					an2: serialiser(expression.rval, uid),
				},
			}
		else:
			raise Exception(f"Unable to serialise expression {expression!r}")

	elif type(expression) is ast.core.ListIndex:
		out = {
			"opcode": "data_itemoflist",
			"inputs": {
				"INDEX": sprite.serialise_arg(expression.index, uid)
			},
			"fields": {
				"LIST": [
					expression.list.name,
					expression.list.uid
				]
			},
		}

	elif type(expression) is ast.core.ListItemNum:
		out = {
			"opcode": "data_itemnumoflist",
			"inputs": {
				"ITEM": sprite.sprite.serialise_arg(expression.item, uid)
			},
			"fields": {
				"LIST": [
					expression.list.name,
					expression.list.uid
				]
			},
		}

	elif type(expression) is ast.core.UnaryOp:
		if expression.op == "!":
			out = {
				"opcode": "operator_not",
				"inputs": {
					"OPERAND": sprite.serialise_bool(expression.value, uid),
				},
			}

		elif expression.op == "len":
			out = {
				"opcode": "operator_length",
				"inputs": {
					"STRING": sprite.serialise_arg(expression.value, uid),
				},
			}

		elif expression.op in UNARYMATHOPS:
			out = {
				"opcode": "operator_mathop",
				"inputs": {
					"NUM": sprite.serialise_arg(expression.value, uid),
				},
				"fields": {
					"OPERATOR": [expression.op, None]
				},
			}

		elif expression.op == "listlen":
			out = {
				"opcode": "data_lengthoflist",
				"fields": {
					"LIST": [expression.value.name, expression.value.uid],
				},
			}

		else:
			raise Exception(f"Unable to serialise expression {expression!r}")
	
	elif type(expression) is ast.core.ProcVar:
		out = {
			"opcode": "argument_reporter_string_number",
			"fields": {
				"VALUE": [expression.name, None]
			},
		}
	
	elif type(expression) is ast.core.ProcVarBool:
		out = {
			"opcode": "argument_reporter_boolean",
			"fields": {
				"VALUE": [expression.name, None]
			},
		}
	
	elif type(expression) is ast.DaysSince2k:
		out = {"opcode": "sensing_dayssince2000"}
	
	elif type(expression) is ast.Answer:
		out = {"opcode": "sensing_answer"}
	
	elif type(expression) is ast.MouseDown:
		out = {"opcode": "sensing_mousedown"}
	
	elif type(expression) is ast.MouseX:
		out = {"opcode": "sensing_mousex"}
	
	elif type(expression) is ast.MouseY:
		out = {"opcode": "sensing_mousey"}
	
	elif type(expression) is ast.CostumeNumber:
		out = {
			"opcode": "looks_costumenumbername",
			"fields": {
				"NUMBER_NAME": ["number", None]
			},
		}
	
	elif type(expression) is ast.Touching:
		out = {
			"opcode": "sensing_touchingobject",
			"inputs": {
				"TOUCHINGOBJECTMENU": sprite.serialise_arg(expression.thing, uid)
			},
		}
	
	elif type(expression) is ast.TouchingColour:
		out = {
			"opcode": "sensing_touchingcolor",
			"inputs": {
				"COLOR": sprite.serialise_arg(expression.colour, uid, alternative=[9, "#FF0000"])
			},
		}

	elif type(expression) is ast.core.PenParamMenu:
		out = {
			"opcode": "pen_menu_colorParam",
			"fields": {
				"colorParam": [expression.param, None],
			}
		}
	
	elif type(expression) is ast.core.TouchingObjectMenu:
		out = {
			"opcode": "sensing_touchingobjectmenu",
			"fields": {
				"TOUCHINGOBJECTMENU": [expression.object, None],
			}
		}
	
	elif type(expression) is ast.core.Costume:
		out = {
			"opcode": "looks_costume",
			"fields": {
				"COSTUME": [expression.costumename, None],
			}
		}

	else:
		raise Exception(f"Unable to serialise expression {expression!r}")
	
	blocks_json[uid].update(out)
	return uid
