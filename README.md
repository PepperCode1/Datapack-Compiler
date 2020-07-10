# DatapackCompiler
A Python program to compile a custom language into a Minecraft datapack

## How to use it
First, make sure lark-parser is installed. If it is not, install it with `pip install lark-parser`. Write your code into code.txt (which contains a sample program) and run compiler.py with Python 3. The resulting datapack will be put into the same directory as compiler.py.

## How it Works
This compiler uses lark-parser to parse the code into a tree and then process it into mcfunction files.

## The Language
The custom language only contains basic elements, such as while, if, variables, functions, and operations. This language has a Java and Python-like syntax. The to-do list at the top of compiler.py details which features are not in the language.
