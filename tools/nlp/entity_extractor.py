"""NEXUS AI Agent - Entity Extractor"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Entity:
    """Extracted entity"""
    text: str
    label: str
    start: int
    end: int
    confidence: float = 1.0


@dataclass
class ExtractionResult:
    """Entity extraction result"""
    text: str
    entities: List[Entity] = field(default_factory=list)
    entity_counts: Dict[str, int] = field(default_factory=dict)


class EntityExtractor:
    """Extract named entities from text"""

    def __init__(self):
        # Regex patterns for common entities
        self._patterns = {
            'EMAIL': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'URL': r'https?://[^\s]+|www\.[^\s]+',
            'PHONE': r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
            'DATE': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b',
            'TIME': r'\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\b',
            'MONEY': r'\$\d+(?:,\d{3})*(?:\.\d{2})?|\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|USD|EUR|GBP)\b',
            'PERCENTAGE': r'\b\d+(?:\.\d+)?%\b',
            'IP_ADDRESS': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'CREDIT_CARD': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            'SSN': r'\b\d{3}-\d{2}-\d{4}\b',
            'HASHTAG': r'#\w+',
            'MENTION': r'@\w+',
        }

        # Common titles for person detection
        self._titles = ['Mr', 'Mrs', 'Ms', 'Miss', 'Dr', 'Prof', 'Sir', 'Lord', 'Lady']

    def extract(self, text: str) -> ExtractionResult:
        """
        Extract entities from text

        Args:
            text: Input text

        Returns:
            ExtractionResult object
        """
        result = ExtractionResult(text=text)

        # Extract pattern-based entities
        for label, pattern in self._patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                result.entities.append(Entity(
                    text=match.group(),
                    label=label,
                    start=match.start(),
                    end=match.end()
                ))

        # Extract potential person names (simple heuristic)
        person_entities = self._extract_persons(text)
        result.entities.extend(person_entities)

        # Extract potential organizations (simple heuristic)
        org_entities = self._extract_organizations(text)
        result.entities.extend(org_entities)

        # Count entities by type
        for entity in result.entities:
            result.entity_counts[entity.label] = result.entity_counts.get(entity.label, 0) + 1

        # Sort by position
        result.entities.sort(key=lambda e: e.start)

        return result

    def _extract_persons(self, text: str) -> List[Entity]:
        """Extract person names"""
        entities = []

        # Pattern for names with titles
        title_pattern = r'\b(' + '|'.join(self._titles) + r')\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        for match in re.finditer(title_pattern, text):
            entities.append(Entity(
                text=match.group(),
                label='PERSON',
                start=match.start(),
                end=match.end()
            ))

        # Pattern for capitalized word sequences (potential names)
        name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
        for match in re.finditer(name_pattern, text):
            # Skip if already captured or if it's at sentence start
            if match.start() > 0 and text[match.start() - 1] not in '.!?\n':
                words = match.group().split()
                if len(words) >= 2 and len(words) <= 4:
                    entities.append(Entity(
                        text=match.group(),
                        label='PERSON',
                        start=match.start(),
                        end=match.end(),
                        confidence=0.7
                    ))

        return entities

    def _extract_organizations(self, text: str) -> List[Entity]:
        """Extract organization names"""
        entities = []

        # Common organization suffixes
        org_suffixes = [
            'Inc', 'Corp', 'LLC', 'Ltd', 'Company', 'Co', 'Corporation',
            'Foundation', 'Institute', 'University', 'College', 'Association',
            'Organization', 'Agency', 'Department', 'Ministry'
        ]

        pattern = r'\b([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*)\s+(' + '|'.join(org_suffixes) + r')\.?\b'
        for match in re.finditer(pattern, text):
            entities.append(Entity(
                text=match.group(),
                label='ORGANIZATION',
                start=match.start(),
                end=match.end()
            ))

        return entities

    def extract_type(self, text: str, entity_type: str) -> List[str]:
        """
        Extract specific entity type

        Args:
            text: Input text
            entity_type: Type to extract

        Returns:
            List of entity strings
        """
        result = self.extract(text)
        return [e.text for e in result.entities if e.label == entity_type.upper()]

    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses"""
        return self.extract_type(text, 'EMAIL')

    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs"""
        return self.extract_type(text, 'URL')

    def extract_phones(self, text: str) -> List[str]:
        """Extract phone numbers"""
        return self.extract_type(text, 'PHONE')

    def extract_dates(self, text: str) -> List[str]:
        """Extract dates"""
        return self.extract_type(text, 'DATE')

    def extract_money(self, text: str) -> List[str]:
        """Extract monetary values"""
        return self.extract_type(text, 'MONEY')

    def extract_custom(self, text: str, pattern: str, label: str) -> List[Entity]:
        """
        Extract entities with custom pattern

        Args:
            text: Input text
            pattern: Regex pattern
            label: Entity label

        Returns:
            List of entities
        """
        entities = []
        for match in re.finditer(pattern, text):
            entities.append(Entity(
                text=match.group(),
                label=label,
                start=match.start(),
                end=match.end()
            ))
        return entities

    def add_pattern(self, label: str, pattern: str) -> None:
        """Add custom entity pattern"""
        self._patterns[label.upper()] = pattern

    def mask_entities(
        self,
        text: str,
        entity_types: Optional[List[str]] = None,
        mask: str = '[REDACTED]'
    ) -> str:
        """
        Mask entities in text

        Args:
            text: Input text
            entity_types: Types to mask (None = all)
            mask: Replacement string

        Returns:
            Text with masked entities
        """
        result = self.extract(text)

        # Sort by position descending to replace from end
        entities = sorted(result.entities, key=lambda e: e.start, reverse=True)

        masked_text = text
        for entity in entities:
            if entity_types is None or entity.label in [t.upper() for t in entity_types]:
                masked_text = masked_text[:entity.start] + mask + masked_text[entity.end:]

        return masked_text

    def highlight_entities(
        self,
        text: str,
        entity_types: Optional[List[str]] = None
    ) -> str:
        """
        Highlight entities in text with markers

        Args:
            text: Input text
            entity_types: Types to highlight

        Returns:
            Text with highlighted entities
        """
        result = self.extract(text)

        entities = sorted(result.entities, key=lambda e: e.start, reverse=True)

        highlighted = text
        for entity in entities:
            if entity_types is None or entity.label in [t.upper() for t in entity_types]:
                highlighted = (
                    highlighted[:entity.start] +
                    f'[{entity.label}:{entity.text}]' +
                    highlighted[entity.end:]
                )

        return highlighted

