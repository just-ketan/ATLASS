"""Phase 7: Conversation Memory workflows."""

from .service import ResearchWorkspaceService


class ConversationAgent:
    """Agent that processes conversations to extract knowledge."""

    def __init__(self, workspace: ResearchWorkspaceService):
        self.workspace = workspace
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            from atlasse.knowledge_engine.paper_understanding.llm_engine import LLMEngine

            self._llm = LLMEngine()
        return self._llm

    def _get_conversation_context(self, user_id: str, conversation_id: str) -> str:
        conversation = self.workspace.store.conversations.get(conversation_id)
        if not conversation or conversation.user_id != user_id:
            raise ValueError("Conversation not found")
        
        context_lines = []
        for msg in conversation.messages:
            context_lines.append(f"{msg.role.capitalize()}: {msg.content}")
        return "\n".join(context_lines)

    def generate_notes(self, user_id: str, conversation_id: str) -> str:
        """Generate summary notes from the conversation."""
        context = self._get_conversation_context(user_id, conversation_id)
        prompt = f"Summarize the key points from this conversation into structured notes:\n{context}\n\nNotes:"
        notes = self.llm.generate(prompt).strip()
        
        conversation = self.workspace.store.conversations.get(conversation_id)
        title = f"Notes: {conversation.title}"
        self.workspace.add_note(user_id, title, notes, project_id=conversation.project_id, paper_id=conversation.paper_id)
        
        return notes

    def extract_insights(self, user_id: str, conversation_id: str) -> list[str]:
        """Extract personal insights and promote to Memory."""
        context = self._get_conversation_context(user_id, conversation_id)
        prompt = f"Extract a comma-separated list of the most important insights or decisions from this conversation:\n{context}\n\nInsights:"
        response = self.llm.generate(prompt).strip()
        
        insights = [i.strip() for i in response.split(",") if i.strip()]
        
        for insight in insights:
            self.workspace.remember(
                user_id,
                content=insight,
                source_type="conversation_insight",
                source_id=conversation_id
            )
            
        return insights

    def generate_follow_ups(self, user_id: str, conversation_id: str) -> list[str]:
        """Generate follow-up questions for tracking."""
        context = self._get_conversation_context(user_id, conversation_id)
        prompt = f"Based on this conversation, suggest 3 follow-up questions to explore further, separated by commas:\n{context}\n\nQuestions:"
        response = self.llm.generate(prompt).strip()
        
        questions = [q.strip() for q in response.split(",") if q.strip()]
        return questions
