"""
to do
fix order of operations
; in commands using \;
comments
return and void
break and continue
variable scopes
for loops
array types
"""

#run in Minecraft using /function [datapack_id]:main

import lark
import os
import shutil

datapack_name = "test"
datapack_id = "test"

with open("code.txt", "r") as f:
	code = f.read()

parser = lark.Lark.open("grammar.lark")
main_tree = parser.parse(code)
main_hash = str(main_tree.__hash__())

commands = {}
functions = {}
locked = []

def add_command(tree_hash, command):
	global commands
	if tree_hash not in commands:
		commands[tree_hash] = []
	commands[tree_hash] += [command]

def transfer_commands(to_hash, from_hash):
	global commands
	if to_hash not in commands:
		commands[to_hash] = []
	commands[to_hash] += commands[from_hash]

#transfer from commands to functions function

def lock_commands(tree_hash):
	global locked
	locked += [tree_hash]

class TestVisitor(lark.Visitor):
	def __init__(self):
		setattr(self, "if", self._if)
		setattr(self, "while", self._while)

	def code(self, tree):
		global functions
		assert tree.data == "code"
		tree_hash = str(tree.__hash__())
		if tree_hash in locked:
			return
		children = tree.children
		
		name = "code_"+tree_hash
		if name not in functions:
			functions[name] = []
		for child in children:
			if type(child) == lark.Tree:
				if str(child.__hash__()) in commands:
					functions[name] += commands[str(child.__hash__())]
		
		lock_commands(tree_hash)

	def create_variable(self, tree):
		assert tree.data == "create_variable"
		tree_hash = str(tree.__hash__())
		if tree_hash in locked:
			return
		children = tree.children
		
		if str(children[0]) == "int":
			name = children[1]
			if len(children) == 3:
				value = children[2]
				transfer_commands(tree_hash, str(value.__hash__()))
				command = "scoreboard players operation "+name+" variables = "+str(value.__hash__())+" expr_temp"
			else:
				command = "scoreboard players set "+name+" variables 0"
			add_command(tree_hash, command)
		
		lock_commands(tree_hash)
	
	def assign_variable(self, tree):
		assert tree.data == "assign_variable"
		tree_hash = str(tree.__hash__())
		if tree_hash in locked:
			return
		children = tree.children
		
		name = children[0]
		operator = children[1]
		value = children[2]
		transfer_commands(tree_hash, str(value.__hash__()))
		command = "scoreboard players operation "+name+" variables "+operator+" "+str(value.__hash__())+" expr_temp"
		add_command(tree_hash, command)

		lock_commands(tree_hash)
	
	def call_function(self, tree):
		assert tree.data == "call_function"
		tree_hash = str(tree.__hash__())
		if tree_hash in locked:
			return
		children = tree.children
		
		i = 0
		for child in children[1:]:
			transfer_commands(tree_hash, str(child.__hash__()))
			command = "scoreboard players operation "+"arg_"+str(i)+" func_temp = "+str(child.__hash__())+" expr_temp"
			add_command(tree_hash, command)
			i += 1
		
		name = children[0]
		command = "function "+datapack_id+":"+"function_"+name
		add_command(tree_hash, command)

		lock_commands(tree_hash)
	
	def command(self, tree):
		assert tree.data == "command"
		tree_hash = str(tree.__hash__())
		if tree_hash in locked:
			return
		children = tree.children
		
		command = str(children[0])
		add_command(tree_hash, command)

		lock_commands(tree_hash)
	
	def _if(self, tree):
		global functions
		assert tree.data == "if"
		tree_hash = str(tree.__hash__())
		if tree_hash in locked:
			return
		children = tree.children
		
		transfer_commands(tree_hash, str(children[0].__hash__()))

		if len(children) == 3:
			command = "scoreboard players operation "+tree_hash+" if_temp = "+str(children[0].__hash__())+" expr_temp"
			add_command(tree_hash, command)
			command = "execute unless score "+tree_hash+" if_temp matches 0 run function "+datapack_id+":"+"code_"+str(children[1].__hash__())
			add_command(tree_hash, command)

			if children[2].data == "code": #code
				command = "execute if score "+tree_hash+" if_temp matches 0 run function "+datapack_id+":"+"code_"+str(children[2].__hash__())
			else: #if
				functions["else_"+str(children[2].__hash__())] = commands[str(children[2].__hash__())]
				command = "execute if score "+tree_hash+" if_temp matches 0 run function "+datapack_id+":"+"else_"+str(children[2].__hash__())
		else:
			command = "execute unless score "+str(children[0].__hash__())+" expr_temp matches 0 run function "+datapack_id+":"+"code_"+str(children[1].__hash__())
		add_command(tree_hash, command)

		lock_commands(tree_hash)
	
	def _while(self, tree):
		global functions
		assert tree.data == "while"
		tree_hash = str(tree.__hash__())
		if tree_hash in locked:
			return
		children = tree.children
		
		functions["while_check_"+tree_hash] = commands[str(children[0].__hash__())] + ["execute unless score "+str(children[0].__hash__())+" expr_temp matches 0 run function "+datapack_id+":"+"while_"+tree_hash]
		functions["while_"+tree_hash] = ["function "+datapack_id+":"+"code_"+str(children[1].__hash__()), "function "+datapack_id+":"+"while_check_"+tree_hash]
		
		command = "function "+datapack_id+":"+"while_check_"+tree_hash
		add_command(tree_hash, command)

		lock_commands(tree_hash)
	
	def function(self, tree):
		global functions
		assert tree.data == "function"
		tree_hash = str(tree.__hash__())
		if tree_hash in locked:
			return
		children = tree.children

		name = children[0]
		commands = []

		i = 0
		for arg in children[1:-1]:
			if str(arg.children[0]) == "int":
				commands += ["scoreboard players operation "+arg.children[1]+" variables = "+"arg_"+str(i)+" func_temp"]
			i += 1
		
		commands += ["function "+datapack_id+":"+"code_"+str(children[-1].__hash__())]
		functions["function_"+name] = commands

		lock_commands(tree_hash)
	
	def expression(self, tree):
		assert tree.data == "expression"
		tree_hash = str(tree.__hash__())
		if tree_hash in locked:
			return
		children = tree.children
		
		if type(children[0]) == lark.Token: #Token
			if children[0].type == "INTEGER": #INTEGER
				command = "scoreboard players set "+tree_hash+" expr_temp "+children[0]
			elif children[0].type == "CNAME": #CNAME
				command = "scoreboard players operation "+tree_hash+" expr_temp = "+children[0]+" variables"
			else: #PREFIX_OPERATOR
				transfer_commands(tree_hash, str(children[1].__hash__()))
				if str(children[0]) == "!": #!
					command = "scoreboard players set "+tree_hash+" expr_temp 0"
					add_command(tree_hash, command)
					command = "execute if score "+str(children[1].__hash__())+" expr_temp matches 0 run scoreboard players set "+tree_hash+" expr_temp 1"
				else: #-
					command = "scoreboard players set "+tree_hash+" expr_temp -1"
					add_command(tree_hash, command)
					command = "scoreboard players operation "+tree_hash+" expr_temp *= "+str(children[1].__hash__())+" expr_temp"
		else: #Tree
			transfer_commands(tree_hash, str(children[0].__hash__()))
			command = "scoreboard players operation "+tree_hash+" expr_temp = "+str(children[0].__hash__())+" expr_temp"
		add_command(tree_hash, command)
		
		if len(children) == 3:
			if type(children[2]) == lark.Token: #Token
				if children[2].type == "INTEGER": #INTEGER
					command = "scoreboard players set "+"temp"+" expr_temp "+children[2]
				else: #CNAME
					command = "scoreboard players operation "+"temp"+" expr_temp = "+children[2]+" variables"
			else: #Tree
				transfer_commands(tree_hash, str(children[2].__hash__()))
				command = "scoreboard players operation "+"temp"+" expr_temp = "+str(children[2].__hash__())+" expr_temp"
			add_command(tree_hash, command)
			
			operator = children[1]
			if operator.type == "MATH_OPERATOR": #MATH_OPERATOR
				command = "scoreboard players operation "+tree_hash+" expr_temp "+operator+"= "+"temp"+" expr_temp"
				add_command(tree_hash, command)
			elif operator.type == "COMPARISON_OPERATOR": #COMPARISON_OPERATOR
				if operator == "!=":
					command = "execute store result score "+tree_hash+" expr_temp unless score "+tree_hash+" expr_temp = "+"temp"+" expr_temp"
				else:
					if operator == "==":
						operator = "="
					command = "execute store result score "+tree_hash+" expr_temp if score "+tree_hash+" expr_temp "+operator+" "+"temp"+" expr_temp"
				add_command(tree_hash, command)
			else: #BOOLEAN_OPERATOR
				command = "execute unless score "+tree_hash+" expr_temp matches 0 run scoreboard players set "+tree_hash+" expr_temp 1"
				add_command(tree_hash, command)
				command = "execute unless score "+"temp"+" expr_temp matches 0 run scoreboard players set "+"temp"+" expr_temp 1"
				add_command(tree_hash, command)
				if operator == "&&":
					command = "scoreboard players operation "+tree_hash+" expr_temp *= "+"temp"+" expr_temp"
				elif operator == "||":
					command = "execute if score "+tree_hash+" expr_temp matches 0 run scoreboard players operation "+tree_hash+" expr_temp = "+"temp"+" expr_temp"
				add_command(tree_hash, command)

		lock_commands(tree_hash)

main_name = "code_"+main_hash

functions[main_name] = []
functions[main_name] += ["scoreboard objectives add variables dummy"]
functions[main_name] += ["scoreboard objectives add expr_temp dummy"]
functions[main_name] += ["scoreboard objectives add if_temp dummy"]
functions[main_name] += ["scoreboard objectives add func_temp dummy"]

TestVisitor().visit(main_tree)

functions[main_name] += ["scoreboard objectives remove variables"]
functions[main_name] += ["scoreboard objectives remove expr_temp"]
functions[main_name] += ["scoreboard objectives remove if_temp"]
functions[main_name] += ["scoreboard objectives remove func_temp"]

functions["main"] = functions[main_name]
del functions[main_name]

folder = os.path.join(datapack_name, "data", datapack_id, "functions")
mcmeta = os.path.join(datapack_name, "pack.mcmeta")
if not os.path.isdir(folder):
	os.makedirs(folder)
if not os.path.isfile(mcmeta):
	shutil.copy("pack.mcmeta", mcmeta)
for name in functions:
	path = os.path.join(folder, name+".mcfunction")
	with open(path, "w") as f:
		f.write("\n".join(functions[name]))
	
print("Datapack compiled")
