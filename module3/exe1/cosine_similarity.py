"""Cosine similarity across every phrase in phrases.md.

scikit-learn turns each phrase into a numeric TF-IDF vector, then
cosine_similarity scores every pair of those vectors.
"""

from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

PHRASES_PATH = Path(__file__).with_name("phrases.md")


def load_phrases(path: Path) -> list[str]:
    # Keep only markdown bullets; headings are labels, not phrases.
    phrases = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("- "):
            phrases.append(line[2:].strip())
    return phrases


def main() -> None:
    phrases = load_phrases(PHRASES_PATH)
    # TF-IDF weights words by how distinctive they are across the phrase set.
    vectors = TfidfVectorizer().fit_transform(phrases)
    # Each cell is the cosine similarity between two phrase vectors, from 0 to 1.
    matrix = cosine_similarity(vectors)

    for index, phrase in enumerate(phrases):
        print(f"[{index}] {phrase}")

    print()
    # Print each unordered pair once; the matrix is symmetric.
    for i in range(len(phrases)):
        for j in range(i + 1, len(phrases)):
            print(f"{i} vs {j}: {matrix[i, j]:.4f}")


if __name__ == "__main__":
    main()
