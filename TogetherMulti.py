import math
import spacy
import re
from collections import Counter
from spacy.tokens import DocBin
from spacy.matcher import Matcher
import multiprocessing as mp
import probables
import os

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
        if (s.pos_ == 'NOUN' or s.pos_ == 'PROPN') and len(s.text) > 2:
            out.append(s.text)
    return ' '.join(out).lower()

def findTop5(total, adj, targSet, exc):
    maxes = [(0, ''), (0, ''), (0, ''), (0, ''), (0, '')]
    for key in adj:
        ks = key.split()
        if key != '' and key.find('category') == -1 and key not in targSet and ks[len(ks) - 1] not in exc:
            val = (adj[key]) / (total.check(key))
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
        if m[0] != 0:
            results.append(m[1])
    return results

def findTop5noNorm(counter, targSet):
    maxes = [(0, ''), (0, ''), (0, ''), (0, ''), (0, '')]
    for key in counter:
        if key != '' and key.find('category') == -1 and key not in targSet:
            val = counter[key]
            for i in range(len(maxes)):
                if val > maxes[i][0] and i == len(maxes) - 1:
                    maxes[i] = (val, key)
                elif val > maxes[i][0] and val > maxes[i + 1][0]:
                    maxes[i] = maxes[i + 1]
                elif val > maxes[i][0]:
                    maxes[i] = (val, key)
                else:
                    break
    results = []
    for m in maxes:
        if m[0] != 0:
            results.append(m[1])
    return results

def searchFromBack(reStr, searchString):
    '''

    :param reStr: 'searchTerm1|searchTerm2|...'
    :param searchString: string to find any of the above
    :return: True if any of reStr were found, false otherwise
    '''
    split = searchString.split()
    if len(split) > 0:
        match = re.search(reStr, split[len(split) - 1])
        if match != None and match.end() >= len(split[len(split) - 1]) - 2 and match.start() <= 1:
            return True
    return False


def conFinder(tup):
    fplist, dicti, cons, spac = tup
    #print('proc helper')
    connsCands = Counter()
    for fp in fplist:
        for doc in DocBin().from_disk(fp).get_docs(
                spac.vocab):
            # text = page['extract']

            pT = doc
            nps = []
            snps = []
            for np in pT.noun_chunks:
                if np.text.find('category') == -1:
                    hold = removeXWords(np)
                    if len(hold.strip()) > 0:
                        nps.append(hold)
                        snps.append(np)
            #print(len(nps))
            for k in range(len(nps)):
                if nps[k] in dicti:
                    if k < len(nps) - 1 and nps[k + 1] in dicti:
                        connect = doc[snps[k].end:snps[k+1].start].text
                        if connect not in cons and '.' not in connect:
                            connsCands.update([connect])
    #print(poss)
    return connsCands


def wordFinder(tup):
    fpList, dicti, connectors, spac = tup
    poss = Counter()
    for fp in fpList:
        for doc in DocBin().from_disk(fp).get_docs(
                spac.vocab):
            # text = page['extract']
            pT = doc
            nps = []
            snps = []
            for np in pT.noun_chunks:
                if np.text.find('category') == -1:
                    hold = removeXWords(np)
                    if len(hold.strip()) > 0:
                        nps.append(hold)
                        snps.append(np)
            # print(len(nps))
            for k in range(len(nps)):
                if nps[k] in dicti:
                    if k < len(nps) - 1 and nps[k + 1] not in dicti:
                        connect = doc[snps[k].end:snps[k + 1].start].text
                        if connect in connectors:
                            poss.update([nps[k+1]])
                    elif k > 0 and nps[k-1] not in dicti:
                        connect = doc[snps[k-1].end:snps[k].start].text
                        if connect in connectors:
                            poss.update([nps[k - 1]])

    # print(poss)
    return poss


def queSend(fp, out, spac, iternum):
    for doc in DocBin().from_disk(fp).get_docs(spac.vocab):
        for np in doc.noun_chunks:
            out.put(removeXWords(np))
    if iternum == 500 or iternum == 950:
        print(iternum, ' done')

def queReader(q, out):
    ret = probables.CountMinSketch(width=10000, depth=15)
    boo = True
    while boo:
        word = q.get(True)
        if word == 'EOQ9765':
            q.put(word)
            break
        ret.add(word)
    fp = 'cms\\' + str(os.getpid()) + '.cms'
    ret.export(fp)
    out.put(fp)



#print(findFirstToken(['a', 'bc', 'd'], ['bc', 'd']))


if __name__ == '__main__':
    spac = spacy.load('en_core_web_sm')
    # spacy.prefer_gpu()
    SIMULPROCCOUNT = 8

    f = open('seeds/seeds.txt')
    open('fish.txt', 'w').close()

    dic = set()
    cons = set()
    excl = set()  # this is a dictionary with every alt seed word in it, to allow for quick checking

    for line in f:
        dic.add(line.strip())

    altSeeds = ['birds', 'locations', 'fishing', 'weirdUnd']
    altDics = []
    for i in range(len(altSeeds)):
        altDics.append(set())
        for line in open('seeds/' + altSeeds[i] + '.txt'):
            excl.add(line.strip())
            altDics[i].add(line.strip())

    reStr = '|'.join(dic)
    lastA = []
    procs = []
    try:
        npPoss = probables.CountMinSketch(filepath='CMScurr.cms')
    except:
        print('beginning construction of count min sketch')
        npqu = mp.Queue()
        cmsq = mp.Queue()
        readProc = []
        for i in range(50):
            p = (mp.Process(target=queReader, args=(npqu, cmsq)))
            p.start()
            readProc.append(p)
        it = 0
        for dirr in os.scandir(r'D:\eeeeee\Downloads\Spring2022\IE\curatedCorps\using'):  #
            if i > SIMULPROCCOUNT:
                procs[i-SIMULPROCCOUNT].join()
            s = mp.Process(target=queSend, args=(dirr.path, npqu, spac, it))
            s.start()
            procs.append(s)
            it += 1

        for i in range(math.floor(len(procs)/50)):
            mp.connection.wait(x.sentinel for x in procs[i * 50:(i+1)*50])
        npqu.put('EOQ9765')
        mp.connection.wait(x.sentinel for x in readProc)
        npPoss = probables.CountMinSketch(filepath=cmsq.get())
        while not cmsq.empty():
            curr = probables.CountMinSketch(filepath=cmsq.get())
            npPoss.join(curr)

        npPoss.export('CMScurr.cms')

    wcandidates = Counter()
    ccandidates = Counter()

    altCands = []
    altCons = []
    altArgLs = []
    for i in range(len(altSeeds)):
        altCands.append(Counter())
        altArgLs.append([])
        altCons.append(set())

    fps = []
    for dirr in os.scandir(r'D:\eeeeee\Downloads\Spring2022\IE\curatedCorps\using'):
        fps.append(str(dirr.path))
    dbPerProc = int((len(fps)+1) / SIMULPROCCOUNT)
    pool = mp.Pool(processes=SIMULPROCCOUNT)
    cQue = mp.Queue()
    arglist = []

    for i in range(SIMULPROCCOUNT):
        arglist.append((fps[i * dbPerProc:(i + 1) * dbPerProc], dic, cons, spac))
        for j in range(len(altArgLs)):
            altArgLs[j].append((fps[i*dbPerProc:(i+1)*dbPerProc], altDics[j], altCons[j], spac))
    addCount = 5.5
    while len(dic) < 1000:

        if len(dic) % 200 == 0:
            wcandidates = Counter()
            ccandidates = Counter()
            cons = set()
        it = 0

        rets = pool.map(conFinder, arglist)

        for counter in rets:
            ccandidates.update(counter)

        ms = findTop5noNorm(ccandidates, cons)
        for m in range(max(1, int(addCount))):
            ccandidates.pop(ms[len(ms) - 1 - m])
            cons.update([ms[len(ms) - 1 - m]])
        addCount -= 0.1

        if len(dic) <= 10:
            for i in range(len(altDics)):
                rets = pool.map(conFinder, altArgLs[i])
                for counter in rets: altCands[i].update(counter)
                ms = findTop5noNorm(altCands[i], altDics[i])
                altCons[i].update(ms)
                altCands[i] = Counter()

        rets = pool.map(wordFinder, arglist)

        for counter in rets:
            wcandidates.update(counter)

        ms = findTop5(npPoss, wcandidates, dic, excl)
        for m in ms:
            wcandidates.pop(m)

        out = open('fish.txt', 'a', encoding='utf-8')
        for m in ms:
            s = m.split()
            if len(s) > 0:
                print(m)
                dic.add(m)
                try:
                    out.write(m + '\n')
                except:
                    print('was not added to the dic b/c encoding issue')
                reStr += '|' + s[len(s) - 1]
        out.close()

        for i in range(len(altDics)):
            rets = pool.map(wordFinder, altArgLs[i])
            for counter in rets:
                altCands[i].update(counter)
            ms = findTop5(npPoss, altCands[i], altDics[i], excl)
            out = open('alts.txt', 'a', encoding='utf-8')
            for m in ms:
                s = m.split()
                if len(s) > 0:
                    altDics[i].add(m)
                    sp = m.split()
                    excl.add(sp[len(sp)-1])
                    try:
                        out.write(m + '\n')
                    except:
                        a=a
                    reStr += '|' + s[len(s) - 1]
            out.close()


        ccandidates = Counter()

