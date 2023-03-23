import math
from collections import Counter
from spacy.tokens import DocBin
import spacy
import random
import multiprocessing as mp
from multiprocessing import Queue
import atexit


def sumSeeds(counter):
    seeds = open('seeds/seeds.txt').read().split()
    sum = 0
    for seed in seeds:
        if seed in counter:
            sum += counter.get(seed)
    return sum


def docSender(docbinda, spac, qs):
    for docbind in docbinda:
        for doc in DocBin().from_disk(
                'D:\eeeeee\Downloads\Spring2022\IE\corps\corpus_group' + str(docbind) + '.spacy').get_docs(
            spac.vocab):
            count = Counter()
            count.update(doc.text.split())
            summ = sumSeeds(count)
            if summ > 0 and summ < 25:
                qs[int((summ-1)/2)].put(doc)#.put((doc, (summ - 1) * 2 + random.choice([0, 1])))
                #print('document added')
            elif summ >= 25:
                qs[12].put(doc)#48 + random.choice([0, 1, 2])))
        if docbind == docbinda[(int)(len(docbinda)/2)]:
            print('Update: ', docbind, '/73374 DocBins parsed')
    print('exiting sender')


def docReader(inq, size):
    tup = inq.get(block=True)
    db = DocBin()
    counter = 0
    try:
        while tup != 'eoq':
            db.add(tup)
            if len(db) >= 500:
                db.to_disk('D:\eeeeee\Downloads\Spring2022\IE\curatedCorps\curated_corpus_group' + str(size) + '-' + str(counter) + '.spacy')
                counter += 1
                db = DocBin()
            tup = inq.get(block=True)
        if len(db) > 0:
            db.to_disk('D:\eeeeee\Downloads\Spring2022\IE\curatedCorps\curated_corpus_group' + str(size) + '-' + str(
                counter) + '.spacy')
    except KeyboardInterrupt:
        if len(db) > 0:
            db.to_disk('D:\eeeeee\Downloads\Spring2022\IE\curatedCorps\curated_corpus_group' + str(size) + '-' + str(
                counter) + '.spacy')
    print('Exiting docReader')



if __name__ == '__main__':
    spac = spacy.load('en_core_web_sm')


    dbaLock = mp.Lock()
    procs = []
    inds = list(range(1, 73374))
    procount = 10
    dbPerProc = math.floor(len(inds) / procount + 1)
    queues = []
    for i in range(13):
        queues.append(Queue())
    #try:
    rprocs = []
    for i in range(13):
        r = mp.Process(target=docReader, args=(queues[i], i))
        r.start()
        rprocs.append(r)
    for i in range(0, procount):
        p = mp.Process(target=docSender, args=(inds[i*dbPerProc:(i+1)*dbPerProc], spac, queues))
        p.start()
        procs.append(p)

    print('waiting for senders')
    mp.connection.wait(x.sentinel for x in procs)
    print('senders finished')
    for q in queues:
        q.put('eoq')
    print('waiting for readers')
    mp.connection.wait(reader.sentinel for reader in rprocs)
    #print('writing to disk')
    #for i in range(len(docBinArr)):
    #    docBinArr[i].to_disk('D:\eeeeee\Downloads\Spring2022\IE\curatedCorps\curated_corpus_group' + str(i) + '.spacy')

    print('Done')

