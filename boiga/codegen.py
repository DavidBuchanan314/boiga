from .utils import gen_uid
from zipfile import ZipFile
import json
import sys

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
	
	def save(self, filename, stealthy=False):
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
			
			print(json.dumps(project, indent=4))
			with zf.open("project.json", "w") as projfile:
				projfile.write(json.dumps(project).encode())
			
			for asset_name in self.used_assets:
				with zf.open(asset_name, "w") as f:
					f.write(self.asset_data[asset_name])


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
	
	def proc_def(self, fmt, generator):
		uid = gen_uid()
		# TODO: generate proc definition code, add to scripts
		# we're gonna need some kinda per-sprite proc registry,
		# to support overwriting existing procs
		return lambda *args: ast.Statement("proc_call", PROC=uid, ARGS=args)
	
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


def serialise_script(blocks_json, sprite, script):
	parent = None
	for statement in script:
		uid = serialise_statement(blocks_json, sprite, statement)
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


def serialise_statement(blocks_json, sprite, statement):
	uid = gen_uid()
	
	if statement.op == "event_whenflagclicked":
		out = {
			"opcode": "event_whenflagclicked",
			"inputs": {},
			"fields": {},
		}
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
	else:
		raise Exception(f"I don't know how to serialise this op: {statement.op!r}")
	
	out["shadow"] = False
	out["topLevel"] = False
	
	blocks_json[uid] = out
	
	return uid


def serialise_arg(blocks_json, sprite, expression, parent):
	expression = expression.simplified() # experimental!
	
	# primitive expressions https://github.com/LLK/scratch-vm/blob/80e25f7b2a47ec2f3d8bb05fb62c7ceb8a1c99f0/src/serialization/sb3.js#L63
	if type(expression) is ast.Literal:
		return [1, [10 if type(expression.value) is str else 4, str(expression.value)]]
	if type(expression) is ast.Var:
		return [3, [12, expression.name, expression.uid], [10, ""]]
	
	# compound expressions
	return [3, serialise_expression(blocks_json, sprite, expression, parent), [10, ""]]


def serialise_expression(blocks_json, sprite, expression, parent):
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
		}
		if expression.op in opmap:
			argname = opmap[expression.op][1]
			blocks_json[uid] = {
				"opcode": opmap[expression.op][0],
				"next": None,
				"parent": parent,
				"inputs": {
					argname+"1": serialise_arg(blocks_json, sprite, expression.lval, uid),
					argname+"2": serialise_arg(blocks_json, sprite, expression.rval, uid),
				},
				"fields": {},
				"shadow": False,
				"topLevel": False,
			}
			return uid
	
	raise Exception(f"Unable to serialise expression of type {type(expression)!r}")
