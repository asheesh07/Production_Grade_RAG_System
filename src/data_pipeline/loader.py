import os
import io
import json
from typing import BinaryIO,Union


from pypdf import PdfReader

def _minimal_clean_text(text):
    if text is None:
        return ''
    return ' '.join(text.split())
def _now_iso():
    from datetime import datetime
    return datetime.utcnow().isoformat() + 'Z'
def _get_doc_id(source):
    import uuid
    return f"{source}_{uuid.uuid4().hex}"
def _safe_title(title):
    import re
    safe_title=re.sub(r'[^a-zA-Z0-9_\- ]','',title)
    return safe_title[:100] if len(safe_title)>100 else safe_title

class DocumentLoader:
    def __init__(self,configs=None):
        self.configs=configs or {}
        self.file_size=int(self.configs.get('max_file_size',50*1024*1024))
        self.temp_dir=self.configs.get('temp_dir','/tmp')
        os.makedirs(self.temp_dir, exist_ok=True)
        
    def load_from_text_input(self,text_input,title=None): 
        try:
            full_text=_minimal_clean_text(text_input)
            if not full_text.strip():
                return False,None
            doc={
                "doc_id":_get_doc_id("user_text"),
                "title":_safe_title("title") if title else f"user_text_{_now_iso()}",
                'source':"user_text",
                "raw_text":full_text,
                "metadata":{
                    "provided_title":title,
                    "upload_time":_now_iso(),
                    "char_count":len(full_text)
            } }
            logger.info("Loaded text input with %d characters", len(full_text))
            return True,doc
        except Exception as e:
            logger.exception("Failed to load text input: %s", e)
            return False,None
    
    def load_from_pdf(self,file_stream,filename):
        try:
            try:
                file_stream.seek(0)
            except Exception:
                file_stream=io.BytesIO(file_stream.read())
                
            reader=PdfReader(file_stream)
            num_pages=len(reader.pages)
            texts=[]
            for i in range(num_pages):
                try:
                    page=reader.pages[i]
                    page_text=page.extract_text()
                    texts.append(page_text)
                except Exception as e:
                    logger.warning("Failed to extract text from page %d of PDF %s: %s", i, filename, e)
                    continue
            full_raw_text="\n".join(texts)
            full_text=_minimal_clean_text(full_raw_text)
            if not full_text.strip():
                logger.warning("No text extracted from pdf %s",filename)
                return False,None
            doc={
                "doc_id":_get_doc_id("user_doc"),
                "title":_safe_title(filename),
                "source":"pdf",
                "raw_text":full_text,
                "metadata":{
                    "num_pages":num_pages,
                    "filename":filename,
                    "upload_time":_now_iso(),
                    "char_count":len(full_text)
                }}
            logger.info("Loaded PDF %s with %d pages and %d characters", filename, num_pages, len(full_text))
            return True,doc
                
        except Exception as e:
            logger.exception("Failed to load PDF %s: %s", filename, e)
            return False, None
    
    def load_from_file(self,file_stream,filename):
        if filename.lower().endswith('.pdf'):
            return self.load_from_pdf(file_stream,filename)
        else:
            raise ValueError("Only PDF files are supported.")
    
    def save_documents(self,documents,output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        temp_path=output_path + ".tmp"
        with open(temp_path,'w',encoding='utf-8') as f:
            for doc in documents:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n") 
        os.replace(temp_path,output_path)
        
        
##########################################################################################

class LoaderDocument:
    def __init__(self,configs):
        self.configs=configs
        
    def load_documents(self,file:Union[str,bytes,BinaryIO]):
        
        file_info=self.detect_file_type(file)
        
        loader_fn=self.router_loader(file_info)
        
        doc=loader_fn(file)
        
        doc=self.mormalise_doocument(doc,file_info)
        
        return doc
    def detect_file_type(self,file):
        if isinstance(file,str):
            extension=os.path.splitext(file)[1].lower()
            mime=magic.from_file(file,mime=True)
        elif isinstance(file,bytes):
            mime=magic.from_buffer(file,mime=True)
            extension=None
        else:
            mime=magic.from_buffer(file.read(2048),mime=True)
            extension=None
            file.seek(0)
            
        if mime=='application/pdf':
            return {'type':'pdf'}
        elif mime=='application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            return {'type':'docx'}
        elif mime.startswith('text/'):
            return {"type":"text"}
        elif mime in ('text/html','application/xhtml+xml'):
            return {'type':'html'}
        elif mime.startswith('image/'):
            return {'type':'image'}
        return {'type':'unknown'}
    
    def router_loader(self,file_info):
        file_type=file_info['type']
        if file_type=='pdf':
            return self.load_pdf
        elif file_type=='docx':
            return self.load_docx
        elif file_type=='text':
            return self.load_text
        elif file_type=='html':
            return self.load_html
        elif file_type=='image':
            return self.load_image
        else:
            raise ValueError("Unsupported file type")
    def load_pdf(self,file):
        return 
    def load_dcox(self,file):
        return
    def load_text(self,file):
        if isinstance(file,str):
            with open(file,'w',encoding='utf-8') as f:
                text=f.read()
            
        return
    def load_html(self,file):
        return
    def load_image(self,file):
        return
    
    def mormalise_doocument(self,doc,file_info):
        return doc