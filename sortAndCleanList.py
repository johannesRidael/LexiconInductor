
f = open('fish-gold-increased.txt')
fish = set()
for line in f:
    fish.add(line.strip())
fish = list(fish)
fish.sort()
f.close()
f = open('fish-gold-increased.txt', 'w')
for fi in fish:
    f.write(fi + '\n')
