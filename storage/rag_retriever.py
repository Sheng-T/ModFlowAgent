import os
from typing import List

from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_community.document_loaders import UnstructuredMarkdownLoader

# from langchain.text_splitter import MarkdownHeaderTextSplitter
# from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from sentence_transformers import CrossEncoder


import torch

import logging

from configs import embedding_args, llm_model_path, OTHER_PATH

logging.getLogger("transformers").setLevel(logging.ERROR)

class HybridRetriever:
    """
    BM25 + Vector Hybrid Retriever
    """

    def __init__(self, vector_retriever, bm25_retriever):
        self.vector = vector_retriever
        self.bm25 = bm25_retriever

    def invoke(self, query):

        docs1 = self.vector.invoke(query)
        docs2 = self.bm25.invoke(query)

        seen = set()
        merged = []

        for d in docs1 + docs2:
            key = d.page_content
            if key not in seen:
                merged.append(d)
                seen.add(key)

        return merged

def get_embedding_device():
    device_config = str(embedding_args.get('device', '')).lower()
    if device_config in ['cpu'] or 'cuda' in device_config:
        return device_config
    if device_config == 'auto':
        return 'cuda' if torch.cuda.is_available() else 'cpu'

    return 'cpu'

class EnhancedMDRAG:

    def __init__(self, doc_path: str, llm=None, cache_dir=None):

        self.doc_path = doc_path
        self.llm = llm
        self._cache_dir = cache_dir

        device = get_embedding_device()

        # print(f'use device {device}')

        # embedding
        self.embeddings = HuggingFaceEmbeddings(
            model_name=llm_model_path['embedding'],
            model_kwargs={
                'device': device
            }
        )

        # reranker
        self.reranker = CrossEncoder(
            model_name_or_path=llm_model_path['reranker'],
            device=device
        )

        self.retriever = self._prepare_retriever()

    def _prepare_retriever(self):

        if self._cache_dir:
            db_dir = self._cache_dir
        else:
            # 保留原有兜底逻辑
            base_name = os.path.basename(self.doc_path).split('_')[0]
            db_dir = os.path.join(OTHER_PATH['db_dir'], base_name)

        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3")
        ]

        header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on
        )

        child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", " ", ""]
        )

        final_docs = []

        loader = UnstructuredMarkdownLoader(self.doc_path)
        raw_data = loader.load()

        header_splits = header_splitter.split_text(raw_data[0].page_content)

        for i, parent in enumerate(header_splits):

            children = child_splitter.split_text(parent.page_content)

            for child_content in children:
                # 文本有效性检查：过滤空白和无意义内容
                cleaned_content = child_content.strip()
                
                # 跳过空文本或过短文本（少于10个字符）
                if not cleaned_content or len(cleaned_content) < 10:
                    continue
                
                # 跳过只包含特殊符号的文本
                if all(c in ' \n\t\r|—–-_*#[](){}' for c in cleaned_content):
                    continue

                new_doc = Document(
                    page_content=cleaned_content,
                    metadata={
                        **parent.metadata,
                        "parent_context": parent.page_content,
                        "doc_id": i
                    }
                )

                final_docs.append(new_doc)

        # vector db
        if os.path.exists(db_dir) and os.listdir(db_dir):

            vector_db = Chroma(
                persist_directory=db_dir,
                embedding_function=self.embeddings
            )

        else:

            vector_db = Chroma.from_documents(
                documents=final_docs,
                embedding=self.embeddings,
                persist_directory=db_dir
            )

        vector_retriever = vector_db.as_retriever(search_kwargs={"k": 12})

        # bm25
        bm25_retriever = BM25Retriever.from_documents(final_docs)
        bm25_retriever.k = 12

        hybrid = HybridRetriever(
            vector_retriever,
            bm25_retriever
        )

        return hybrid

    def expand_query(self, query: str) -> List[str]:

        if self.llm is None:
            return [query]

        prompt = f"""
        Rewrite the following query into 3 distinct search queries aimed at retrieving technical documentation for bioinformatics tools. 
        Return ONLY the queries, one per line, without numbering or extra text.

        Original query: {query}
        """

        result = self.llm.invoke(prompt)

        queries = [query]

        for line in result.split("\n"):

            line = line.strip()

            if len(line) > 3:
                queries.append(line)

        return list(set(queries))

    def rerank(self, query: str, docs: List[Document]):

        if len(docs) == 0:
            return docs

        pairs = [(query, d.page_content) for d in docs]

        scores = self.reranker.predict(pairs)

        ranked = sorted(
            zip(scores, docs),
            key=lambda x: x[0],
            reverse=True
        )

        return [d for _, d in ranked[:6]]

    def search(self, query: str):
        # 1 query expansion
        queries = self.expand_query(query)

        # 2 hybrid retrieval
        docs = []
        for q in queries:
            docs.extend(self.retriever.invoke(q))

        # 去重
        seen = set()
        unique_docs = []
        for d in docs:
            key = d.page_content
            if key not in seen:
                unique_docs.append(d)
                seen.add(key)

        # 3 rerank
        reranked_docs = self.rerank(query, unique_docs)

        # 4 核心修复：丢弃庞大的 parent_context，只用当前切片，并注入 Header 导航
        context_parts = []
        for doc in reranked_docs:
            # 提取所在的标题层级 (例如: "samtools view > OPTIONS")
            headers = []
            for i in range(1, 4):
                h_key = f"Header {i}"
                if h_key in doc.metadata:
                    headers.append(doc.metadata[h_key])

            header_path = " > ".join(headers) if headers else "文档片段"

            # 组合上下文：[导航路径] + 具体切片内容
            chunk_text = f"【来源: {header_path}】\n{doc.page_content}"
            context_parts.append(chunk_text)

        # 返回 Top 5 的相关切片 (10 * 500 chunk_size ≈ 5000 tokens，极度安全)
        return "\n\n---\n\n".join(context_parts[:10])