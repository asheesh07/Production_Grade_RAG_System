import faiss
class Indexer:
    def __init__(self,dims,index_type,metrics,n_list,m):
        self.dims=dims
        self.index_type=index_type
        self.metrics=metrics
        self.n_list=n_list
        self.m=m
        self.index=self._create_index()
    def _create_index(self):
        if self.metrics=='cosine':
            basic__metrics=faiss.METRIC_INNER_PRODUCT
        else:
            basic__metrics=faiss.METRIC_L2
        if self.index_type=='IVF':
            index=faiss.IndexFlatIP(self.dims) if self.metrics=='cosine' else faiss.IndexFlatL2(self.dims)
        elif self.index_type=='HNSW':
            index=faiss.IndexHNSWFlat(self.dims,32)
            index.hnsw.efConstruction=200
            index.hnsw.efSearch=50
        elif self.index_type=='IVF_PQ':
            quantizer=faiss.IndexFlat(self.dims,basic__metrics)
            index=faiss.IndexIVFPQ(quantizer,self.dims,self.n_list,self.m,8,basic__metrics)
            index.nprobe=10
        else:
            raise ValueError(f"Unsupported index type: {self.index_type}")
        return index
    def train(self,vectors):
        if self.index.is_trained:
            return
        if vectors.shape[0]<self.index.ntotal:
            raise ValueError("Not enough vectors to train the index")
        self.index.train(vectors)
    
    def add  (self,vectors):
        if self.metric == "cosine":
            faiss.normalize_L2(vectors)

        if not self.index.is_trained:
            raise RuntimeError("Index must be trained before adding vectors")

        self.index.add(vectors)
        
    def search(self,query_vectors,top_k):
        if self.metric == "cosine":
            faiss.normalize_L2(query_vectors)

        distances, indices = self.index.search(query_vectors, top_k)
        return distances, indices
    def save(self, path: str):
        faiss.write_index(self.index, path)

    def load(self, path: str):
        self.index = faiss.read_index(path)