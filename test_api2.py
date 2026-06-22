import requests
import json

response = requests.get('http://127.0.0.1:8090/api/books/?page=2')
data = response.json()

print('=== API Response for page 2 ===')
print('Success:', data.get('success'))
print('Books count:', len(data.get('books', [])))
print('Default cover URL:', data.get('default_cover_url'))
print()

# Check first few books
for book in data.get('books', [])[:5]:
    print(f'Title: {book["title"][:40]}')
    print(f'Cover URL: {book.get("cover_image_url", "NONE")}')
    print()
