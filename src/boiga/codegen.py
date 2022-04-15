import hashlib

from .utils import flatten, gen_uid, BLANK_SVG
from zipfile import ZipFile
import json
import sys
import subprocess
from PIL import Image

from . import ast
from .expressions import serialise_expression
from .statements import serialise_statement

class Project():
	def __init__(self):
		self.asset_data = {} # maps file name (md5.ext) to file contents
		self.sprites = []
		self.monitors = []
		self.stage = self.new_sprite("Stage", is_stage=True)
	
	def new_sprite(self, name, is_stage=False):
		sprite = Sprite(self, name, is_stage=is_stage)
		self.sprites.append(sprite)
		return sprite
	
	def save(self, filename, stealthy=False, execute=False):
		self.used_layers = set() # used during serialisation
		self.used_assets = set()
		
		with ZipFile(filename, "w") as zf:
			project = {
				"targets": [s.serialise() for s in self.sprites],
				"monitors": self.monitors,
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
			
			block_count = 0
			for serialised, sprite in zip(project["targets"], self.sprites):
				block_count += len(serialised["blocks"]) + sprite.block_count
			print(f"[*] Serialised {block_count} blocks")

			# TODO: put this behind a debug flag
			debug_json = json.dumps(project, indent=4)
			#print(debug_json)
			open("DEBUG.json", "w").write(debug_json + "\n")

			with zf.open("project.json", "w") as projfile:
				json_blob = json.dumps(project).encode()
				print(f"[*] project.json size: {len(json_blob)}")
				projfile.write(json_blob)
			
			for asset_name in self.used_assets:
				with zf.open(asset_name, "w") as f:
					f.write(self.asset_data[asset_name])
		
		if execute:
			subprocess.call(["./tools/run_scratch.js", filename])


class Sprite():
	def __init__(self, project, name, is_stage=False):
		self.project = project
		self.name = name
		self.isStage = is_stage
		self.variable_uids = {} # name to uid
		self.variable_values = {} # uid to value
		self.list_uids = {} # name to uid
		self.list_values = {} # uid to value
		self.scripts = []
		self.costumes = {} # indexed by name
		
		self.current_costume = 1 # some way to adjust this?
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
	
	def new_list(self, name, value=[], monitor=None):
		if not type(name) is str:
			raise Exception("List name must be a string")
		
		uid = self.list_uids.get(name, gen_uid())
		self.list_uids[name] = uid
		self.list_values[uid] = value
		if monitor:
			self.project.monitors.append({
				"id": uid,
				"mode": "list",
				"opcode": "data_listcontents",
				"params": {
					"LIST": name
				},
				"spriteName": None if self.name == "Stage" else self.name,
				"value": [],
				"width": monitor[2],
				"height": monitor[3],
				"x": monitor[0],
				"y": monitor[1],
				"visible": True
			})
		return ast.List(self, name, uid)
	
	def add_script(self, stack):
		self.scripts.append(stack)
	
	def add_costume(self, name, data_or_path, extension=None, center=(0, 0)):
		if type(data_or_path) is str:
			path = data_or_path
			data = open(path, "rb").read()
			if extension is None:
				extension = path.split(".")[-1]
		else:
			data = data_or_path

		self.costumes[name] = (data, extension, center)

	def on_flag(self, stack):
		self.add_script(ast.on_flag(stack))

	def on_press(self, key, stack):
		self.add_script(ast.on_press(key, stack))

	def proc_def(self, fmt=None, generator=None, turbo=True):
		if generator is None: # function decorator hackery
			return lambda generator: self.proc_def(fmt, generator, turbo)
		
		if fmt is None:
			arg_names = generator.__code__.co_varnames[:generator.__code__.co_argcount]
			fmt = generator.__name__
			for arg in arg_names[1:]: # skip locals
				if generator.__annotations__.get(arg) is bool:
					fmt += f" <{arg}>"
				else:
					fmt += f" [{arg}]"

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
		self.block_count = 0

		if not self.costumes:
			self.add_costume("costume", BLANK_SVG, "svg")

		sprite = {}
		sprite["isStage"] = self.isStage
		sprite["name"] = self.name
		sprite["variables"] = {}
		sprite["lists"] = {}
		sprite["broadcasts"] = {}
		sprite["blocks"] = {}
		sprite["comments"] = {}
		sprite["currentCostume"] = self.current_costume
		sprite["costumes"] = []
		
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
		
		for costume_name, (data, extension, center) in self.costumes.items():
			md5 = hashlib.md5(data).hexdigest()
			md5ext = f"{md5}.{extension}"
			sprite["costumes"].append({
				"assetId": md5,
				"name": costume_name,
				"md5ext": md5ext,
				"dataFormat": extension,
				"rotationCenterX": center[0],
				"rotationCenterY": center[1]
			})
			self.project.asset_data[md5ext] = data

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
		
		self.blocks_json = sprite["blocks"]
		for script in self.scripts:
			self.serialise_script(script)
		
		return sprite

	def serialise_script(self, script, parent=None):
		top_uid = None
		script = flatten(script)
		for statement in script:
			uid = self.serialise_statement(statement)
			top_uid = top_uid or uid
			self.blocks_json[uid]["next"] = None
			if parent:
				self.blocks_json[uid]["parent"] = parent
				self.blocks_json[parent]["next"] = uid
			else:
				self.blocks_json[uid]["parent"] = None
				self.blocks_json[uid]["topLevel"] = True
				self.blocks_json[uid]["x"] = 0
				self.blocks_json[uid]["y"] = 0
			parent = uid
		
		return [2, top_uid]
	
	def serialise_arg(self, expression, parent, alternative=[10, ""]):
		#expression = expression.simplified() # experimental!
		
		# primitive expressions https://github.com/LLK/scratch-vm/blob/80e25f7b2a47ec2f3d8bb05fb62c7ceb8a1c99f0/src/serialization/sb3.js#L63
		if type(expression) is ast.Literal:
			return [1, [10 if type(expression.value) is str else 4, str(expression.value)]]
		if type(expression) is ast.LiteralColour:
			return [1, [9, expression.value]]
		if type(expression) is ast.Var:
			self.block_count += 1
			return [3, [12, expression.name, expression.uid], alternative]
		
		# compound expressions
		return [3, self.serialise_expression(expression, parent), alternative]

	def serialise_bool(self, expression, parent):
		if expression.type != "bool":
			raise Exception("Cannot serialise non-bool expression as bool: " + repr(expression))
		return [2, self.serialise_expression(expression, parent)]

	def serialise_procproto(self, proto, parent):
		inputs = {}
		self.block_count -= 1

		for var in proto.vars:
			self.block_count -= 1
			inputs[var.uid2] = [1, var.uid]
			self.serialise_expression(var, proto.uid, shadow=True)
		
		self.blocks_json[proto.uid] = {
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
				"warp": "true" if proto.turbo else "false"
			}
		}
		return [1, proto.uid]
	
	def serialise_expression(self, expression, parent, shadow=False):
		return serialise_expression(self, expression, parent, shadow)
	
	def serialise_statement(self, statement):
		return serialise_statement(self, statement)
