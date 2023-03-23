import matplotlib.pyplot as plt

outFile = 'fish.txt'
f = open('fish-gold-official.txt')
gold = set()
exGold = set()
for line in f:
    gold.add(line.strip())
f = open('fish-gold-increased.txt')
for line in f:
    exGold.add(line.strip())
f = open(outFile)
correct = 0
hcorrect = 0
total = 0
accuracies = []
steps = []
for line in f:
    if line.strip() in gold:
        correct += 1
        hcorrect += 1
    elif line.strip() not in exGold:
        print(str(total) + ')', line.strip(), ' was not in the gold list.')
    total += 1
    if total > 0 and total % 5 == 0:
        accuracies.append(hcorrect/5)
        hcorrect = 0
        steps.append(total)
print('accuracy: ', correct/total)
plt.scatter(steps, accuracies)
plt.show()


f = open('fish-gold-increased.txt')
for line in f:
    exGold.add(line.strip())
f = open(outFile)
correct = 0
hcorrect = 0
total = 0
accuracies = []
steps = []
for line in f:
    if line.strip() in gold or line.strip() in exGold:
        correct += 1
        hcorrect += 1
    total += 1
    if total > 0 and total % 5 == 0:
        accuracies.append(hcorrect/5)
        steps.append(total)
        hcorrect = 0
print('accuracy: ', correct / total)
plt.scatter(steps, accuracies)
plt.show()