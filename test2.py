import regex

# \p{Han} instantly captures every single Chinese character and its extensions
text = "测试 𠀀 123 hello"
characters_found = regex.findall(r'\p{Han}', text)

print(characters_found)  # Output: ['测', '试', '𠀀']
