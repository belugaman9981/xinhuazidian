import re
import regex
from zhon import hanzi

text = "测试 𠀀 123 hello"
characters_found = regex.findall(r'\p{Han}', text)

print(characters_found) 