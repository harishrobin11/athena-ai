from pathlib import Path


class PromptBuilder:

    @staticmethod
    def build(query, documents):
        context = "\n\n".join(
            doc["document"]
            for doc in documents
        )

        return f"""
You are Athena AI.

Use the provided document context as your primary source of information.

Rules:

1. If the document context contains the answer:
   - Use the document information.
   - Prefer document facts over general knowledge.

2. If the document context does NOT contain the answer:
   - Use your general knowledge to help the user.
   - Do not claim the information came from the documents.

3. If the document context partially answers the question:
   - Answer using the document information first.
   - Then supplement with general knowledge when helpful.

4. Never invent document content that is not present.

======================
DOCUMENT CONTEXT
======================

{context}

======================
QUESTION
======================

{query}

======================
ANSWER
======================
"""

    @staticmethod
    def get_sources(documents):

        seen = set()
        sources = []

        for doc in documents:

            metadata = doc["metadata"]

            filename = Path(
                metadata.get(
                    "source",
                    "Unknown"
                )
            ).name

            page = (
                metadata.get(
                    "page",
                    0
                )
                + 1
            )

            score = round(
                doc.get(
                    "hybrid_score",
                    0,
                ),
                3,
            )

            key = (
                filename,
                page,
            )

            if key not in seen:

                seen.add(key)

                sources.append(
                    {
                        "filename": filename,
                        "page": page,
                        "score": score,
                    }
                )

        return sources