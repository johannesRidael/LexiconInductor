import requests
import spacy
import textacy
from bs4 import BeautifulSoup
import re
from collections import Counter
from spacy.tokens import DocBin

def findFirstToken(list, sub):
    """

    :param list:
    :param sub:
    :return: list of indices of first element if it is in, otherwise empty list
    """
    i = 0
    while i < len(list):
        indices = []
        if list[i] == sub[0]:
            full = True
            for j in range(1, len(sub)):
                if not (i+j < len(list) and list[i+j] == sub[j]):
                    full = False
                    break
            if full:
                indices.append(i)
                i += j
        i += 1
    #if len(indices) == 0: return -1
    return indices

def removeXWords(str):
    """

    :param str: string to remove non nouns from
    :return: string with words removed
    """
    #str = str.split()
    out = []
    for s in str:
        if s.pos_ == 'NOUN' or s.pos_ == 'PROPN':
            out.append(s.text)
    return ' '.join(out).lower()

def findTop5(dict, occ):
    maxes = [(0, ''), (0, ''), (0, ''), (0, ''), (0, '')]
    for key in dict:
        val = dict[key] / (occ[key] + 1)
        for i in range(len(maxes)):
            if val > maxes[i][0] and i == len(maxes) - 1:
                maxes[i] = (val, key)
            elif val > maxes[i][0] and val > maxes[i+1][0]:
                maxes[i] = maxes[i+1]
            elif val > maxes[i][0]:
                maxes[i] = (val, key)
            else:
                break
    results = []
    for m in maxes:
        results.append(m[1])
    return results



#print(findFirstToken(['a', 'bc', 'd'], ['bc', 'd']))

f = open('../seeds/seeds.txt')
dic = set()
adj = set()

posS = {}
for line in f:
    dic.add(line.strip())
spac = spacy.load('en_core_web_sm')
out = open('fish_normed.txt', 'w')

while len(dic) < 1000:
    occurances = Counter()
    posS.clear()
    for i in range(1, 73374):  #
        for doc in DocBin().from_disk('D:\eeeeee\Downloads\Spring2022\IE\corps\corpus_group' + str(i) + '.spacy').get_docs(spac.vocab):
            #text = page['extract']
            pT = doc
            nps = []
            for n in pT.noun_chunks:
                x = removeXWords(n)
                nps.append(x)
                occurances.update([x])
            for k in range(len(nps)):
                if nps[k] in dic:
                    if k < len(nps) - 1 and nps[k + 1] not in adj:
                        if nps[k + 1] not in posS:
                            posS[nps[k + 1]] = 1
                        else:
                            posS[nps[k + 1]] += 1
                    if k > 0 and nps[k - 1] not in adj:
                        if nps[k - 1] not in posS:
                            posS[nps[k - 1]] = 1
                        else:
                            posS[nps[k - 1]] += 1

    ms = findTop5(posS, occurances)
    adj.update(ms)

    occurances = Counter()
    posS.clear()
    for i in range(1, 73374):  #
        for doc in DocBin().from_disk('D:\eeeeee\Downloads\Spring2022\IE\corps\corpus_group' + str(i) + '.spacy').get_docs(spac.vocab):
            pT = doc
            nps = []
            for n in pT.noun_chunks:
                x = removeXWords(n)
                nps.append(x)
                occurances.update([x])
            for k in range(len(nps)):
                if nps[k] in adj:
                    if k < len(nps) - 1 and nps[k + 1] not in dic:
                        if nps[k + 1] not in posS:
                            posS[nps[k + 1]] = 1
                        else:
                            posS[nps[k + 1]] += 1
                    if k > 0 and nps[k - 1] not in dic:
                        if nps[k - 1] not in posS:
                            posS[nps[k - 1]] = 1
                        else:
                            posS[nps[k - 1]] += 1

    ms = findTop5(posS, occurances)
    for m in ms:
        print(m)
        dic.add(m)
        out.write(m + '\n')
