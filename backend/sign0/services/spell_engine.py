"""
Sign0 Real-Time Vocabulary & Autocorrect Spell Engine
Trie-based prefix matching and Levenshtein distance correction tailored for ASL fingerspelling.
"""

from typing import List, Dict, Optional, Set


class TrieNode:
    def __init__(self):
        self.children: Dict[str, "TrieNode"] = {}
        self.is_word: bool = False
        self.frequency: int = 0


class SpellEngine:
    """Fast in-memory Trie and Levenshtein spell checker for rapid ASL fingerspelling translation."""

    DEFAULT_VOCABULARY = [
        # Emergency & Clinical
        "HELP", "EMERGENCY", "DOCTOR", "HOSPITAL", "PAIN", "WATER", "MEDICINE", "NURSE",
        "ALLERGY", "DIABETES", "BREATHING", "HEART", "SURGERY", "FEVER", "HEADACHE",
        "PLEASE", "THANK", "YOU", "YES", "NO", "HELLO", "GOODBYE", "SORRY", "STOP",
        "REST", "FOOD", "HUNGRY", "COLD", "HOT", "TIRED", "SICK", "DIZZY",
        # Common Everyday Conversational Words
        "THE", "BE", "TO", "OF", "AND", "A", "IN", "THAT", "HAVE", "I", "IT", "FOR",
        "NOT", "ON", "WITH", "HE", "AS", "YOU", "DO", "AT", "THIS", "BUT", "HIS",
        "BY", "FROM", "THEY", "WE", "SAY", "HER", "SHE", "OR", "AN", "WILL", "MY",
        "ONE", "ALL", "WOULD", "THERE", "THEIR", "WHAT", "SO", "UP", "OUT", "IF",
        "ABOUT", "WHO", "GET", "WHICH", "GO", "ME", "WHEN", "MAKE", "CAN", "LIKE",
        "TIME", "NO", "JUST", "HIM", "KNOW", "TAKE", "PEOPLE", "INTO", "YEAR", "YOUR",
        "GOOD", "SOME", "COULD", "THEM", "SEE", "OTHER", "THAN", "THEN", "NOW", "LOOK",
        "ONLY", "COME", "ITS", "OVER", "THINK", "ALSO", "BACK", "AFTER", "USE", "TWO",
        "HOW", "OUR", "WORK", "FIRST", "WELL", "WAY", "EVEN", "NEW", "WANT", "BECAUSE",
        "ANY", "THESE", "GIVE", "DAY", "MOST", "US", "NAME", "CALL", "SIGN", "LANGUAGE",
        "NICE", "MEET", "FRIEND", "FAMILY", "LOVE", "HAPPY", "WHERE", "WHY", "AGAIN"
    ]

    def __init__(self, vocabulary: Optional[List[str]] = None):
        self.root = TrieNode()
        self.words: Set[str] = set()
        vocab = vocabulary or self.DEFAULT_VOCABULARY
        for word in vocab:
            self.insert(word.upper())

    def insert(self, word: str, frequency: int = 1):
        """Insert a word into the Trie."""
        word = word.upper().strip()
        if not word:
            return
        self.words.add(word)
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_word = True
        node.frequency += frequency

    def get_prefix_completions(self, prefix: str, max_results: int = 5) -> List[str]:
        """Find words that start with the specified prefix (for predictive typing)."""
        prefix = prefix.upper().strip()
        if not prefix:
            return []

        node = self.root
        for char in prefix:
            if char not in node.children:
                # If prefix not found, return fuzzy matches
                return self.suggest_corrections(prefix, max_results=max_results)
            node = node.children[char]

        results: List[str] = []

        def _dfs(current_node: TrieNode, path: str):
            if len(results) >= max_results:
                return
            if current_node.is_word:
                results.append(path)
            for char, next_node in sorted(current_node.children.items()):
                _dfs(next_node, path + char)

        _dfs(node, prefix)
        return results

    def suggest_corrections(self, word: str, max_distance: int = 2, max_results: int = 3) -> List[str]:
        """Suggest closest vocabulary matches using Levenshtein distance."""
        word = word.upper().strip()
        if not word:
            return []
        if word in self.words:
            return [word]

        candidates = []
        for v_word in self.words:
            dist = self._levenshtein(word, v_word)
            if dist <= max_distance:
                candidates.append((dist, v_word))

        candidates.sort(key=lambda x: (x[0], len(x[1])))
        return [w for _, w in candidates[:max_results]]

    @staticmethod
    def _levenshtein(s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return SpellEngine._levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]


spell_engine = SpellEngine()
