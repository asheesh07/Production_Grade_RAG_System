class Retriever:
    def __init__(self,embedder,indexer,top_k,docs_store,score_threshold):
        self.embedder=embedder
        self.indexer=indexer
        self.top_k=top_k
        self.docs_store=docs_store
        self.score_threshold=score_threshold
        
    def retrieve(self,query):
        query_vector=self._embed_query(query)
        
        scores,indices=self._search(query_vector)
        
        docs=self._fetch_docs(indices,scores)
        
        return docs
    
    def _embed_query(self,query):
        embedding=self.embedder.embed([query])
        return np.array(embedding).astype('float32')
    def _search(self,query_vector):
        scores,indices=self.indexer.search(query_vector,self.top_k)
        return scores[0],indices[0]
    def _fetch_docs(self,indices,scores):
        docs=[]
        for idx,score in zip(scores,indices):
            if idx==-1:
                continue
            if self.score_threshold is not None:
                if score<self.score_threshold:
                    continue
            doc=self.docs_store.get_document_by_id(idx)
            if not doc:
                continue
            docs.append(
                Document(page_content=doc['text'],metadata=doc['metadata'])
            )
        return docs