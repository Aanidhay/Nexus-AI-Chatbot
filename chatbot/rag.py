
import os
import json
import math
import re
from collections import Counter, defaultdict

def _tokenize(text):
    # simple whitespace + punctuation tokenizer, lowercase
    text = text.lower()
    tokens = re.findall(r"\w+", text)
    return tokens

def chunk_text(text, max_chars=800):
    # naive chunking by sentences/line breaks preserving words
    paragraphs = re.split(r'\n+', text)
    chunks = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if len(p) <= max_chars:
            chunks.append(p)
        else:
            # split by sentences
            parts = re.split(r'(?<=[.!?]) +', p)
            cur = ""
            for s in parts:
                if len(cur) + len(s) + 1 <= max_chars:
                    cur = (cur + " " + s).strip()
                else:
                    if cur:
                        chunks.append(cur)
                    cur = s
            if cur:
                chunks.append(cur)
    return chunks

class RAGIndex:
    def __init__(self):
        self.chunks = []  # list of strings
        self.tfidf = []   # list of dict token->tfidf
        self.idf = {}     # token->idf
        self.vocab = set()

    def build_from_texts(self, texts):
        # texts: list of strings (documents)
        chunks = []
        for t in texts:
            chunks.extend(chunk_text(t))
        self.chunks = chunks
        # build token counts
        doc_tokens = []
        df = defaultdict(int)
        for ch in chunks:
            toks = _tokenize(ch)
            doc_tokens.append(toks)
            for tok in set(toks):
                df[tok] += 1
            self.vocab.update(toks)
        N = max(1, len(chunks))
        self.idf = {tok: math.log((N+1)/(df[tok]+1)) + 1 for tok in df}
        self.tfidf = []
        for toks in doc_tokens:
            cnt = Counter(toks)
            maxf = max(cnt.values()) if cnt else 1
            vec = {}
            for tok, c in cnt.items():
                tf = c / maxf
                vec[tok] = tf * self.idf.get(tok, 0.0)
            self.tfidf.append(vec)

    def save(self, path):
        data = {"chunks": self.chunks, "idf": self.idf}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def load(self, path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.chunks = data.get("chunks", [])
        self.idf = data.get("idf", {})
        # rebuild tfidf
        self.build_from_texts(self.chunks)

    def _cosine_sim(self, vec1, vec2):
        # vecs are token->weight dicts
        num = 0.0
        for k,v in vec1.items():
            num += v * vec2.get(k, 0.0)
        norm1 = math.sqrt(sum(v*v for v in vec1.values()))
        norm2 = math.sqrt(sum(v*v for v in vec2.values()))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return num / (norm1 * norm2)

    def query(self, q, top_k=3):
        qtokens = _tokenize(q)
        cnt = Counter(qtokens)
        maxf = max(cnt.values()) if cnt else 1
        qvec = {}
        for tok,c in cnt.items():
            tf = c / maxf
            qvec[tok] = tf * self.idf.get(tok, math.log(2))  # fallback idf
        sims = []
        for i, docvec in enumerate(self.tfidf):
            sims.append((i, self._cosine_sim(qvec, docvec)))
        sims.sort(key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in sims[:top_k]:
            results.append({"chunk": self.chunks[idx], "score": score})
        return results

# convenience single-file index
_index = None
_index_path = os.path.join(os.path.dirname(__file__), "rag_index.json")

def get_index():
    global _index
    if _index is None:
        _index = RAGIndex()
        if os.path.exists(_index_path):
            try:
                _index.load(_index_path)
            except Exception:
                pass
    return _index

def build_index_from_texts(texts, save=True):
    idx = get_index()
    idx.build_from_texts(texts)
    if save:
        idx.save(_index_path)
    return idx

def retrieve(query, top_k=3):
    idx = get_index()
    return idx.query(query, top_k=top_k)
