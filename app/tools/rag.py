"""
rag.py —— 基于财务知识语料的轻量检索（TF-IDF + 余弦相似度）

不依赖向量库/嵌入模型（DeepSeek 无 embedding API），改用可解释、可离线运行的
TF-IDF 加权检索：对中文按 bigram、对英文按词切分，再用 idf 加权做余弦排序。
这样 Agent 可以在「会计准则/审计/估值」等知识里检索，回答带依据（RAG 的轻量实现）。
"""
from __future__ import annotations
import math, re, json, os
from collections import Counter

_CORPUS_FILE = os.path.join(os.path.dirname(__file__), "..", "knowledge", "corpus.json")

def _load_corpus():
    with open(_CORPUS_FILE, encoding="utf-8") as f:
        return json.load(f)  # [{title, text}, ...]

def _tokenize(text: str) -> list[str]:
    """中文按字符 bigram（含单字兜底），英文/数字按词，去除噪声。"""
    toks = []
    for seg in re.split(r"[\s\W_]+", text.lower()):
        if not seg: continue
        if re.search(r"[一-鿿]", seg):
            for ch in re.findall(r"[一-鿿]", seg):
                toks.append(ch)
            for i in range(len(seg) - 1):
                if seg[i].isascii() or seg[i+1].isascii(): continue
                toks.append(seg[i] + seg[i+1])
        else:
            for ch in seg: toks.append(ch)
    return toks

class Retrieval:
    def __init__(self):
        self.corpus = _load_corpus()
        self.docs = [(d["title"], d["text"]) for d in self.corpus]
        self.tfs = [Counter(_tokenize(t)) for _, t in self.docs]
        self.df = Counter()
        for tf in self.tfs:
            for w in tf: self.df[w] += 1
        n = len(self.docs)
        self.idf = {w: math.log((n + 1) / (c + 1)) + 1 for w, c in self.df.items()}

    def _vec(self, text: str) -> dict:
        tf = Counter(_tokenize(text))
        return {w: c * self.idf.get(w, 0) for w, c in tf.items()}

    def search(self, query: str, k: int = 3) -> list[dict]:
        if not query.strip(): return []
        qv = self._vec(query)
        qnorm = math.sqrt(sum(v * v for v in qv.values())) or 1
        scored = []
        for i, tf in enumerate(self.tfs):
            dv = {w: c * self.idf.get(w, 0) for w, c in tf.items()}
            dnorm = math.sqrt(sum(v * v for v in dv.values())) or 1
            overlap = set(qv) & set(dv)
            dot = sum(qv[w] * dv[w] for w in overlap)
            scored.append((dot / (qnorm * dnorm), i))
        scored.sort(key=lambda x: -x[0])
        out = []
        for s, i in scored[:k]:
            if s <= 0: continue
            title, text = self.docs[i]
            # 截取最相关片段
            snippet = text[:400]
            out.append({"title": title, "score": round(s, 4), "snippet": snippet})
        return out

RAG = Retrieval()

if __name__ == "__main__":
    for q in ["新收入准则 时点 时段 确认", "IFRS9 预期信用损失 ECL", "DCF 估值 WACC"]:
        print("Q:", q)
        for r in RAG.search(q, 2):
            print("  ", r["score"], r["title"])
