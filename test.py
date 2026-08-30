import re
from zhon import hanzi

print(hanzi.characters)

text = "这是一个测试，不对的话，请告诉我。"

if re.match(f'^[{hanzi.characters}]+$', text):
    print("Contains only Chinese characters!")
    
