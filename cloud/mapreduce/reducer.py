#!/usr/bin/env python3
import sys

def reducer(word_count_list):
    """Reducer function to aggregate word counts"""
    counts = {}
    for word, count in word_count_list:
        counts[word] = counts.get(word, 0) + count
    return counts

# For Hadoop Streaming, we need to process sorted input
current_word = None
current_count = 0

for line in sys.stdin:
    line = line.strip()
    try:
        word, count = line.split('\t')
        count = int(count)
    except:
        continue

    if word == current_word:
        current_count += count
    else:
        if current_word is not None:
            print("{}\t{}".format(current_word, current_count))
        current_word = word
        current_count = count

if current_word is not None:
    print("{}\t{}".format(current_word, current_count))