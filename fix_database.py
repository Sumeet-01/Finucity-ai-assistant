import re

routes_file = r"D:\Moto Edge 50\Projects\Software engineering projects\Finucity\finucity\routes. py"

with open(routes_file, 'r', encoding='utf-8') as f:
    content = f. read()

original = content

# Fix all spaces before . html in render_template calls
content = re.sub(r'\.\s+html', '.html', content)

# Fix all spaces after main.  and auth. 
content = re.sub(r"main\.\s+", "main.", content)
content = re. sub(r"auth\.\s+", "auth.", content)

if content != original:
    with open(routes_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print("routes.py fixed!")
else:
    print("No changes needed")