# generator.py
from typing import List
from langchain.schema import Document


class Generator:
    

    def __init__(
        self,
        llm,
        max_context_tokens: int = 3000,
        temperature: float = 0.0
    ):
        
        self.llm = llm
        self.max_context_tokens = max_context_tokens
        self.temperature = temperature


    def generate(
        self,
        query: str,
        docs: List[Document]
    ) -> str:
        
        context = self._build_context(docs)
        prompt = self._build_prompt(query, context)

        response = self.llm.invoke(prompt)

        return response


    def _build_context(self, docs: List[Document]) -> str:

        context_blocks = []
        total_length = 0

        for i, doc in enumerate(docs):
            block = f"[Document {i+1}]\n{doc.page_content.strip()}\n"
            block_len = len(block)

            if total_length + block_len > self.max_context_tokens:
                break

            context_blocks.append(block)
            total_length += block_len

        return "\n".join(context_blocks)


    def _build_prompt(self, query: str, context: str) -> str:
        
        return f"""
You are a precise and factual AI assistant.

Answer the question ONLY using the context provided below.
If the answer is not contained in the context, say:
"I don't know based on the provided information."

Context:
{context}

Question:
{query}

Answer:
""".strip()
