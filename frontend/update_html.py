import os
import re

directory = r'c:\Users\neeks\Desktop\project\frontend'

for filename in os.listdir(directory):
    if filename.endswith(".html"):
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()

        # Remove CDN script
        content = re.sub(r'<script src="https://cdn.tailwindcss.com[^>]*"></script>', '', content)
        
        # Remove tailwind config script block
        content = re.sub(r'<script id="tailwind-config">.*?</script>', '', content, flags=re.DOTALL)
        
        # Add stylesheet link before </head> if not already there
        if 'href="style.css"' not in content:
            content = content.replace('</head>', '<link rel="stylesheet" href="style.css"></head>')

        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(content)

print("Updated HTML files to use external style.css")
