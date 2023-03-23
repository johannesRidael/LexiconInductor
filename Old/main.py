import requests
import spacy
import textacy
from bs4 import BeautifulSoup
import re
from collections import Counter


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

while len(dic) < 3000:
    occurances = Counter()
    posS.clear()
    titles = open('corpus.txt')
    for title in titles:
        #url = requests.get('http://en.wikipedia.org/wiki/Special:Random')
        #soup = BeautifulSoup(url.content, 'html.parser')
        #title = soup.find(class_="firstHeading").text
        title = title.strip()
        response = requests.get('https://en.wikipedia.org/w/api.php',
            params={'action': 'query', 'format': 'json', 'titles': title, 'prop': 'extracts', 'explaintext': True}).json()

        page = next(iter(response['query']['pages'].values()))
        if 'missing' not in page:
            #print(page['title'])
        #else:
            text = page['extract']
            pT = spac(text)
            nps = []
            for n in pT.noun_chunks:
                x = removeXWords(n)
                nps.append(x)
                occurances.update([x])
            for i in range(len(nps)):
                if nps[i] in dic:
                    if i < len(nps) - 1 and nps[i+1] not in adj:
                        if nps[i+1] not in posS:
                            posS[nps[i+1]] = 1
                        else:
                            posS[nps[i + 1]] += 1
                    if i > 0 and nps[i-1] not in adj:
                        if nps[i-1] not in posS:
                            posS[nps[i-1]] = 1
                        else:
                            posS[nps[i - 1]] += 1

        ms = findTop5(posS, occurances)
        adj.update(ms)

        occurances = Counter()
        posS.clear()
        titles = open('corpus.txt')
        for title in titles:
            # url = requests.get('http://en.wikipedia.org/wiki/Special:Random')
            # soup = BeautifulSoup(url.content, 'html.parser')
            # title = soup.find(class_="firstHeading").text
            title = title.strip()
            response = requests.get('https://en.wikipedia.org/w/api.php',
                                    params={'action': 'query', 'format': 'json', 'titles': title, 'prop': 'extracts',
                                            'explaintext': True}).json()

            page = next(iter(response['query']['pages'].values()))
            if 'missing' not in page:
                # print(page['title'])
                # else:
                text = page['extract']
                pT = spac(text)
                nps = []
                for n in pT.noun_chunks:
                    x = removeXWords(n)
                    nps.append(x)
                    occurances.update([x])
                for i in range(len(nps)):
                    if nps[i] in adj:
                        if i < len(nps) - 1 and nps[i + 1] not in dic:
                            if nps[i + 1] not in posS:
                                posS[nps[i + 1]] = 1
                            else:
                                posS[nps[i + 1]] += 1
                        if i > 0 and nps[i - 1] not in dic:
                            if nps[i - 1] not in posS:
                                posS[nps[i - 1]] = 1
                            else:
                                posS[nps[i - 1]] += 1

            ms = findTop5(posS, occurances)
        for m in ms:
            print(m)
            dic.add(m)
            out.write(m + '\n')
