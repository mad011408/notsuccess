"""NEXUS AI Agent - Sentiment Analyzer"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SentimentResult:
    """Sentiment analysis result"""
    text: str
    sentiment: str  # positive, negative, neutral
    score: float  # -1 to 1
    confidence: float  # 0 to 1
    positive_words: List[str]
    negative_words: List[str]


class SentimentAnalyzer:
    """Analyze text sentiment"""

    def __init__(self):
        # Basic sentiment lexicon
        self._positive_words = set([
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'awesome', 'outstanding', 'brilliant', 'superb', 'love', 'happy',
            'joy', 'delightful', 'pleasant', 'beautiful', 'perfect', 'best',
            'better', 'nice', 'fine', 'positive', 'success', 'successful',
            'win', 'winner', 'winning', 'fortunate', 'lucky', 'glad', 'pleased',
            'satisfied', 'enjoy', 'enjoyable', 'fun', 'exciting', 'excited',
            'thrilled', 'enthusiastic', 'optimistic', 'hopeful', 'grateful',
            'thankful', 'appreciate', 'impressive', 'remarkable', 'exceptional'
        ])

        self._negative_words = set([
            'bad', 'terrible', 'awful', 'horrible', 'poor', 'worst', 'hate',
            'dislike', 'sad', 'unhappy', 'disappointed', 'disappointing',
            'failure', 'fail', 'failed', 'failing', 'wrong', 'error', 'problem',
            'issue', 'bug', 'broken', 'damage', 'damaged', 'ugly', 'nasty',
            'negative', 'loss', 'lose', 'losing', 'unfortunate', 'unlucky',
            'angry', 'annoyed', 'frustrated', 'annoying', 'frustrating', 'boring',
            'bored', 'dull', 'painful', 'pain', 'hurt', 'harmful', 'dangerous',
            'risk', 'risky', 'fear', 'afraid', 'scared', 'worried', 'anxious',
            'stress', 'stressful', 'difficult', 'hard', 'complicated', 'confusing'
        ])

        self._intensifiers = {
            'very': 1.5,
            'extremely': 2.0,
            'really': 1.5,
            'quite': 1.2,
            'somewhat': 0.8,
            'slightly': 0.5,
            'highly': 1.5,
            'incredibly': 2.0,
            'absolutely': 2.0,
            'totally': 1.5
        }

        self._negations = set([
            'not', 'no', 'never', 'neither', 'nobody', 'nothing', 'nowhere',
            "don't", "doesn't", "didn't", "won't", "wouldn't", "couldn't",
            "shouldn't", "can't", "cannot", "isn't", "aren't", "wasn't", "weren't"
        ])

    def analyze(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of text

        Args:
            text: Input text

        Returns:
            SentimentResult object
        """
        import re
        words = re.findall(r'\b\w+\b', text.lower())

        positive_found = []
        negative_found = []
        score = 0.0
        word_count = 0

        i = 0
        while i < len(words):
            word = words[i]

            # Check for intensifiers
            multiplier = 1.0
            if i > 0 and words[i - 1] in self._intensifiers:
                multiplier = self._intensifiers[words[i - 1]]

            # Check for negation
            negated = False
            if i > 0 and words[i - 1] in self._negations:
                negated = True
            if i > 1 and words[i - 2] in self._negations:
                negated = True

            if word in self._positive_words:
                if negated:
                    score -= 1.0 * multiplier
                    negative_found.append(word)
                else:
                    score += 1.0 * multiplier
                    positive_found.append(word)
                word_count += 1

            elif word in self._negative_words:
                if negated:
                    score += 0.5 * multiplier  # Negated negative is weakly positive
                    positive_found.append(word)
                else:
                    score -= 1.0 * multiplier
                    negative_found.append(word)
                word_count += 1

            i += 1

        # Normalize score
        if word_count > 0:
            normalized_score = score / word_count
            normalized_score = max(-1, min(1, normalized_score))
        else:
            normalized_score = 0.0

        # Determine sentiment label
        if normalized_score > 0.1:
            sentiment = 'positive'
        elif normalized_score < -0.1:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'

        # Calculate confidence
        confidence = min(1.0, abs(normalized_score) + (word_count / len(words)) * 0.5) if words else 0.0

        return SentimentResult(
            text=text,
            sentiment=sentiment,
            score=round(normalized_score, 3),
            confidence=round(confidence, 3),
            positive_words=positive_found,
            negative_words=negative_found
        )

    def analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """Analyze multiple texts"""
        return [self.analyze(text) for text in texts]

    def get_sentiment_distribution(self, texts: List[str]) -> Dict[str, int]:
        """Get sentiment distribution"""
        results = self.analyze_batch(texts)
        distribution = {'positive': 0, 'negative': 0, 'neutral': 0}
        for r in results:
            distribution[r.sentiment] += 1
        return distribution

    def add_positive_words(self, words: List[str]) -> None:
        """Add custom positive words"""
        self._positive_words.update(w.lower() for w in words)

    def add_negative_words(self, words: List[str]) -> None:
        """Add custom negative words"""
        self._negative_words.update(w.lower() for w in words)

    def analyze_aspects(
        self,
        text: str,
        aspects: List[str]
    ) -> Dict[str, SentimentResult]:
        """
        Aspect-based sentiment analysis

        Args:
            text: Input text
            aspects: List of aspects to analyze

        Returns:
            Dict mapping aspects to sentiment results
        """
        sentences = text.split('.')
        results = {}

        for aspect in aspects:
            aspect_lower = aspect.lower()
            relevant_sentences = [
                s for s in sentences
                if aspect_lower in s.lower()
            ]

            if relevant_sentences:
                combined_text = ' '.join(relevant_sentences)
                results[aspect] = self.analyze(combined_text)
            else:
                results[aspect] = SentimentResult(
                    text="",
                    sentiment="neutral",
                    score=0.0,
                    confidence=0.0,
                    positive_words=[],
                    negative_words=[]
                )

        return results

    def get_emotional_tone(self, text: str) -> Dict[str, float]:
        """
        Analyze emotional tone

        Args:
            text: Input text

        Returns:
            Dict of emotion scores
        """
        emotions = {
            'joy': ['happy', 'joy', 'delighted', 'excited', 'cheerful', 'glad', 'pleased'],
            'sadness': ['sad', 'unhappy', 'depressed', 'miserable', 'sorrowful', 'gloomy'],
            'anger': ['angry', 'furious', 'irritated', 'annoyed', 'outraged', 'mad'],
            'fear': ['afraid', 'scared', 'frightened', 'terrified', 'worried', 'anxious'],
            'surprise': ['surprised', 'amazed', 'astonished', 'shocked', 'stunned'],
            'trust': ['trust', 'believe', 'faith', 'confident', 'reliable', 'honest']
        }

        import re
        words = set(re.findall(r'\b\w+\b', text.lower()))

        scores = {}
        for emotion, keywords in emotions.items():
            matches = len(words.intersection(keywords))
            scores[emotion] = round(matches / max(len(words), 1), 3)

        return scores

