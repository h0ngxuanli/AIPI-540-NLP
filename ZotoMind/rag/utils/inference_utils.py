import re

def convert_to_latex(text):
    text = text.replace('\\\\', '\\')
    pattern = r"\\\((.*?)\\\)"
    converted_text = re.sub(pattern, r"$\1$", text)
    pattern = r"\\\[(.*?)\\\]"
    converted_text = re.sub(pattern, r"$\1$", converted_text)
    return converted_text