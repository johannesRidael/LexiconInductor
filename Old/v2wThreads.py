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

def findTop5(total, adj, targSet):
    maxes = [(0, ''), (0, ''), (0, ''), (0, ''), (0, '')]
    for key in adj:
        if key != '' and key.find('category') == -1 and key not in targSet:
            try:
                val = (adj[key]) / (total.check(key))
            except TypeError:
                a = adj[key]
                b = total.check(key)
                b = a
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


def processHelper(fp, oq, searchSet, targSet, spac, iternum, reStr, bf):
    #print('proc helper')
    poss = Counter()
    for doc in DocBin().from_disk(fp).get_docs(
            spac.vocab):
        # text = page['extract']
        pT = doc
        nps = []
        for np in pT.noun_chunks:
            if np.text.find('category') == -1:
                hold = removeXWords(np)
                if len(hold.strip())>0:
                    nps.append(hold)
        #print(len(nps))
        for k in range(len(nps)):
            if bf:
                if nps[k] in searchSet:
                    if k < len(nps) - 1 and nps[k + 1] not in targSet:
                        poss.update([nps[k+1]])
                    if k > 0 and nps[k - 1] not in targSet:
                        poss.update([nps[k-1]])
                #else:
                #    if searchFromBack(reStr, nps[k]) and nps[k] not in targSet:
                #        poss.update([nps[k]])
            else:
                if searchFromBack(reStr, nps[k]):
                    if k < len(nps) - 1 and nps[k + 1] not in targSet:
                        poss.update([nps[k + 1]])
                    if k > 0 and nps[k - 1] not in targSet:
                        poss.update([nps[k - 1]])
    #print(poss)
    oq.put(poss)
    if iternum == 500 or iternum == 950:
        print(iternum, ' done')

def verbPhrasePH(fp, oq, searchSet, targSet, spac, iternum):
    pattern = [{'POS': 'VERB', 'OP': '?'},
               {'POS': 'ADV', 'OP': '*'},
               {'POS': 'AUX', 'OP': '*'},
               {'POS': 'VERB', 'OP': '+'}]

    poss = Counter()
    for doc in DocBin().from_disk(fp).get_docs(spac.vocab):
        # text = page['extract']
        pT = doc
        match = Matcher(spac.vocab)
        match.add('Verb Phrase', None, pattern)
        for sent in pT.sents:
            nps = []
            for np in sent.noun_chunks:
                nps.append(removeXWords(np), np.start, np.end)
            # print(len(nps))
            for k in range(len(nps)):
                if nps[k][0] in searchSet:
                    vps = match(sent)
                    mini = 50
                    hold = mini
                    closestVP = None
                    for _, start, end in vps:
                        mini = min(math.fabs(start - nps[k][2]), math.fabs(end - nps[k][1]), mini)
                        if hold != mini:
                            hold = mini
                            closestVP = sent[start:end]
                    if closestVP not in targSet:
                        poss.update([closestVP])
    # print(poss)
    oq.put(poss)
    if iternum == 500 or iternum == 950:
        print(iternum, ' done')

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
    SIMULPROCCOUNT = 80000
    #inRange = list(range(1, 73374))
    #random.shuffle(inRange)
    #inRange = numpy.load('randOrdArr.npy')
    #inRange = inRange[:200]

    f = open('../seeds/seeds.txt')
    open('fish_normed.txt', 'w').close()
    dic = set()
    adj = set()

    for line in f:
        dic.add(line.strip())

    lastW = dic
    reStr = '|'.join(dic)
    lastA = []
    procs = []
    try:
        npPoss = probables.CountMinSketch(filepath='../CMScurr.cms')
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
    acandidates = Counter()
    while len(dic) < 1000:

        cQue = mp.Queue()
        procs = []
        it = 0
        for dirr in os.scandir(r'D:\eeeeee\Downloads\Spring2022\IE\curatedCorps\using'):
            p = mp.Process(target=processHelper, args=(dirr.path, cQue, lastW, adj, spac, it, reStr, False))
            p.start()
            procs.append(p)
            it += 1
        for i in range(math.floor(len(procs) / 50)):
            mp.connection.wait(x.sentinel for x in procs[i * 50:(i + 1) * 50])


        while not cQue.empty():
            acandidates.update(cQue.get(block=False))

        ms = findTop5(npPoss, acandidates, adj)
        for m in ms:
            acandidates.pop(m)
        adj.update(ms)
        lastA = ms

        it = 0
        for dirr in os.scandir(r'D:\eeeeee\Downloads\Spring2022\IE\curatedCorps\using'):
            p = mp.Process(target=processHelper, args=(dirr.path, cQue, lastA, dic,spac, it, reStr, True))
            p.start()
            procs.append(p)
            it += 1

        for i in range(math.floor(len(procs) / 50)):
            mp.connection.wait(x.sentinel for x in procs[i * 50:(i + 1) * 50])

        while not cQue.empty():
            wcandidates.update(cQue.get())

        ms = findTop5(npPoss, wcandidates, dic)
        for m in ms:
            wcandidates.pop(m)
        lastW = ms
        out = open('fish_normed.txt', 'a')
        for m in ms:
            s = m.split()
            if len(s) > 0:
                print(m)
                dic.add(m)
                out.write(m + '\n')
                reStr += '|' + s[len(s) - 1]
        out.close()
