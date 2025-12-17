import torch
class Reranker:
    def __init__(self,model,tokenizer,top_n,device='cpu'):
        self.model=model.to(device)
        self.tokenizer=tokenizer
        self.top_n=top_n
        self.device=device
    def rerank(self,query,documents):
        pairs=[(query,doc.page_content) for doc in documents]
        
        scores=self._score_pairs(pairs)
        
        scored_docs=zip(documents,scores)
        
        scored_docs.sort(key=lambda x:x[1],reverse=True)
        
        reranked_docs=[doc for doc,_ in scored_docs[:self.top_n]]
        
        return reranked_docs
    
    def _score_pairs(self,pairs):
        inputs=self.tokenizer(
            pairs,
            padding=True,
            truncation=True,
            return_tensors='pt'
        ).to(self.device)
        
    
        with torch.no_grad():
            outputs=self.model(**inputs)
        scores=outputs.logits.squeeze().tolist()
        if isinstance(scores, float):
            scores = [scores]
        return scores