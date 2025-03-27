import re
from sklearn.feature_extraction.text import TfidfVectorizer
import spacy
import jieba
from collections import Counter, defaultdict


def clean_text(text):
    text = re.sub(r'\[sticker\]|http\S+', '', text)  # 删除表情/链接
    text = re.sub(r'\s+', ' ', text)  # 合并空格
    return text.strip()

corpus = []
# 示例：提取个人特色词汇
with open(r"E:\\Personal Data\\corpus\\corpus.txt", "r", encoding="utf-8") as f:
    line = f.readline()
    while line:
        line = line.strip()
        corpus.extend(phrase for phrase in re.split(r'。|？', line))
        line = (f.readline())

print("corpus length:", len(corpus))

vectorizer = TfidfVectorizer(tokenizer=jieba.lcut, max_features=500)
X = vectorizer.fit_transform(corpus)
top_words = vectorizer.get_feature_names_out()
print(X)
print(top_words)


# 大文件流式读取（避免内存爆炸）
def chunk_reader(file_path, chunk_size=1024*1024):  # 每次1MB
    with open(file_path, 'r', encoding='utf-8') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk

# 分布式分词统计
word_counts = Counter()
for chunk in chunk_reader(r"E:\\Personal Data\\corpus\\corpus.txt"):
    words = jieba.lcut(chunk)  # 中文分词
    word_counts.update(words)
print(word_counts)

for k,v in word_counts.items():
    print(k, v)

# 句式提取（加入依存句法分析）
nlp = spacy.load("zh_core_web_sm")  # 中文模型

def extract_patterns(text):
    doc = nlp(text)
    patterns = []
    for sent in doc.sents:
        # 提取主谓宾结构等
        pattern = " ".join([f"{tok.text}/{tok.dep_}" for tok in sent])
        patterns.append(pattern)
    return patterns

my_pattern = []
for cc in corpus:
    my_pattern.append(extract_patterns(cc))

def extract_phrase_patterns(texts, min_freq=5):
    # 统计连续词序列频率
    phrase_counts = defaultdict(int)

    for text in texts:
        words = list(jieba.cut(text))
        # 提取2-4词长度的连续序列
        for n in range(2, 5):
            for i in range(len(words) - n + 1):
                phrase = "".join(words[i:i + n])
                phrase_counts[phrase] += 1

    # 过滤低频项并排序
    return {k: v for k, v in phrase_counts.items()
            if v >= min_freq and "..." in k or ".." in k}  # 包含省略号的模式


import jieba
from collections import defaultdict
from itertools import combinations
import math
import numpy as np

def auto_phrase_mining(texts, top_n=50):
    # 1. 生成所有候选短语（2-4词组合）
    candidates = defaultdict(int)
    for text in texts:
        words = [w for w in jieba.cut(text) if len(w) > 1]  # 过滤单字
        for n in range(2, 5):
            for i in range(len(words) - n + 1):
                phrase = ''.join(words[i:i + n])
                candidates[phrase] += 1

    # 2. 过滤统计显著短语（PMI算法）
    significant_phrases = []
    for phrase, freq in candidates.copy().items():
        if freq < 5: continue  # 忽略低频
        words = phrase.split('_') if '_' in phrase else list(phrase)
        pmi_score = calculate_pmi(phrase, words, candidates)  # 见下方公式
        if pmi_score > 1.0:  # 阈值可调
            significant_phrases.append((phrase, freq, pmi_score))

    # 3. 按综合评分排序
    return sorted(significant_phrases,
                  key=lambda x: x[1] * x[2],
                  reverse=True)[:top_n]


def calculate_pmi(phrase, words, candidates):
    # PMI(phrase) = log[ P(phrase) / (P(word1)*P(word2)*...) ]
    phrase_prob = candidates[phrase] / sum(candidates.values())
    word_probs = [candidates[w] / sum(candidates.values()) for w in words]
    return math.log(phrase_prob / max(0.00001, np.prod(word_probs)))

print(auto_phrase_mining(corpus))
