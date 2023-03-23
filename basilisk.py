import spacy
import math
from collections import Counter
from spacy.tokens import DocBin
import multiprocessing as mp
import os

def findPattern(doc, nlp, np):
    rel = doc[np.end - 1].dep_
    head = doc[np.end-1].head
    return rel + '-' + head.text





def rlog(pattern, allPat, cPat):
    return len(cPat[pattern]) * math.log(len(cPat[pattern]), 2) / len(allPat[pattern])

def removeXWords(str):
    """

    :param str: string to remove non nouns from
    :return: string with words removed
    """
    #str = str.split()
    out = []
    for s in str:
        if (s.pos_ == 'NOUN' or s.pos_ == 'PROPN') and len(s.text) > 2:
            out.append(s.text)
    return ' '.join(out).lower()


def initFindAllPatterns(doc, snps, nps, dic):
    allowedRels = {'nsubj', 'dobj', 'nsubjpass', 'appositive'}#, 'csubjpass', 'csubj', 'dative', 'pobj', 'pcomp'}
    #aret = []
    aDic = {}  # maps pattern to set of nouns extracted
    cDic = {}
    #cret = []
    for i in range(len(nps)):
        rel = doc[snps[i].end - 1].dep_
        if rel in allowedRels:
            head = doc[snps[i].end - 1].head
            hold = rel + '-' + head.text
            #aret.append(hold)
            if hold not in aDic:
                aDic[hold] = set()
            aDic[hold].add(nps[i])
            if nps[i] in dic:
                #cret.append(hold)
                if hold not in cDic:
                    cDic[hold] = set()
                cDic[hold].add(nps[i])
    return aDic, cDic  #aret, cret

def findAllPatterns(doc, snps, nps, dic, patterns):
    #ret = []
    allowedRels = {'nsubj', 'dobj', 'nsubjpass'} #, 'csubj', 'csubjpass', 'dative', 'pobj', 'pcomp'}
    cDic = {}
    for i in range(len(nps)):
        rel = doc[snps[i].end - 1].dep_
        if rel in allowedRels:
            head = doc[snps[i].end - 1].head
            hold = rel + '-' + head.text
            if nps[i] in dic and hold not in patterns:
                #ret.append(hold)
                if hold not in cDic:
                    cDic[hold] = set()
                cDic[hold].add(nps[i])
    return cDic #ret


def initPatternSearchHelper(tup):
    fplist, patterns, dicti, spac = tup
    allC = {}
    catC = {}  # catC[pattern] -> set(words)
    allList = []
    cList = []


    for fp in fplist:
        for doc in DocBin().from_disk(fp).get_docs(spac.vocab):
            nps = []
            snps = []
            for np in doc.noun_chunks:
                if np.text.find('category') == -1:
                    hold = removeXWords(np)
                    if len(hold.strip()) > 0:
                        nps.append(hold)
                        snps.append(np)
            ret = initFindAllPatterns(doc, snps, nps, dicti)
            allList.append(ret[0])
            cList.append(ret[1])
    allC = combWordDics(allC, allList)
    catC = combWordDics(catC, cList)
    return allC, catC


def patternSearchHelper(tup):
    fplist, patterns, dicti, spac = tup
    catC = {}
    lis = []
    for fp in fplist:
        for doc in DocBin().from_disk(fp).get_docs(spac.vocab):
            nps = []
            snps = []
            for np in doc.noun_chunks:
                if np.text.find('category') == -1:
                    hold = removeXWords(np)
                    if len(hold.strip()) > 0:
                        nps.append(hold)
                        snps.append(np)
            lis.append(findAllPatterns(doc, snps, nps, dicti, patterns))
    catC = combWordDics(catC, lis)
    return catC


def combWordDics(org, dList):
    ret = org
    for i in range(0, len(dList)):
        for key in dList[i]:
            if key not in ret:
                ret[key] = dList[i][key]
            else:
                ret[key].update(dList[i][key])
    return ret

def findAllWords(doc, snps, nps, patterns, dic):
    wordDic = {}  # wordDic[word] is a set containing all the patterns that produced it
    patDic = {}  # pat[pat] is a set
    #pC = {}  # pC[word][pattern] = count of how many times that pat produced that word
    #ret = []  # add a word every time a pattern produces it
    for i in range(len(nps)):
        rel = doc[snps[i].end - 1].dep_
        head = doc[snps[i].end - 1].head
        pat = rel + '-' + head.text
        if pat in patterns and nps[i] not in dic:
            if pat not in patDic:
                patDic[pat] = set()
            patDic[pat].add(nps[i])
            if nps[i] not in wordDic:
                wordDic[nps[i]] = set()
                #pC[nps[i]] = Counter()
            wordDic[nps[i]].add(pat)
            #pC[nps[i]].update([pat])
    return wordDic, patDic  #pC, ret


def wordSearchHelper(tup):
    fplist, patterns, dic, spac = tup
    wordPats = {}
    patWords = {}
    #wordNextC = Counter()
    #pC = {}
    dlist = []
    plist = []
    for fp in fplist:
        for doc in DocBin().from_disk(fp).get_docs(spac.vocab):
            nps = []
            snps = []
            for np in doc.noun_chunks:
                if np.text.find('category') == -1:
                    hold = removeXWords(np)
                    if len(hold.strip()) > 0:
                        nps.append(hold)
                        snps.append(np)
            wD, pD = findAllWords(doc, snps, nps, patterns, dic)
            dlist.append(wD)
            plist.append(pD)

    wordPats = combWordDics(wordPats,dlist)
    patWords = combWordDics(patWords, plist)
    return wordPats, patWords, #pC, wordNextC


def avgLog(word, wordPats, patWords):
    ret = 0
    for pat in wordPats[word]:
        ret += math.log(len(patWords[pat]) + 1, 2)
    return ret/(len(wordPats[word]))


if __name__ == '__main__':
    startPatternCount = 20
    simProcCount = 8
    pool = mp.Pool(processes=simProcCount)
    nlp = spacy.load('en_core_web_sm')
    cDic = {}
    aDic = {}
    patterns = set()
    f = open('seeds/seeds.txt')
    open('fish.txt', 'w').close()

    dic = set()
    patterns = set()
    for line in f:
        dic.add(line.strip())
    f.close()

    fps = []
    for dirr in os.scandir(r'D:\eeeeee\Downloads\Spring2022\IE\curatedCorps\using'):
        fps.append(str(dirr.path))
    dbPerProc = int((len(fps) + 1) / simProcCount)

    argList = []
    for i in range(simProcCount):
        argList.append((fps[i * dbPerProc:(i + 1) * dbPerProc], patterns, dic, nlp))

    allR = pool.map(initPatternSearchHelper, argList)

    aList = [x[0] for x in allR]
    cList = [x[1] for x in allR]

    aDic = combWordDics(aDic, aList)
    cDic = combWordDics(cDic, cList)

    scores = Counter()
    for key in cDic:
        scores[key] = rlog(key, cDic, aDic)

    patterns.update([x[0] for x in scores.most_common(startPatternCount) if x[1] > 0])


    while len(dic) < 500:
        allR = pool.map(wordSearchHelper, argList)

        wDic = {}
        pDic = {}

        wList = [x[0] for x in allR]
        pList = [x[1] for x in allR]

        wDic = combWordDics(wDic, wList)
        pDic = combWordDics(pDic, pList)

        scores = Counter()
        for word in wDic:
            scores[word] = avgLog(word, wDic, pDic)

        newWords = [x[0] for x in scores.most_common(5) if x[1] > 0]


        out = open('fish.txt', 'a')
        for m in newWords:
            s = m.split()
            if len(s) > 0:
                print(m)
                dic.add(m)
                try:
                    out.write(m + '\n')
                except:
                    print('was not added due to characters')
        out.close()


        allR = pool.map(patternSearchHelper, argList)

        aList = allR

        aDic = combWordDics(aDic, aList)
        cDic = combWordDics(cDic, cList)

        scores = Counter()
        for key in cDic:
            scores[key] = rlog(key, cDic, aDic)

        m = scores.most_common(1)[0]
        patterns.update({m[0]: m[1]})






