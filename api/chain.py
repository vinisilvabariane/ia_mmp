import re

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_groq import ChatGroq

from config import LLM_MODEL, RETRIEVER_K, SYSTEM_PROMPT
from retriever import build_retriever, format_documents


def _clean_response(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def build_chain():
    retriever = build_retriever(RETRIEVER_K)
    llm = ChatGroq(model_name=LLM_MODEL, temperature=0)
    prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)

    return (
        {
            "context": RunnableLambda(retriever.invoke) | RunnableLambda(format_documents),
            "question": RunnablePassthrough(),
            "student_metrics": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
        | RunnableLambda(_clean_response)
    )


def ask(question: str, student_metrics: dict[str, any]) -> str:
    return build_chain().invoke({
        "question": question,
        "student_metrics": student_metrics
    })
