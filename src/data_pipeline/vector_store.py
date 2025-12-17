from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
class Vector_Store:
    def __init__(self,host,port,collection_name,vector_size,distance:Distance=Distance.COSINE):
        self.client=QdrantClient(host=host,port=port)
        self.collection_name=collection_name
        
        self._create_collection(vector_size,distance)
        
    def _create_collection(self,vector_size,distance):
        collections=self.client.get_collections().collections
        
        existing=[c.name for c in collections]
        if self.collection_name not in existing:
            self.client.create_collection(
                collection_nme=self.collection_name,
                vector_config=VectorParams(
                    size=vector_size,
                    distance=distance
                ))
    def upsert_vectors(self,records):
        points=[]
        for rec in records:
            payload=rec['metadata'].copy()
            payload['text']=rec['text']
            points.append(PointStruct(
                id=rec['id'],
                vector=rec['vector'],
                payload=payload))
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
    def search_vectors(self,query_vector,top_k,filter_dict=None):
        
        q_filter=None
        if filter_dict:
            q_filter=Filter(
                must=[
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                    for key,value in filter_dict.items()
                ]
            )
        results=self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            filter=q_filter
        )
        docs=[]
        for r in results:
            metadata=r.payload.copy()
            text=metadata.pop('text',"")
            docs.append(Document(
                page_content=text,
                metadata=metadata
            ))
        return docs