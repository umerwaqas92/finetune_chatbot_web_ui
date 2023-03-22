from flask import Flask, request, jsonify, render_template, redirect
import requests
import json
import os
from llama_index import SimpleDirectoryReader, GPTListIndex, readers, GPTSimpleVectorIndex, LLMPredictor, PromptHelper
from langchain import OpenAI
from flask_cors import CORS
import datetime


app = Flask(__name__)
CORS(app)

my_dir = os.path.dirname(__file__)
api_key_json = os.path.join(my_dir, 'api_key.json')
DATA_FILE = os.path.join(my_dir, 'query_responses.json')


with open(api_key_json, 'r') as f:
    jsonfile= json.load(f)

    api_key = jsonfile['api_key']
    api_temp = jsonfile['api_temp']
    api_model_name = jsonfile['api_model_name']
    api_token_max = jsonfile['api_token_max']


    os.environ["OPENAI_API_KEY"]=api_key


def construct_index(api_key, api_temp, api_model_name, api_token_max):

    # set maximum input size
    max_input_size = 4096
    # set number of output tokens
    num_outputs = int(api_token_max)
    # set maximum chunk overlap
    max_chunk_overlap = 20
    # set chunk size limit
    chunk_size_limit = 600

    my_dir = os.path.dirname(__file__)
    pickle_file_path = os.path.join(my_dir, 'context_data/data')


    # define LLM

    llm_predictor = LLMPredictor(llm=OpenAI(temperature=api_temp, model_name=api_model_name, max_tokens=num_outputs))
    prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size_limit)

    documents = SimpleDirectoryReader(pickle_file_path).load_data()

    index = GPTSimpleVectorIndex(
        documents, llm_predictor=llm_predictor, prompt_helper=prompt_helper
    )

    index.save_to_disk(os.path.join(my_dir, 'index.json'))

    return index


@app.route('/clearchhat')
def clear_chat_history():
    with open(DATA_FILE, 'w') as f:
            json.dump({"":"\nHi there! feel free to ask!"}, f)
    return redirect('/')


@app.route('/answer', methods=['POST'])
def answer():
    query = request.json['query']
    response = ask_ai(query)
    return jsonify(response)

@app.route('/save', methods=['POST'])
def save():
    content = request.form['content']
    filename = request.form['filename']

    filepath = os.path.join(my_dir+'/context_data/data', filename,)
    with open(filepath, 'w') as f:
        f.write(content)
            
    return redirect('/edit?filename=' + filename)


@app.route('/delete', methods=['POST'])
def delete():
    filename = request.json['filename']
    filepath = os.path.join(my_dir+'/context_data/data', filename)
    os.remove(filepath)

    return 'OK'



# Load query-response data from file, or create empty dict if file does not exist
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        query_responses = json.load(f)
else:
    query_responses = {}

def ask_ai(query):
    my_dir = os.path.dirname(__file__)
    pickle_file_path = os.path.join(my_dir, 'index.json')
    index = GPTSimpleVectorIndex.load_from_disk(pickle_file_path)

    response = index.query(query, response_mode="compact")
    return {"response": response.response}



@app.route('/chatbot')
def chatbot():
    return render_template('/chatbot.html')






@app.route('/create_new_page', methods=['POST'])
def create_new_page():
    # Get form data
    
    filename_input = request.form.get('filename')
    
    filepath = os.path.join(my_dir+'/context_data/data',  f"{filename_input}.txt")
    
   
    with open(filepath, 'w') as f:
        f.write('')
    
    # Return success response
    return redirect('/edit?filename=' +  f"{filename_input}.txt")





@app.route('/edit')
def edit():
    filename = request.args.get('filename')
    filepath = os.path.join(my_dir+'/context_data/data', filename)
    print(filepath)
    with open(filepath, 'r') as f:
        content = f.read()
    return render_template('editor.html', content=content, filename=filename)



def get_files():
    list_dir=os.path.join(my_dir, 'context_data/data')
    files = os.listdir(list_dir)
    return files


@app.route('/files')
def file_list():
    files = get_files()
    # Render the file list template with the list of files
    return render_template('file_list.html', files=files)


@app.route('/', methods=['GET', 'POST'])
def index():
    # Load query-response data from file, or create empty dict if file does not exist
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            query_responses = json.load(f)
    else:
        query_responses = {}


    query_responses = {k: v for k, v in reversed(query_responses.items())}


    if request.method == 'POST':
        query = request.form['query']

        response_text = ask_ai(query)['response']

        # Save query-response pair to dictionary and write to file
        query_responses[query] = response_text
        query_responses = {k: v for k, v in reversed(query_responses.items())}

        with open(DATA_FILE, 'w') as f:
            json.dump(query_responses, f)

        return render_template('index.html', query_responses=query_responses)
    return render_template('index.html', query_responses=query_responses)


# @app.route('/uploadFile', methods=['GET', 'POST'])
# def upload_file():
#     file_list = get_files()
#     if request.method == 'POST':
#         document_files = request.files.getlist('documents')
#         print("got files "+str(document_files))
#         print(len(document_files))
#         if len(document_files) > 0:
#             for document_file in document_files:
#                 document_filename = document_file.filename
#                 if document_filename:
#                     document_path = os.path.join(my_dir+'/context_data', 'data', document_filename,)
#                     document_file.save(document_path)
#             file_list = get_files() # assuming this function returns a list of file paths
#             return render_template('upload.html', success='File(s) uploaded successfully', api_key=api_key, api_temp=api_temp, api_model_name=api_model_name, api_token_max=api_token_max, file_list=file_list)
#         else:
#             return render_template('upload.html', error='No file selected', api_key=api_key, api_temp=api_temp, api_model_name=api_model_name, api_token_max=api_token_max, file_list=file_list)
#     else:
#         return render_template('upload.html', api_key=api_key, api_temp=api_temp, api_model_name=api_model_name, api_token_max=api_token_max, file_list=file_list)


@app.route('/uploadFile', methods=['GET', 'POST'])
def uploadFile():
    
     document_file = request.files['document']

    
     file_list=get_files()
     print("got files "+str(len(file_list)))

     document_filename = document_file.filename
     if document_filename:
        document_path = os.path.join(my_dir+'/context_data', 'data', document_filename,)
        document_file.save(document_path)
        file_list=get_files()
      
        return  redirect("/upload") #render_template('upload.html',success='File uploaded successfully',api_key=api_key, api_temp=api_temp, api_model_name=api_model_name, api_token_max=api_token_max,file_list=file_list)
     
     return redirect("/upload")  #render_template('upload.html',error='File is not selected',api_key=api_key, api_temp=api_temp, api_model_name=api_model_name, api_token_max=api_token_max, file_list=file_list)


def ask_ai2(query):
    my_dir = os.path.dirname(__file__)
    pickle_file_path = os.path.join(my_dir, 'islamic_index.json')

    index = GPTSimpleVectorIndex.load_from_disk(pickle_file_path)

    response = index.query(query, response_mode="compact")

    return {"response": response.response}

def ask_ai3(query):
    my_dir = os.path.dirname(__file__)
    pickle_file_path = os.path.join(my_dir, 'index.json')
    index = GPTSimpleVectorIndex.load_from_disk(pickle_file_path)
    response = index.query(query, response_mode="compact")
        # Save log data to chat_log.txt
    log_path = os.path.join(my_dir, 'chat_log.txt')
    with open(log_path, 'a') as log_file:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_file.write(f'{timestamp}: {query} --> {response.response}\n')

    return response.response


@app.route('/show_log')
def show_log_api():
    my_dir = os.path.dirname(__file__)
    log_path = os.path.join(my_dir, 'chat_log.txt')

    if not os.path.exists(log_path):
        return {'error': 'Log file not found.'}

    with open(log_path, 'r') as log_file:
        log_data = log_file.read()

    return {'log_data': log_data}


@app.route('/answer3', methods=['POST'])
def answer3():
    query = request.json['query']
    response = ask_ai3(query)
    return response



@app.route('/upload', methods=['GET', 'POST'])
def upload():
    files = get_files()
    if request.method == 'POST':
        if 'upload-file"' in request.form:
            #save file
            file = request.files['file']
            filename = secure_filename(file.filename)
            file.save(os.path.join(my_dir+'/context_data/data', filename))


            return render_template('upload.html',success='File uploaded successfully',api_key=api_key, api_temp=api_temp, api_model_name=api_model_name, api_token_max=api_token_max,files=files)

        if 'chat_screen' in request.form:
            return render_template('index.html')

        if 'start-training' in request.form:

            api_key = request.form['api_key']
            api_temp = request.form['api_temp']
            api_model_name = request.form['api_model_name']
            api_token_max = request.form['api_token_max']
            with open(my_dir+'/api_key.json', 'w') as f:
                json.dump({'api_key':api_key,'api_temp':api_temp,'api_model_name':api_model_name,'api_token_max':api_token_max}, f)
                construct_index(api_key=api_key, api_temp=api_temp,api_model_name=api_model_name,api_token_max=api_token_max)
                return render_template('upload.html', success='Trained successfully',api_key=api_key, api_temp=api_temp, api_model_name=api_model_name, api_token_max=api_token_max,files=files)

        if'submit' in request.form:
            # Check if the file is present in the request
            if 'document' not in request.files:

                with open(my_dir+'/api_key.json', 'r') as f:
                                jsonfile= json.load(f)
                                api_key = jsonfile['api_key']
                                api_temp = jsonfile['api_temp']
                                api_model_name = jsonfile['api_model_name']
                                api_token_max = jsonfile['api_token_max']
                                return render_template('upload.html', success='configuration has been saved',api_key=api_key, api_temp=api_temp, api_model_name=api_model_name, api_token_max=api_token_max,files=files)
            else:
                # Get the file from the request and save it to the data directory
                document_file = request.files['document']
                document_filename = document_file.filename
                if not document_filename:

                    api_key = request.form['api_key']
                    api_temp = request.form['api_temp']
                    api_model_name = request.form['api_model_name']
                    api_token_max = request.form['api_token_max']


                    with open(api_key_json, 'w') as f:
                        json.dump({'api_key': api_key,"api_temp":api_temp,"api_model_name":api_model_name,"api_token_max":api_token_max}, f)

                    return render_template('upload.html', error='No file selected but api has been uploaded',api_key=api_key, api_temp=api_temp, api_model_name=api_model_name, api_token_max=api_token_max,files=files)

                document_path = os.path.join(my_dir+'/context_data', 'data', document_filename,)
                document_file.save(document_path)

            # Update the OpenAI API key in api_key.json
            #filepath = os.path.join(my_dir+'/context_data/data', filename)
            api_key = request.form['api_key']
            with open(my_dir+'/api_key.json', 'w') as f:
                json.dump({'api_key': api_key}, f)

            return render_template('upload.html', success='File uploaded successfully',api_key=api_key, api_temp=api_temp, api_model_name=api_model_name, api_token_max=api_token_max,files=files)
        else:
            with open(my_dir+'/api_key.json', 'r') as f:
                jsonfile= json.load(f)
                api_key = jsonfile['api_key']
                api_temp = jsonfile['api_temp']
                api_model_name = jsonfile['api_model_name']
                api_token_max = jsonfile['api_token_max']

                return render_template('upload.html',api_key=api_key, api_temp=api_temp, api_model_name=api_model_name, api_token_max=api_token_max,files=files)
    else:
         with open(my_dir+'/api_key.json', 'r') as f:


                jsonfile= json.load(f)

                api_key = jsonfile['api_key']
                api_temp = jsonfile['api_temp']
                api_model_name = jsonfile['api_model_name']
                api_token_max = jsonfile['api_token_max']
                return render_template('upload.html',api_key=api_key, api_temp=api_temp, api_model_name=api_model_name, api_token_max=api_token_max,files=files)


if __name__ == '__main__':
    app.run(debug=True)
