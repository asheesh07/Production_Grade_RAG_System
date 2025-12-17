from .cleaning import clean_text
import os
import json
import tiktoken
from langchain import Document
class DocumentPreprocessor:
    def __init__(self,chunk_size=500,chunk_overlap=50,min_chars=50):
        self.chunk_size=chunk_size
        self.chunk_overlap=chunk_overlap
        self.min_chars=min_chars
        self.tokenizer=tiktoken.get_encoding("cl100k_base")
        
    def clean_text(self,text,pages):
        return clean_text(text,pages)
            
                
        
    def chunk_text(self,text,doc_id,title):
        tokens=self.tokenizer.encode(text)
        chunks=[]
        start=0
        chunk_id=0
        
        while start<len(tokens):
            end=start+self.chunk_size
            chunk_tokens=tokens[start:end]
            
            chunk_text=self.tokenizer.decode(chunk_tokens).strip()
            
            if len(chunk_text)>=self.min_chars:
                chunk={
                    "chunk_id":f"{doc_id}_chunk_{chunk_id_:04d}",
                    "doc_id":doc_id,
                    "title":title,
                    "text":chunk_text,
                    "token_count":len(chunk_tokens),
                    "char_count":len(chunk_text),
                    "offset_tokens":(start,end),
                    
                    
                }
            chunk_id+=1
            start+=self.chunk_size - self.chunk_overlap    
                

    def process_document(self,doc):
        raw_text=doc['raw_text']
        title=doc['title']
        doc_id=doc['doc_id']
        clean_text=self.clean_text(raw_text)
        chunks=self.chunk_text(clean_text,doc_id,title)
        return chunks
    def save_chunks(self,chunks,ouput_path):
        os.makedirs(os.path.dirname(ouput_path),exist_ok=True)
        temp_file=ouput_path +".tmp"
        with open(temp_file,'w',encoding='utf-8') as f:
            for ch in chunks:
                f.write(json.dumps(ch,ensure_ascii=False)+'\n')
        os.replace(temp_file,ouput_path)
    
########################################################################################
class CleanDocument:
    def __init__(self,configs):
        self.configs=configs
    def clean(self,docs):
        cleaned_docs=[]
        
        for doc in docs:
            text=doc.page_content()
            
            text=self._normalize_unicode(text)
            text=self._remove_null_chars(text)
            text=self._remove_html_tags(text)
            text=self._hyphenate_words(text)
            text=self._remove_page_numbers(text)
            text=self._standardize_whitespace(text)
            text=self._strip_headers_footers(text)
            
            cleaned_docs.append(
                Document(
                    page_content=text.strip(),
                    metadata=doc.metadata
                )
            )
        return cleaned_docs
    
    def _normalize_unicode(self,text):
        return unicode.normalize("NFKC",text)
    def _remove_null_chars(self,text):
        return text.replace('\x00',"").replace("\x0c","")
    def _remove_html_tags(self,text):
        text = re.sub(r"<script.*?>.*?</script>", "", text, flags=re.DOTALL)
        text = re.sub(r"<style.*?>.*?</style>", "", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", "", text)
        return text
    def _hyphenate_words(self,text):
        return re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)
    def _remove_page_numbers(self,text):
        text = re.sub(r"Page\s+\d+(\s+of\s+\d+)?", "", text, flags=re.IGNORECASE)
        return text
    def _standardize_whitespace(self,text):
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Replace multiple spaces with one
        text = re.sub(r"[ \t]{2,}", " ", text)

        return text.strip()
    def _strip_headers_footers(self,text):
        lines=text.splitlines()
        if len(lines)<=4:
            return text
        header=lines[0]
        footer=lines[-1]
        cleaned_lines=[]
        for line in lines:
            if line.strip()==header.strip():
                continue
            if line.strip()==footer.strip():
                continue
            cleaned_lines.append(line)
        return "\n".join(cleaned_lines)
class ChunkDocument:
    def __init__(self,configs):
        self.configs=configs
    def chunk(self,docs):
        chunk_docs=[]
        for doc in docs:
            text=doc.page_content()
            metadata=doc.metadata
            
            if self.mode=='simple':
                chunk=self._simple_chunk(text)
            else:
                chunk=self._recursive_chunk(text)
        for idx,chunk in enumerate(chunks):
            chunk_metadata=metadata.copy()
            chunk_metadata['chunk_id']=idx
            chunk_docs.append(
                Document(
                    page_content=chunk,
                    metadata=chunk_metadata
                )
            )
        return chunk_docs
    def _simple_chunk(self,text):
        start=0
        chunks=[]
        text_length=len(text)
        while start<text_length:
            end=start+self.chunk_size
            chunk=text[start:end]
            chunks.append(chunk)
            start+=self.chunk_size -self.chunk_overlap
        return chunks
    def _recursive_chunk(self,text):
        paragraphs=self._split_into_paragraphs(text)
        chunks=[]
        buffer="" 
        for para in paragraphs:
            if len(buffer)+len(para)<=self.chunk_size:
                buffer+=para +"\n"
            else:
                chunk=buffer.strip()
                if chunk:
                    chunks.append(chunk)
                buffer=para +"\n"
        if buffer.strip():
            chunks.append(buffer.strip())
            
        final_chunks=[]
        for chunk in chunks:
            if len(chunk)> self.chunk_size:
                final_chunks.extend(self._split_into_sentences(chunk))
            else:
                final_chunks.append(chunk)
        overlapping=self._add_overlaps(final_chunks)
        return overlapping
    def _split_by_paragraph(self, text: str) -> List[str]:
        return [p.strip() for p in text.split("\n\n") if p.strip()]


    def _sentence_splitter(self, text: str) -> List[str]:
        """
        Splits by sentence boundaries using a simple regex.
        """
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []

        buffer = ""
        for s in sentences:
            if len(buffer) + len(s) <= self.chunk_size:
                buffer += s + " "
            else:
                chunks.append(buffer.strip())
                buffer = s + " "

        if buffer.strip():
            chunks.append(buffer.strip())

        return chunks
                    
    def _add_overlap(self, chunks: List[str]) -> List[str]:
        overlapped = []

        for i, chunk in enumerate(chunks):
            if i == 0:
                overlapped.append(chunk)
                continue

            prev = chunks[i - 1]
            overlap_text = prev[-self.chunk_overlap:] if len(prev) > self.chunk_overlap else prev

            new_chunk = overlap_text + "\n" + chunk
            overlapped.append(new_chunk)

        return overlapped
    
class EmbedDocument:
    def __init__(self,embedding_model):
        self.model=embedding_model
    def embed(self,docs):
        results=[]
        texts=[doc.page_content() for doc in docs]
        embedding=self._embed_texts(texts)
        for idx,(doc,vector) in enumerate(zip(docs,embedding)):
            results.append({
                "id":idx,
                "vector":vector,
                "text":doc.page_content(),
                "metadata":doc.metadata,
            }
            )
        return results
    def _embed_texts(self,text):
        batch_size=32
        vectors=[]
        for i in range(0,len(text),batch_size):
            batch=text[i:i+batch_size]
            vector=self.model.embed_documents(batch)
            vectors.append(vector)
        return vectors