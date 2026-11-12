import os
from typing import List, Dict, Any, Optional
import httpx

from backend.app.core.config import settings
from backend.app.schemas.chat import QuestionResponse, CitationSchema
from backend.app.core.logging import logger

class RepositoryQAEngine:
    def __init__(self, commit_sha: str):
        self.commit_sha = commit_sha

    async def answer_question(
        self,
        question: str,
        experience_level: str,
        retrieved_evidence: List[Dict[str, Any]],
        citations: List[CitationSchema],
        repo_name: str
    ) -> QuestionResponse:
        # Check if an LLM is configured
        provider = settings.LLM_PROVIDER.lower()
        if provider == "openai" and settings.OPENAI_API_KEY:
            try:
                answer = await self._call_openai(question, experience_level, retrieved_evidence, repo_name)
                return QuestionResponse(
                    answer=answer,
                    experience_level=experience_level,
                    citations=citations,
                    retrieved_symbols=[c.symbol_name for c in citations if c.symbol_name],
                    mode_used="llm_grounded"
                )
            except Exception as e:
                logger.warning(f"OpenAI call failed ({e}). Falling back to deterministic engine.")

        # Deterministic Grounded Engine (No-LLM mode)
        answer = self._generate_deterministic_answer(
            question=question,
            experience_level=experience_level,
            retrieved_evidence=retrieved_evidence,
            citations=citations,
            repo_name=repo_name
        )
        return QuestionResponse(
            answer=answer,
            experience_level=experience_level,
            citations=citations,
            retrieved_symbols=[c.symbol_name for c in citations if c.symbol_name],
            mode_used="deterministic_engine"
        )

    def _generate_deterministic_answer(
        self,
        question: str,
        experience_level: str,
        retrieved_evidence: List[Dict[str, Any]],
        citations: List[CitationSchema],
        repo_name: str
    ) -> str:
        if not retrieved_evidence:
            return (
                f"No direct code symbols or files matching your query were found in {repo_name} "
                f"at commit `{self.commit_sha[:8]}`. Try querying a specific function name, class, or module."
            )

        q_lower = question.lower()
        top_doc = retrieved_evidence[0]

        symbols_found = [d["name"] for d in retrieved_evidence if d.get("type") == "symbol"]
        files_found = list({d["file_path"] for d in retrieved_evidence})

        if experience_level == "beginner":
            tone = (
                f"In simple terms, looking at {repo_name}, the code relevant to your question is located in: "
                f"`{files_found[0]}`. "
            )
            if symbols_found:
                tone += (
                    f"Specifically, the component named `{symbols_found[0]}` is responsible for this task. "
                    f"You can think of this as the main function that runs when this operation is performed."
                )
        elif experience_level == "senior":
            tone = (
                f"Static architectural grounding for query '{question}' in commit `{self.commit_sha[:8]}`: "
                f"Analysis isolates {len(retrieved_evidence)} structural elements across {len(files_found)} file(s). "
                f"Key symbol `{top_doc.get('name')}` defined at `{top_doc.get('file_path')}` (lines {top_doc.get('start_line')}-{top_doc.get('end_line')}). "
                f"Review afferent dependencies before modifying to preserve decoupling boundaries."
            )
        else:
            tone = (
                f"Based on static analysis of {repo_name} at commit `{self.commit_sha[:8]}`: "
                f"Relevant logic is declared in `{top_doc.get('file_path')}` (lines {top_doc.get('start_line')}-{top_doc.get('end_line')}). "
            )
            if symbols_found:
                tone += f"Identified primary symbol: `{symbols_found[0]}` with related components: {', '.join(symbols_found[1:4]) or 'none'}."

        return tone

    async def _call_openai(
        self,
        question: str,
        experience_level: str,
        evidence: List[Dict[str, Any]],
        repo_name: str
    ) -> str:
        prompt_evidence = "\n".join([
            f"- {e.get('name')} in {e.get('file_path')} (lines {e.get('start_line')}-{e.get('end_line')}): {e.get('snippet')}"
            for e in evidence
        ])
        system_prompt = (
            f"You are RepoVerse AI, explaining repository {repo_name} at commit {self.commit_sha}. "
            f"Ground your answer strictly on the provided evidence. Cite file paths and line ranges. "
            f"Admit uncertainty if something is not in the evidence. "
            f"Target experience level: {experience_level}."
        )
        user_prompt = f"Question: {question}\n\nRetrieved Evidence:\n{prompt_evidence}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.2
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                raise RuntimeError(f"OpenAI API error {resp.status_code}: {resp.text}")
