"""
Монгол латин галиг -> кирилл хөрвүүлэгч  (v0.2)

Жишээ:
    >>> to_cyrillic("Ugui ee, uur yu hiij boloh uu")
    'Үгүй ээ, өөр юу хийж болох уу'

Ажиллах зарчим:
  1. Түгээмэл товчлол, онцгой үгсийг толиос (EXCEPTIONS) шууд авна.
  2. Латин үгийг хэсэглэж, о/ө, у/ү/ө гэх мэт эргэлзээтэй эгшгүүдийн
     бүх боломжит хувилбарыг үүсгэнэ (эгшиг зохицох ёсыг баримтална).
  3. Хувилбар бүрийг бодит Монгол текстээс сурсан загвараар оноо өгч,
     хамгийн өндөр оноотойг сонгоно:
       - үгийн санд байгаа бол их оноо (давтамжаар нь)
       - байхгүй бол тэмдэгтийн n-gram загварын магадлал
  4. "uu", "ruu" зэрэг нөхцөлийг өмнөх үгийн эгшгээр тааруулна.
"""

import math
import os
import re
import sys
from collections import Counter
from itertools import product

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "words.txt")

# ---------------------------------------------------------------------------
# 1. Онцгой үгс, товчлол
# ---------------------------------------------------------------------------
EXCEPTIONS = {
    "yu": "юу",
    "ym": "юм",
    "ymar": "ямар",
    "bn": "байна",
    "bna": "байна",
    "bh": "байх",
    "mongoliin": "монголын",
    "ok": "ок",
}

# Өмнөх үгийн эгшгээс хамаардаг нөхцөл, сул үгс: латин -> (эр, эм)
PARTICLES = {
    "uu": ("уу", "үү"),
    "ruu": ("руу", "рүү"),
    "luu": ("луу", "лүү"),
}

# ---------------------------------------------------------------------------
# 2. Хэсэглэх дүрэм
# ---------------------------------------------------------------------------
# Эргэлзээтэй эгшиг: латин -> (эр үгэнд, [эм үгэнд байж болох хувилбарууд])
AMBIGUOUS = {
    "oo": ("оо", ["өө"]),
    "uu": ("уу", ["үү", "өө"]),
    "o": ("о", ["ө"]),
    "u": ("у", ["ү", "ө"]),
}

MULTI = [
    ("kh", "х"), ("ts", "ц"), ("ch", "ч"), ("sh", "ш"),
    ("yo", "ё"), ("yu", "ю"), ("ya", "я"), ("ye", "е"),
    ("ii", "ий"),
]

SINGLE = {
    "a": "а", "b": "б", "v": "в", "w": "в", "g": "г", "d": "д",
    "e": "э", "j": "ж", "z": "з", "i": "и", "k": "к", "l": "л",
    "m": "м", "n": "н", "p": "п", "r": "р", "s": "с",
    "t": "т", "f": "ф", "h": "х", "x": "х", "c": "ц",
    "y": "ы", "q": "ө",
}

VOWELS = set("aeiouy")
BACK = set("аоуяё")   # эр эгшиг
FRONT = set("эөүе")   # эм эгшиг


def _segment(word):
    """Латин үгийг хэсгүүдэд хуваана.
    Хэсэг бүр нь ('fixed', кирилл) эсвэл ('amb', латин эгшиг)."""
    parts = []
    i = 0
    while i < len(word):
        for lat, cyr in MULTI:
            if word.startswith(lat, i):
                parts.append(("fixed", cyr))
                i += len(lat)
                break
        else:
            for lat in ("oo", "uu", "o", "u"):
                if word.startswith(lat, i):
                    parts.append(("amb", lat))
                    i += len(lat)
                    break
            else:
                ch = word[i]
                if ch == "i" and i > 0 and word[i - 1] in VOWELS:
                    parts.append(("fixed", "й"))
                else:
                    parts.append(("fixed", SINGLE.get(ch, ch)))
                i += 1
    return parts


def _candidates(word):
    """Эгшиг зохицох ёсыг баримталсан бүх кирилл хувилбарыг буцаана."""
    parts = _segment(word)
    fixed = "".join(c for kind, c in parts if kind == "fixed")
    has_back = any(ch in BACK for ch in fixed)
    has_front = any(ch in FRONT for ch in fixed)
    amb = [lat for kind, lat in parts if kind == "amb"]
    if not amb:
        return [fixed]

    options = []
    if not has_front:   # эр үг байж болно
        options.append([AMBIGUOUS[a][0] for a in amb])
    if not has_back:    # эм үг байж болно
        for combo in product(*[AMBIGUOUS[a][1] for a in amb]):
            options.append(list(combo))
    if not options:     # зээлдэх үг гэх мэт холимог тохиолдол
        options.append([AMBIGUOUS[a][0] for a in amb])

    results = []
    for choice in options:
        it = iter(choice)
        results.append("".join(c if kind == "fixed" else next(it) for kind, c in parts))
    return results


# ---------------------------------------------------------------------------
# 3. Загвар: үгийн сан + тэмдэгтийн n-gram
# ---------------------------------------------------------------------------
class Scorer:
    def __init__(self, path=DATA_FILE, n=4):
        self.n = n
        self.freq = Counter()
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                for line in f:
                    w, _, c = line.rstrip("\n").partition("\t")
                    if w:
                        self.freq[w] = int(c or 1)
        self.total = sum(self.freq.values()) or 1
        self.ngrams = Counter()
        self.contexts = Counter()
        for w, c in self.freq.items():
            padded = "^" * (n - 1) + w + "$"
            for i in range(n - 1, len(padded)):
                ctx = padded[i - n + 1:i]
                self.ngrams[ctx + padded[i]] += 1
                self.contexts[ctx] += 1
        self.vocab = len({ch for w in self.freq for ch in w}) + 1

    def ngram_logprob(self, word):
        n = self.n
        padded = "^" * (n - 1) + word + "$"
        lp = 0.0
        for i in range(n - 1, len(padded)):
            ctx = padded[i - n + 1:i]
            num = self.ngrams[ctx + padded[i]] + 0.1
            den = self.contexts[ctx] + 0.1 * self.vocab
            lp += math.log(num / den)
        return lp

    def score(self, word):
        s = self.ngram_logprob(word)
        if word in self.freq:
            s += 20 + math.log(self.freq[word])
        return s

    def best(self, candidates):
        return max(candidates, key=self.score)


_scorer = None


def _get_scorer():
    global _scorer
    if _scorer is None:
        _scorer = Scorer()
    return _scorer


# ---------------------------------------------------------------------------
# 4. Үндсэн функцууд
# ---------------------------------------------------------------------------
def _is_front(cyr_word):
    return any(ch in FRONT for ch in cyr_word)


def _convert_word(word, prev_cyr=None):
    if word in EXCEPTIONS:
        return EXCEPTIONS[word]
    if word in PARTICLES:
        back, front = PARTICLES[word]
        return front if prev_cyr and _is_front(prev_cyr) else back
    return _get_scorer().best(_candidates(word))


def to_cyrillic(text):
    """Бүтэн өгүүлбэрийг хөрвүүлнэ. Цэг таслал, тоо хэвээр үлдэнэ."""
    prev = [None]

    def repl(m):
        word = m.group(0)
        result = _convert_word(word.lower(), prev[0])
        prev[0] = result
        if word.isupper() and len(word) > 1:
            return result.upper()
        if word[0].isupper():
            return result[0].upper() + result[1:]
        return result

    return re.sub(r"[A-Za-z]+", repl, text)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(to_cyrillic(" ".join(sys.argv[1:])))
    else:
        for line in sys.stdin:
            print(to_cyrillic(line.rstrip("\n")))
