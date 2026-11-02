"""Tiny BM25 over the guidance notes.

The corpus is a dozen short notes, so a vector database would be overkill. BM25
also has the advantage that you can see exactly why a note was picked.
"""
import math
import re

TOKEN = re.compile(r"[a-z0-9]+")


def tokens(text):
    return TOKEN.findall(text.lower())


class Guidance:
    def __init__(self, notes, k1=1.4, b=0.75):
        self.notes = notes
        self.docs = [tokens(n["title"] + " " + n["keywords"] + " " + n["text"]) for n in notes]
        self.avg = sum(len(d) for d in self.docs) / len(self.docs)
        self.k1, self.b = k1, b
        df = {}
        for d in self.docs:
            for t in set(d):
                df[t] = df.get(t, 0) + 1
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def search(self, query, k=4):
        q = tokens(query)
        scored = []
        for note, d in zip(self.notes, self.docs):
            s = 0.0
            for t in q:
                if t not in self.idf:
                    continue
                f = d.count(t)
                s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * len(d) / self.avg))
            if s > 0:
                scored.append((s, note))
        scored.sort(key=lambda x: -x[0])
        return [n for _, n in scored[:k]]
