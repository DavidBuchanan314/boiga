from .utils import gen_uid
from zipfile import ZipFile
import json
import sys
import subprocess

from . import ast

class Project():
	def __init__(self, template=None):
		self.asset_data = {} # maps file name (md5.ext) to file contents
		
		if template:
			with ZipFile(template) as zf:
				self.template_json = json.load(zf.open("project.json"))
				for asset_name in set(zf.namelist()) - {"project.json",}:
					self.asset_data[asset_name] = zf.open(asset_name).read()
		
		self.sprites = []
		self.stage = self.new_sprite("Stage")
	
	def new_sprite(self, name):
		template = None
		if self.template_json:
			for sprite_json in self.template_json["targets"]:
				if sprite_json["name"] == name:
					template = sprite_json
					break
		sprite = Sprite(self, name, template=template)
		self.sprites.append(sprite)
		return sprite
	
	def save(self, filename, stealthy=False, execute=False):
		self.used_layers = set() # used during serialisation
		self.used_assets = set()
		
		with ZipFile(filename, "w") as zf:
			project = {
				"targets": [s.serialise() for s in self.sprites],
				"monitors": [],
				"extensions": [],
				"meta": {
					"semver": "3.0.0",
					"vm": "0.2.0-prerelease.20210706190652",
					"agent": "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
				} if stealthy else {
					"semver": "3.0.0",
					"vm": "0.0.1-com.github.davidbuchanan314.boiga",
					"agent": "Python " + sys.version.replace("\n", "")
				}
			}
			
			# TODO: put this behind a debug flag
			debug_json = json.dumps(project, indent=4)
			#print(debug_json)
			open("DEBUG.json", "w").write(debug_json + "\n")

			with zf.open("project.json", "w") as projfile:
				projfile.write(json.dumps(project).encode())
			
			for asset_name in self.used_assets:
				with zf.open(asset_name, "w") as f:
					f.write(self.asset_data[asset_name])
		
		if execute:
			subprocess.call(["./tools/run_scratch.js", filename])


class Sprite():
	def __init__(self, project, name, template=None):
		self.project = project
		self.name = name
		self.template_json = template
		self.isStage = name == "Stage" # XXX: Technically, any sprite can be called Stage
		self.variable_uids = {} # name to uid
		self.variable_values = {} # uid to value
		self.list_uids = {} # name to uid
		self.list_values = {} # uid to value
		self.scripts = []
		
		if template:
			for uid, (name, value) in template["variables"].items():
				self.variable_uids[name] = uid
				self.variable_values[uid] = value
			
			for uid, (name, value) in template["lists"].items():
				self.list_uids[name] = uid
				self.list_values[uid] = value
			
			self.current_costume = template["currentCostume"]
			self.volume = template["volume"]
		else:
			self.current_costume = 0
			self.volume = 100
	
	def new_var(self, name, value=""):
		if not type(name) is str:
			raise Exception("Variable name must be a string")
		
		#if name in self.variable_uids:
		#	raise Exception(f"Variable {name!r} already exists!")
		
		uid = self.variable_uids.get(name, gen_uid())
		self.variable_uids[name] = uid
		self.variable_values[uid] = value
		return ast.Var(self, name, uid)
	
	def new_list(self, name, value=[]):
		if not type(name) is str:
			raise Exception("List name must be a string")
		
		uid = self.list_uids.get(name, gen_uid())
		self.list_uids[name] = uid
		self.list_values[uid] = value
		return ast.List(self, name, uid)
	
	def add_script(self, stack):
		self.scripts.append(stack)
	
	def on_flag(self, stack):
		self.add_script(ast.on_flag(stack))

	def proc_def(self, fmt, generator=None, turbo=True):
		if generator is None: # function decorator hackery
			return lambda generator: self.proc_def(fmt, generator, turbo)
		
		uid = gen_uid()
		proc_proto = ast.ProcProto(self, fmt, uid, turbo)

		for varname, vartype in zip(proc_proto.argnames, proc_proto.argtypes):
			varinit = ast.ProcVarBool if vartype == "bool" else ast.ProcVar
			proc_proto.vars.append(varinit(self, proc_proto, varname, gen_uid(), gen_uid()))
		
		procdef = ast.ProcDef(proc_proto)

		self.add_script([procdef] + generator(procdef, *proc_proto.vars))

		# TODO: generate proc definition code, add to scripts
		# we're gonna need some kinda per-sprite proc registry,
		# to support overwriting existing procs
		return procdef#lambda *args: ast.Statement("procedures_call", PROC=uid, ARGS=args)
	
	def serialise(self):
		if self.template_json:
			sprite = self.template_json
		else:
			sprite = {}
			sprite["isStage"] = self.isStage
			sprite["name"] = self.name
			sprite["variables"] = {}
			sprite["lists"] = {}
			sprite["broadcasts"] = {}
			sprite["blocks"] = {}
			sprite["comments"] = {}
			sprite["currentCostume"] = self.current_costume
			sprite["costumes"] = [{ # TODO: this should be an empty list that we add to later
				"assetId": "cd21514d0531fdffb22204e0ec5ed84a",
				"name": "backdrop1",
				"md5ext": "cd21514d0531fdffb22204e0ec5ed84a.svg",
				"dataFormat": "svg",
				"rotationCenterX": 240,
				"rotationCenterY": 180
			}]
			
			sprite["sounds"] = []
			sprite["volume"] = self.volume
			
			# fid the next unused layer
			for i in range(99999999):
				if i not in self.project.used_layers:
					sprite["layerOrder"] = i
					break
			else:
				raise Exception("Too many layers?!??!")
			
			if self.isStage:
				sprite["tempo"] = 60
				sprite["videoTransparency"] = 50
				sprite["videoState"] = "on"
				sprite["textToSpeechLanguage"] = None
			else:
				sprite["visible"] = True
				sprite["x"] = 0
				sprite["y"] = 0
				sprite["size"] = 100
				sprite["direction"] = 90
				sprite["draggable"] = False
				sprite["rotationStyle"] = "all around"
		
		# keep track of which lauers are occupied
		self.project.used_layers.add(sprite["layerOrder"])
		
		# mark the asset to be added to the sb3
		for asset in sprite["costumes"] + sprite["sounds"]:
			self.project.used_assets.add(asset["md5ext"])
		
		sprite["variables"] = {
			uid: [name, self.variable_values[uid]]
			for name, uid
			in self.variable_uids.items()
		}
		
		sprite["lists"] = {
			uid: [name, self.list_values[uid]]
			for name, uid
			in self.list_uids.items()
		}
		
		for script in self.scripts:
			serialise_script(sprite["blocks"], self, script)
		
		return sprite

# https://stackoverflow.com/a/12472564
def flatten(S):
	if S == []:
		return S
	if isinstance(S[0], list):
		return flatten(S[0]) + flatten(S[1:])
	return S[:1] + flatten(S[1:])

def serialise_script(blocks_json, sprite, script, parent=None):
	top_uid = None
	script = flatten(script)
	for statement in script:
		uid = serialise_statement(blocks_json, sprite, statement)
		top_uid = top_uid or uid
		blocks_json[uid]["next"] = None
		if parent:
			blocks_json[uid]["parent"] = parent
			blocks_json[parent]["next"] = uid
		else:
			blocks_json[uid]["parent"] = None
			blocks_json[uid]["topLevel"] = True
			blocks_json[uid]["x"] = 0
			blocks_json[uid]["y"] = 0
		parent = uid
	
	return [2, top_uid]


def serialise_statement(blocks_json, sprite, statement):
	#if type(statement) is list:
	#	for substatement in statement:
	#		uid = serialise_statement(blocks_json, sprite, substatement)
	#	return uid
	if not issubclass(type(statement), ast.Statement):
		raise Exception(f"Cannot serialise {statement!r} as a statement")

	uid = gen_uid()
	blocks_json[uid] = {
		"inputs": {},
		"fields": {}
	}
	
	# ===== EVENTS =======
	if statement.op == "event_whenflagclicked":
		out = {
			"opcode": "event_whenflagclicked"
		}
	
	# ===== CONTROL =======
	elif statement.op == "control_repeat":
		out = {
			"opcode": "control_repeat",
			"inputs": {
				"TIMES": serialise_arg(blocks_json, sprite, statement.args["TIMES"], uid),
				"SUBSTACK": serialise_script(blocks_json, sprite, statement.args["SUBSTACK"], uid)
			}
		}
	elif statement.op == "control_repeat_until":
		out = {
			"opcode": "control_repeat_until",
			"inputs": {
				"CONDITION": serialise_bool(blocks_json, sprite, statement.args["CONDITION"], uid),
				"SUBSTACK": serialise_script(blocks_json, sprite, statement.args["SUBSTACK"], uid)
			}
		}
	elif statement.op == "control_forever":
		out = {
			"opcode": "control_forever",
			"inputs": {
				"SUBSTACK": serialise_script(blocks_json, sprite, statement.args["SUBSTACK"], uid)
			}
		}
	elif statement.op == "control_if":
		out = {
			"opcode": "control_if",
			"inputs": {
				"CONDITION": serialise_bool(blocks_json, sprite, statement.args["CONDITION"], uid),
				"SUBSTACK": serialise_script(blocks_json, sprite, statement.args["SUBSTACK"], uid)
			}
		}
	elif statement.op == "control_if_else":
		out = {
			"opcode": "control_if_else",
			"inputs": {
				"CONDITION": serialise_bool(blocks_json, sprite, statement.args["CONDITION"], uid),
				"SUBSTACK": serialise_script(blocks_json, sprite, statement.args["SUBSTACK"], uid),
				"SUBSTACK2": serialise_script(blocks_json, sprite, statement.args["SUBSTACK2"], uid)
			}
		}
	
	# ===== DATA =======
	elif statement.op == "data_setvariableto":
		out = {
			"opcode": "data_setvariableto",
			"inputs": {
				"VALUE": serialise_arg(blocks_json, sprite, statement.args["VALUE"], uid)
			},
			"fields": {
				"VARIABLE": [
					statement.args["VARIABLE"].name,
					statement.args["VARIABLE"].uid
				]
			}
		}
	elif statement.op == "data_changevariableby":
		out = {
			"opcode": "data_changevariableby",
			"inputs": {
				"VALUE": serialise_arg(blocks_json, sprite, statement.args["VALUE"], uid)
			},
			"fields": {
				"VARIABLE": [
					statement.args["VARIABLE"].name,
					statement.args["VARIABLE"].uid
				]
			}
		}
	elif statement.op == "data_replaceitemoflist":
		out = {
			"opcode": "data_replaceitemoflist",
			"inputs": {
				"INDEX": serialise_arg(blocks_json, sprite, statement.args["INDEX"], uid),
				"ITEM": serialise_arg(blocks_json, sprite, statement.args["ITEM"], uid)
			},
			"fields": {
				"LIST": [
					statement.args["LIST"].name,
					statement.args["LIST"].uid
				]
			}
		}
	elif statement.op == "data_addtolist":
		out = {
			"opcode": "data_addtolist",
			"inputs": {
				"ITEM": serialise_arg(blocks_json, sprite, statement.args["ITEM"], uid)
			},
			"fields": {
				"LIST": [
					statement.args["LIST"].name,
					statement.args["LIST"].uid
				]
			}
		}
	elif statement.op == "data_deletealloflist":
		out = {
			"opcode": "data_deletealloflist",
			"fields": {
				"LIST": [
					statement.args["LIST"].name,
					statement.args["LIST"].uid
				]
			}
		}
	elif statement.op == "data_deleteoflist":
		out = {
			"opcode": "data_deleteoflist",
			"inputs": {
				"INDEX": serialise_arg(blocks_json, sprite, statement.args["INDEX"], uid)
			},
			"fields": {
				"LIST": [
					statement.args["LIST"].name,
					statement.args["LIST"].uid
				]
			}
		}
	
	# ======= custom blocks =======

	elif statement.op == "procedures_definition":
		out = {
			"opcode": "procedures_definition",
			"inputs": {
				"custom_block": serialise_procproto(blocks_json, sprite, statement.proto, uid)
			}
		}

	elif statement.op == "procedures_call":
		inputs = {}
		for arg, var in zip(statement.args["ARGS"], statement.proc.vars):
			inputs[var.uid2] = serialise_arg(blocks_json, sprite, arg, uid)
		out = {
			"opcode": "procedures_call",
			"inputs": inputs,
			"mutation": {
				"tagName": "mutation",
				"children": [],
				"proccode": statement.proc.proccode,
				"argumentids": json.dumps(list(inputs.keys())),
				"warp": "true" if statement.proc.turbo else "false"
			}
		}

	elif statement.op == "sensing_askandwait":
		out = {
			"opcode": "sensing_askandwait",
			"inputs": {
				"QUESTION": serialise_arg(blocks_json, sprite, statement.prompt, uid)
			}
		}

	else:
		raise Exception(f"I don't know how to serialise this op: {statement.op!r}")
	
	out["shadow"] = False
	out["topLevel"] = False
	
	blocks_json[uid].update(out)
	
	return uid


def serialise_arg(blocks_json, sprite, expression, parent):
	#expression = expression.simplified() # experimental!
	
	# primitive expressions https://github.com/LLK/scratch-vm/blob/80e25f7b2a47ec2f3d8bb05fb62c7ceb8a1c99f0/src/serialization/sb3.js#L63
	if type(expression) is ast.Literal:
		return [1, [10 if type(expression.value) is str else 4, str(expression.value)]]
	if type(expression) is ast.Var:
		return [3, [12, expression.name, expression.uid], [10, ""]]
	
	# compound expressions
	return [3, serialise_expression(blocks_json, sprite, expression, parent), [10, ""]]


def serialise_bool(blocks_json, sprite, expression, parent):
	if expression.type != "bool":
		raise Exception("Cannot serialise non-bool expression as bool: " + repr(expression))
	return [2, serialise_expression(blocks_json, sprite, expression, parent)]

def serialise_procproto(blocks_json, sprite, proto, parent):
	inputs = {}

	for var in proto.vars:
		inputs[var.uid2] = [1, var.uid]
		serialise_expression(blocks_json, sprite, var, proto.uid, shadow=True)
	
	blocks_json[proto.uid] = {
		"opcode": "procedures_prototype",
		"next": None,
		"parent": parent,
		"inputs": inputs,
		"fields": {},
		"shadow": True,
		"topLevel": False,
		"mutation": {
			"tagName": "mutation",
			"children": [],
			"proccode": proto.proccode,
			"argumentids": json.dumps(list(inputs.keys())),
			"argumentnames": json.dumps(proto.argnames),
			"argumentdefaults": json.dumps(["false" if x == "bool" else "" for x in proto.argtypes]),
			"warp": "true"
		}
	}
	return [1, proto.uid]

def serialise_expression(blocks_json, sprite, expression, parent, shadow=False):
	if not issubclass(type(expression), ast.Expression):
		raise Exception(f"Cannot serialise {expression!r} as a expression")
	
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
			serialiser = serialise_bool if expression.op in ["&&", "||"] else serialise_arg
			
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
					an1: serialiser(blocks_json, sprite, expression.lval, uid),
					an2: serialiser(blocks_json, sprite, expression.rval, uid),
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
				"INDEX": serialise_arg(blocks_json, sprite, expression.index, uid)
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
				"ITEM": serialise_arg(blocks_json, sprite, expression.item, uid)
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
					"OPERAND": serialise_bool(blocks_json, sprite, expression.value, uid),
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
					"STRING": serialise_arg(blocks_json, sprite, expression.value, uid),
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
					"NUM": serialise_arg(blocks_json, sprite, expression.value, uid),
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
					"NUM": serialise_arg(blocks_json, sprite, expression.value, uid),
				},
				"fields": {
					"OPERATOR": ["ceiling", None]
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

	raise Exception(f"Unable to serialise expression {expression!r}")
