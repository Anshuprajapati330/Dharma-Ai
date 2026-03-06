import json
print("File is running...")
with open("New folder/gita_verses.json", "r", encoding="utf-8") as f:

    data = json.load(f)

print("Total verses:", len(data))
print("First verse:", data[0])
