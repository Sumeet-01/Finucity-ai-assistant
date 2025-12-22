import os
import re

base = r"D:\Moto Edge 50\Projects\Software engineering projects\Finucity\finucity"

# Fix routes.py
routes = os.path.join(base, "routes. py")
if os.path.exists(routes):
    with open(routes, 'r', encoding='utf-8') as f:
        c = f.read()
    c = re.sub(r'\.  html', '.html', c)
    c = re.sub(r'main\. ', 'main.', c)
    c = re.sub(r'auth\. ', 'auth.', c)
    with open(routes, 'w', encoding='utf-8') as f:
        f.write(c)
    print("Fixed routes.py")

# Fix all HTML files
for root, dirs, files in os.walk(os.path.join(base, "templates")):
    for f in files:
        if f.endswith('.html'):
            path = os.path. join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                c = file.read()
            orig = c
            c = re.sub(r'\. html', '.html', c)
            c = re.sub(r'main\. ', 'main.', c)
            c = re. sub(r'auth\. ', 'auth.', c)
            if c != orig:
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(c)
                print(f"Fixed {f}")

print("Done!")