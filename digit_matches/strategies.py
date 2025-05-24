from collections import Counter

def least_seen_digit(buffer):
    freq = Counter(buffer)
    all_digits = set(range(10))
    missing = all_digits - set(freq.keys())
    return list(missing)[0] if missing else min(freq, key=freq.get)

def most_frequent_digit(buffer):
    freq = Counter(buffer)
    return max(freq, key=freq.get) if freq else None

def detect_pattern(buffer, window=10, threshold=5):
    recent = list(buffer)[-window:]
    freq = Counter(recent)
    for digit, count in freq.items():
        if count >= threshold:
            return digit
    return None

def detect_compression_breakout(buffer, prev_digits, window=10):
    recent = list(buffer)[-window:]
    unique_digits = set(recent)
    if len(unique_digits) <= 3:
        recent_5 = list(buffer)[-5:]
        breakout_digits = unique_digits - prev_digits
        for digit in breakout_digits:
            if digit in recent_5:
                return digit
    return None