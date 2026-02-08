"""
RAG (Retrieval-Augmented Generation) engine.
Generates answers with citations based on retrieved context.
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class RAGEngine:
    """RAG engine for question answering with citations."""
    
    def __init__(self, retriever, llm_client=None):
        """
        Initialize RAG engine.
        
        Args:
            retriever: Retriever for finding relevant context
            llm_client: Optional LLM client for answer generation
        """
        self.retriever = retriever
        self.llm_client = llm_client
        
    def answer_question(self, question: str, principal: str,
                       top_k: int = 5,
                       filters: Optional[Dict[str, Any]] = None,
                       include_citations: bool = True) -> Dict[str, Any]:
        """
        Answer a question using RAG.
        
        Args:
            question: Question to answer
            principal: User making the request
            top_k: Number of context chunks to retrieve
            filters: Optional filters for retrieval
            include_citations: Whether to include citations
            
        Returns:
            Dictionary with answer and citations
        """
        # Retrieve relevant context
        search_results = self.retriever.search(
            query=question,
            principal=principal,
            top_k=top_k,
            filters=filters
        )
        
        if not search_results:
            return {
                "question": question,
                "answer": "I couldn't find any relevant information to answer this question.",
                "citations": [],
                "confidence": 0.0
            }
            
        # Generate answer
        if self.llm_client:
            answer = self._generate_answer_with_llm(question, search_results)
        else:
            answer = self._generate_answer_extractive(question, search_results)
            
        # Format response
        response = {
            "question": question,
            "answer": answer["text"],
            "confidence": answer.get("confidence", 0.8)
        }
        
        if include_citations:
            response["citations"] = self._format_citations(search_results)
            response["sources"] = self._format_sources(search_results)
            
        return response
        
    def _generate_answer_with_llm(self, question: str, 
                                  context_results: List[Dict]) -> Dict[str, Any]:
        """Generate answer using LLM."""
        # Build context from search results
        context_parts = []
        for i, result in enumerate(context_results):
            context_parts.append(f"[{i+1}] {result['text']}")
            
        context = "\n\n".join(context_parts)
        
        # Build prompt
        prompt = f"""Answer the following question based on the provided context. 
Include citation numbers [1], [2], etc. when referencing information from the context.

Context:
{context}

Question: {question}

Answer:"""
        
        try:
            # Call LLM (placeholder for actual implementation)
            # In production, this would call OpenAI, Anthropic, or local LLM
            if hasattr(self.llm_client, 'chat'):
                response = self.llm_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that answers questions based on provided context."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                answer_text = response.choices[0].message.content
            else:
                # Fallback to extractive answer
                return self._generate_answer_extractive(question, context_results)
                
            return {
                "text": answer_text,
                "confidence": 0.9,
                "method": "generative"
            }
            
        except Exception as e:
            logger.error(f"LLM answer generation failed: {e}")
            # Fallback to extractive answer
            return self._generate_answer_extractive(question, context_results)
            
    def _generate_answer_extractive(self, question: str, 
                                    context_results: List[Dict]) -> Dict[str, Any]:
        """Generate extractive answer from top result."""
        if not context_results:
            return {
                "text": "No relevant information found.",
                "confidence": 0.0,
                "method": "extractive"
            }
            
        # Use the top result as the answer
        top_result = context_results[0]
        
        answer_text = f"Based on the retrieved information: {top_result['text']}"
        
        return {
            "text": answer_text,
            "confidence": 0.7,
            "method": "extractive"
        }
        
    def _format_citations(self, results: List[Dict]) -> List[Dict[str, Any]]:
        """Format citations from search results."""
        citations = []
        
        for i, result in enumerate(results):
            citation = {
                "index": i + 1,
                "bucket": result["bucket"],
                "key": result["key"],
                "version_id": result.get("version_id"),
                "start_offset": result["start_offset"],
                "end_offset": result["end_offset"],
                "citation_string": result["citation"],
                "score": result["score"]
            }
            citations.append(citation)
            
        return citations
        
    def _format_sources(self, results: List[Dict]) -> List[str]:
        """Format source list from search results."""
        sources = []
        seen_objects = set()
        
        for result in results:
            object_key = f"{result['bucket']}/{result['key']}"
            if object_key not in seen_objects:
                sources.append(object_key)
                seen_objects.add(object_key)
                
        return sources
        
    def batch_answer(self, questions: List[str], principal: str,
                    **kwargs) -> List[Dict[str, Any]]:
        """
        Answer multiple questions in batch.
        
        Args:
            questions: List of questions
            principal: User making the request
            **kwargs: Additional arguments passed to answer_question
            
        Returns:
            List of answer dictionaries
        """
        answers = []
        for question in questions:
            answer = self.answer_question(question, principal, **kwargs)
            answers.append(answer)
        return answers
