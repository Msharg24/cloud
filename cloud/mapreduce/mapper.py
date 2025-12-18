#!/usr/bin/env python3
import sys
import re

def mapper(text):
    """Mapper function with text preprocessing"""
    word_count = []
    # Expand contractions
    
    # Lowercase and remove punctuation
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    words = text.split()
    for word in words:
        if word:
            word_count.append((word, 1))
    return word_count

# Read from stdin and apply mapper
for line in sys.stdin:
    line = line.strip()
    if line:
        # Apply mapper function to the line
        mapped_results = mapper(line)
        # Output in Hadoop format: word\t1
        for word, count in mapped_results:
            print("{}\t{}".format(word, count))