import os
from typing import List, Dict, Optional
import json
import time
from openai import OpenAI
import ollama as ollama_client

class LLMService:
    """Handle LLM interactions with multiple providers"""
    
    def __init__(self):
        self.default_llm = os.getenv("DEFAULT_LLM", "ollama")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.openai_client = None
        
        if os.getenv("OPENAI_API_KEY"):
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def generate_answer(
        self,
        query: str,
        contexts: List[Dict],
        model: Optional[str] = None,
        max_tokens: int = 500
    ) -> Dict:
        """
        Generate answer using retrieved contexts
        Returns answer with citations
        """
        # Prepare context
        context_text = "\n\n".join([
            f"[{i+1}] {ctx['text']}" 
            for i, ctx in enumerate(contexts)
        ])
        
        # Create prompt
        prompt = f"""You are a helpful assistant that answers questions based on the provided context.
        
Context:
{context_text}

Question: {query}

Instructions:
1. Answer based ONLY on the provided context
2. If the answer cannot be found in the context, say "I cannot answer this based on the provided documents"
3. Include citation numbers [1], [2], etc. when referencing specific information
4. Be concise and direct

Answer:"""

        start_time = time.time()
        
        # Generate response
        if self.default_llm == "ollama" or not self.openai_client:
            answer_text = self._ollama_generate(prompt, model or "mistral")
        else:
            answer_text = self._openai_generate(prompt, model or "gpt-3.5-turbo")
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Extract citations from answer
        citations = self._extract_citations(answer_text, contexts)
        
        return {
            "answer": answer_text,
            "citations": citations,
            "latency_ms": latency_ms,
            "model": model or self.default_llm,
            "contexts_used": len(contexts)
        }
    
    def _ollama_generate(self, prompt: str, model: str) -> str:
        """Generate using Ollama"""
        try:
            response = ollama_client.generate(
                model=model,
                prompt=prompt
            )
            return response['response']
        except Exception as e:
            print(f"Ollama error: {e}")
            return "Error generating response. Please ensure Ollama is running."
    
    def _openai_generate(self, prompt: str, model: str) -> str:
        """Generate using OpenAI"""
        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI error: {e}")
            return self._ollama_generate(prompt, "mistral")  # Fallback to Ollama
    
    def _extract_citations(self, answer: str, contexts: List[Dict]) -> List[Dict]:
        """Extract citation references from answer"""
        import re
        citations = []
        
        # Find all [n] patterns in answer
        pattern = r'\[(\d+)\]'
        matches = re.findall(pattern, answer)
        
        for match in matches:
            idx = int(match) - 1
            if 0 <= idx < len(contexts):
                ctx = contexts[idx]
                citations.append({
                    "index": idx + 1,
                    "text": ctx['text'][:200] + "...",
                    "document_id": ctx.get('document_id'),
                    "chunk_index": ctx.get('chunk_index')
                })
        
        return citations
    
    def check_answerability(self, query: str, contexts: List[Dict]) -> float:
        """
        Check if query can be answered from contexts
        Returns confidence score (0-1)
        """
        if not contexts:
            return 0.0
        
        # Much more lenient scoring for better results
        query_words = set(query.lower().split())
        context_words = set()
        
        # Check all contexts, not just top 3
        for ctx in contexts:
            context_words.update(ctx['text'].lower().split())
        
        # If ANY query word appears in context, give some confidence
        overlap = len(query_words & context_words) / len(query_words) if query_words else 0
        
        # Boost confidence if we have any contexts at all
        base_confidence = 0.3 if contexts else 0.0
        
        # Combine signals with higher base confidence
        confidence = base_confidence + (overlap * 0.5)
        
        return min(confidence, 1.0)  # Cap at 1.0