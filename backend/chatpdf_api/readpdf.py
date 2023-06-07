

from PyPDF2 import PdfReader
import openai
import os
from dotenv import load_dotenv

load_dotenv()

from langchain.chains import AnalyzeDocumentChain
from langchain.chains.summarize import load_summarize_chain
from langchain.llms import OpenAI
from langchain.document_loaders import UnstructuredPDFLoader

# This function is reading PDF from the start page to final page
# given as input (if less pages exist, then it reads till this last page)


import pandas as pd

import requests

from .database import add_document

from base64 import b64decode

def get_pdf_text(document_path, start_page=1, final_page=999):
    reader = PdfReader(document_path)
    # reader = UnstructuredPDFLoader(document_path)
    number_of_pages = len(reader.pages)
    
    page = ""
    for page_num in range(start_page - 1, min(number_of_pages, final_page)):
        page += reader.pages[page_num].extract_text()
    return page

def summarize(pages):
    model = OpenAI(temperature=0, openai_api_key=os.getenv('OPENAI_API_KEY'))
    summary_chain = load_summarize_chain(llm=model, chain_type='map_reduce')
    summarize_document_chain = AnalyzeDocumentChain(combine_docs_chain=summary_chain)
    summary = summarize_document_chain.run(pages)
    return summary

def create_dataframe(title, identifier, author, summary):
    data = {'Id': [identifier], 'Title': [title],'Author': [author] ,'Summary': [summary]}
    # print(data)
    df = pd.DataFrame(data)
    # print(df)
    # print(df.head())
    # print(df.columns)
    return df


def processing(document_path, author):
    pages = get_pdf_text(document_path)
    summary = summarize(pages)
    df = create_dataframe(document_path, author, summary)
    return df

def extract(document_path, author):
    pages = get_pdf_text(document_path)
    df = create_dataframe(document_path, author, pages)
    return df

def read_from_url(url, author,identifier, namespace):
    response = requests.get(url)
    response.raise_for_status()

    with open('temp.pdf', 'wb') as file:
        file.write(response.content)
    
    pages = get_pdf_text('temp.pdf')
    add_document(document_id = identifier, document_file=pages, namespace_name=namespace)
    df = create_dataframe(url, identifier, author, pages)
    os.remove('temp.pdf')
    
    return df

def read_from_encode(encoded_doc, author,identifier, namespace):
    pages = b64decode(encoded_doc).decode('utf-8')
    if pages [0:4] != b'%PDF':
        raise ValueError('Missing the PDF file signature, may not be a PDF file')
    add_document(document_id = identifier, document_file=pages, namespace_name=namespace)
    df = create_dataframe(identifier, author, pages)
    return df




