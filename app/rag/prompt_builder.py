from pathlib import Path


class PromptBuilder:

    @staticmethod
    def build(query, documents):
        context = "\n\n".join(
            doc.page_content for doc in documents
        )

        return f"""
You are Athena AI.

You are answering questions using the provided documents.

Rules:
1. Answer only using the document context.
2. If the answer is not in the documents, reply:
   "I couldn't find that information in the provided documents."
3. Do not make up information.

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
        """
        Extract filename and page number from retrieved documents.
        """

        sources = []

        for doc in documents:

            metadata = doc.metadata

            filename = Path(
                metadata.get("source", "Unknown")
            ).name

            page = metadata.get("page", 0) + 1

            sources.append({
                "filename": filename,
                "page": page,
            })

        return sources