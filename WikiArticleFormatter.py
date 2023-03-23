out = open('Old/unf_corpus.txt', errors='ignore').read()

out = out.replace(' - ', '\n')

o = open('Old/corpus.txt', 'w')
o.write(out)
