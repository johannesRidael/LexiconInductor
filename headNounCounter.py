from collections import Counter

file = open('fish-gold-official.txt')
counts = Counter()

for line in file:
    s = line.strip().split()
    counts.update([s[len(s)-1]])

print(counts)