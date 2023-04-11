from flask import Flask, jsonify, request
from llama_index import SimpleDirectoryReader, GPTListIndex, readers, GPTSimpleVectorIndex, LLMPredictor, PromptHelper
from langchain import OpenAI
import sys
import os

app = Flask(__name__)
os.environ["OPENAI_API_KEY"]="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"



def construct_index():
    # set maximum input size
    max_input_size = 4096
    # set number of output tokens
    num_outputs = 2000
    # set maximum chunk overlap
    max_chunk_overlap = 20
    # set chunk size limit
    chunk_size_limit = 600 

    # define LLM
    my_dir = os.path.dirname(__file__)
    pickle_file_path = os.path.join(my_dir, 'index.json')
    llm_predictor = LLMPredictor(llm=OpenAI(temperature=0.5, model_name="text-davinci-003", max_tokens=num_outputs))
    prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size_limit)
 
    documents = SimpleDirectoryReader(pickle_file_path).load_data()
    
    index = GPTSimpleVectorIndex(
        documents, llm_predictor=llm_predictor, prompt_helper=prompt_helper
    )

    index.save_to_disk('index.json')

    return index

def ask_ai(query):
    my_dir = os.path.dirname(__file__)
    pickle_file_path = os.path.join(my_dir, 'index.json')
    index = GPTSimpleVectorIndex.load_from_disk(pickle_file_path)
    
    response = index.query(query, response_mode="compact")
    return {"response": response.response}


construct_index()   