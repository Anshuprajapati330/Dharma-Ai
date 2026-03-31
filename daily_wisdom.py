import random
from datetime import datetime
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
data_folder = os.path.join(base_dir, "data")
data_folder = "data"
def get_daily_wisdom(collection):
    data = collection.get()
    documents = data["documents"]

    if not documents:
        return "No wisdom available."

    today = datetime.now().strftime("%Y-%m-%d")
    random.seed(today)

    wisdom = random.choice(documents)
    return wisdom

# print("Total documents loaded:", len(documents))