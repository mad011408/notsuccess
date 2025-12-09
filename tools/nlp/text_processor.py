"""NEXUS AI Agent - Text Processor"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class TextStats:
    """Text statistics"""
    char_count: int = 0
    word_count: int = 0
    sentence_count: int = 0
    paragraph_count: int = 0
    avg_word_length: float = 0.0
    avg_sentence_length: float = 0.0
    unique_words: int = 0
    lexical_diversity: float = 0.0


@dataclass
class TokenizedText:
    """Tokenized text"""
    tokens: List[str] = field(default_factory=list)
    sentences: List[str] = field(default_factory=list)
    paragraphs: List[str] = field(default_factory=list)


class TextProcessor:
    """Process and analyze text"""

    def __init__(self):
        self._stopwords = set([
            'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were',
            'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
            'she', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your',
            'his', 'her', 'our', 'their', 'what', 'which', 'who', 'whom', 'when',
            'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more',
            'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
            'same', 'so', 'than', 'too', 'very', 'just', 'can', 'as'
        ])

    def tokenize(self, text: str) -> TokenizedText:
        """
        Tokenize text into words, sentences, and paragraphs

        Args:
            text: Input text

        Returns:
            TokenizedText object
        """
        result = TokenizedText()

        # Paragraphs
        result.paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        # Sentences
        sentence_pattern = r'(?<=[.!?])\s+'
        result.sentences = [s.strip() for s in re.split(sentence_pattern, text) if s.strip()]

        # Words
        word_pattern = r'\b\w+\b'
        result.tokens = re.findall(word_pattern, text.lower())

        return result

    def get_stats(self, text: str) -> TextStats:
        """
        Get text statistics

        Args:
            text: Input text

        Returns:
            TextStats object
        """
        tokenized = self.tokenize(text)

        stats = TextStats(
            char_count=len(text),
            word_count=len(tokenized.tokens),
            sentence_count=len(tokenized.sentences),
            paragraph_count=len(tokenized.paragraphs)
        )

        if tokenized.tokens:
            stats.avg_word_length = sum(len(w) for w in tokenized.tokens) / len(tokenized.tokens)
            stats.unique_words = len(set(tokenized.tokens))
            stats.lexical_diversity = stats.unique_words / stats.word_count

        if tokenized.sentences:
            stats.avg_sentence_length = stats.word_count / stats.sentence_count

        return stats

    def clean(
        self,
        text: str,
        lowercase: bool = True,
        remove_punctuation: bool = True,
        remove_numbers: bool = False,
        remove_urls: bool = True,
        remove_emails: bool = True,
        remove_extra_whitespace: bool = True
    ) -> str:
        """
        Clean text

        Args:
            text: Input text
            lowercase: Convert to lowercase
            remove_punctuation: Remove punctuation
            remove_numbers: Remove numbers
            remove_urls: Remove URLs
            remove_emails: Remove email addresses
            remove_extra_whitespace: Normalize whitespace

        Returns:
            Cleaned text
        """
        if remove_urls:
            text = re.sub(r'https?://\S+|www\.\S+', '', text)

        if remove_emails:
            text = re.sub(r'\S+@\S+', '', text)

        if lowercase:
            text = text.lower()

        if remove_numbers:
            text = re.sub(r'\d+', '', text)

        if remove_punctuation:
            text = re.sub(r'[^\w\s]', '', text)

        if remove_extra_whitespace:
            text = re.sub(r'\s+', ' ', text).strip()

        return text

    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """Remove stopwords from tokens"""
        return [t for t in tokens if t.lower() not in self._stopwords]

    def add_stopwords(self, words: List[str]) -> None:
        """Add custom stopwords"""
        self._stopwords.update(w.lower() for w in words)

    def get_word_frequency(
        self,
        text: str,
        top_n: int = 10,
        remove_stopwords: bool = True
    ) -> Dict[str, int]:
        """
        Get word frequency

        Args:
            text: Input text
            top_n: Number of top words to return
            remove_stopwords: Whether to remove stopwords

        Returns:
            Dict of word frequencies
        """
        tokenized = self.tokenize(text)
        tokens = tokenized.tokens

        if remove_stopwords:
            tokens = self.remove_stopwords(tokens)

        from collections import Counter
        counts = Counter(tokens)
        return dict(counts.most_common(top_n))

    def get_ngrams(
        self,
        text: str,
        n: int = 2,
        top_k: int = 10
    ) -> List[tuple]:
        """
        Get n-grams

        Args:
            text: Input text
            n: N-gram size
            top_k: Number of top n-grams to return

        Returns:
            List of n-gram tuples with counts
        """
        tokenized = self.tokenize(text)
        tokens = tokenized.tokens

        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngrams.append(tuple(tokens[i:i + n]))

        from collections import Counter
        counts = Counter(ngrams)
        return counts.most_common(top_k)

    def split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        return self.tokenize(text).sentences

    def split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs"""
        return self.tokenize(text).paragraphs

    def stem(self, word: str) -> str:
        """Simple suffix stemming"""
        suffixes = ['ing', 'ed', 'ly', 'es', 's', 'ment', 'ness', 'tion', 'ation']
        for suffix in suffixes:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                return word[:-len(suffix)]
        return word

    def stem_tokens(self, tokens: List[str]) -> List[str]:
        """Stem list of tokens"""
        return [self.stem(t) for t in tokens]

    def extract_keywords(
        self,
        text: str,
        top_n: int = 10,
        method: str = 'frequency'
    ) -> List[str]:
        """
        Extract keywords from text

        Args:
            text: Input text
            top_n: Number of keywords
            method: Extraction method

        Returns:
            List of keywords
        """
        freq = self.get_word_frequency(text, top_n * 2, remove_stopwords=True)

        # Filter short words
        keywords = [(w, c) for w, c in freq.items() if len(w) > 2]

        return [w for w, _ in sorted(keywords, key=lambda x: -x[1])[:top_n]]

    def readability_score(self, text: str) -> Dict[str, float]:
        """
        Calculate readability scores

        Args:
            text: Input text

        Returns:
            Dict with readability metrics
        """
        stats = self.get_stats(text)

        if stats.sentence_count == 0 or stats.word_count == 0:
            return {"flesch_reading_ease": 0, "flesch_kincaid_grade": 0}

        # Approximate syllable count
        tokenized = self.tokenize(text)
        syllable_count = sum(self._count_syllables(w) for w in tokenized.tokens)

        # Flesch Reading Ease
        fre = 206.835 - 1.015 * (stats.word_count / stats.sentence_count) - \
              84.6 * (syllable_count / stats.word_count)

        # Flesch-Kincaid Grade Level
        fkgl = 0.39 * (stats.word_count / stats.sentence_count) + \
               11.8 * (syllable_count / stats.word_count) - 15.59

        return {
            "flesch_reading_ease": round(fre, 2),
            "flesch_kincaid_grade": round(fkgl, 2)
        }

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word"""
        word = word.lower()
        vowels = 'aeiou'
        count = 0
        prev_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel

        if word.endswith('e'):
            count -= 1

        return max(1, count)

