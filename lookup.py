import json

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

# Load the character dictionary
words = load_json("data/word.json")

def find_character(char):
    for entry in words:
        if entry.get("word") == char:
            return entry
    return None

if __name__ == "__main__":
    while True:
        query = input("Enter a Chinese character (or 'q' to quit): ").strip()
        if query.lower() == "q":
            break
        result = find_character(query)
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("Not found.")