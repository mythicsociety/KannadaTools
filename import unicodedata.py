import unicodedata

# Print Kannada Unicode range mapping
for code_point in range(0x0C80, 0x0CFF + 1):
    char = chr(code_point)
    name = unicodedata.name(char, "Unknown Character")
    print(f"U+{code_point:04X} {char} - {name}")