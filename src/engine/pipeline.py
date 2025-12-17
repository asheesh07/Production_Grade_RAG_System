class RAGPipeline:
    def __init__(self,loader,cleaner,chunker,embedder,indexer,retriver,reranker,scorenormalizer,generator):
        self.loader=loader
        self.cleaner=cleaner
        self.chunker=chunker
        self.embedder=embedder
        self.indexer=indexer
        self.retriver=retriver
        self.reranker=reranker
        self.scorenormalizer=scorenormalizer
        self.generator=generator
        
    async def run(self,query):
        docs=self.retriver.retrieve(query)
        
        if not docs:
            logger.warning("No documents retrieved for the query.")
            return "I don't know based on the provided information."
        
        reranked_docs=self.reranker.rerank(query,docs)
        
        answer=self.generator.generate(query,reranked_docs)
        
        logging.info("Generated answer for the query.")
        return answer
    async def ingest(self,file):
        
        raw_data=await self.loader.load(file)
        
        cleaned_data=self.cleaner.clean(raw_data)
        
        chunks=self.chunker.chunk(cleaned_data)
        
        vectors=self.embedder.embed([chunk.page_content for chunk in chunks])
        
        self.indexer.add(vectors)
        
        logging.info(f"Successfully ingested document: {file.filename}")
        
def build_rag_pipeline(settings,cache):
    loader=Loader()
    cleaner=Cleaner()
    chunker=Chunker()
    embedder=Embedder(settings)
    indexer=Indexer(settings)
    retriever=Retriever(embedder,indexer)
    reranker=Reranker(settings)
    score_normalizer=ScoreNormalizer()
    generator=Generator(settings)
    
    return RAGPipeline(
        loader=loader,
        cleaner=cleaner,
        chunker=chunker,
        embedder=embedder,
        indexer=indexer,
        retriever=retriever,
        reranker=reranker,
        score_normalizer=score_normalizer,
        generator=generator,
        cache=cache,
    )