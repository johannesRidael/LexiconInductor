import math
import multiprocessing

from wiki_dump_reader import Cleaner, iterate
import re
from spacy.tokens import DocBin
import spacy
import torch
import multiprocessing as mp




def formatText(text):
    m = re.search('== See Also ==|== References ==', text, flags=re.IGNORECASE)  # Removes non-text
    if m is not None: text = text[:m.start()]
    text = re.sub("\n==.*==\n", '', text)  # removes titles
    text = re.sub("\[\[[^\]]*\||\[\[|\]\]|\{\{.*?\}\}|'''|File:.*\n|<.*>|\*", '', text)
    # removes remnants of images, bullet points, references, links, and remarks/comments ( for the most part)
    text = re.sub("\{[^\}]*\}", "", text)  # finishes removing some weird artifacts
    return text.strip()  # removes like, 20 lines of empty from the start cause by previous removes

def dealWithTextArr(arr, groupnum, nlp):
    docs = DocBin()
    for t in arr:
        ct = formatText(t)
        docs.add(nlp(ct))

    docs.to_disk('D:\eeeeee\Downloads\Spring2022\IE\corps\corpus_group' + str(groupnum) + '.spacy')
    print('Group ', groupnum, ' saved')


if __name__ == '__main__':
    print('using gpu: ', spacy.prefer_gpu())
    mp.set_start_method('spawn')
    nlp = spacy.load('en_core_web_sm')
    cleaner = Cleaner()
    i = 0
    group = 1
    tarr = []
    for title, text in iterate('D:\eeeeee\Downloads\Spring2022\IE\enwiki-20211020-pages-articles-multistream.xml'):
        #print(text)
        #text = cleaner.clean_text(text)
        if text[:9] != '#REDIRECT' and text[:9] != '#TEMPLATE':
            #cleaned_text, links = cleaner.build_links(text)
            #print(text)
            #cleaned_text = formatText(text)
            #print(cleaned_text)
            #print('*******************************************')
            #print(links)
            i += 1
            #docs.add(nlp(text))
            tarr.append(text)
            if i % 100 == 0:
                # print('starting process ', group)
                if group > 41272:
                    p = multiprocessing.Process(target=dealWithTextArr, args=(tarr, group, nlp))
                    p.start()
                group += 1
                tarr = []

    dealWithTextArr(tarr, group, nlp)


