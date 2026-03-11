import timeit
import random
import string

def generate_random_string(length):
    return ''.join(random.choices(string.ascii_letters + string.digits + " ", k=length))

def original_logic(raw_data, keywords):
    all_announcements = []
    for item in raw_data:
        desc = item.get("desc", "")
        is_match = False
        for kw in keywords:
            if kw.lower() in desc.lower():
                is_match = True
                break
        if is_match:
            all_announcements.append(item)
    return all_announcements

def optimized_logic(raw_data, keywords):
    all_announcements = []
    lowered_keywords = [kw.lower() for kw in keywords]
    for item in raw_data:
        desc = item.get("desc", "").lower()
        is_match = False
        for kw in lowered_keywords:
            if kw in desc:
                is_match = True
                break
        if is_match:
            all_announcements.append(item)
    return all_announcements

# Setup data
num_items = 1000
keywords = ["Analyst", "Institutional Investor", "Meet", "Con. Call", "Press Release", "Media Release", "Presentation", "Investor Presentation"]
raw_data = [{"desc": generate_random_string(100)} for _ in range(num_items)]

# Add some matches
for i in range(100):
    raw_data[i]["desc"] += " " + random.choice(keywords)

def run_benchmark():
    t_original = timeit.timeit(lambda: original_logic(raw_data, keywords), number=100)
    t_optimized = timeit.timeit(lambda: optimized_logic(raw_data, keywords), number=100)

    print(f"Original logic: {t_original:.4f}s")
    print(f"Optimized logic: {t_optimized:.4f}s")
    print(f"Improvement: {(t_original - t_optimized) / t_original * 100:.2f}%")

if __name__ == "__main__":
    run_benchmark()
