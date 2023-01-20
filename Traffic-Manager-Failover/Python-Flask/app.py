import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import CorsOptions, SearchIndex, ScoringProfile, SearchFieldDataType, SimpleField, SearchableField

app = Flask(__name__)

westus_url = "https://luouelle-2023-bcdr-test-westus2.search.windows.net"
westeu_url = "https://luouelle-2023-bcdr-test-westeu.search.windows.net"
index_name = "hotelsexample"

region = os.environ['REGION']
query_key = os.environ['WESTEU_QUERY_KEY'] if region == 'WESTEU' else os.environ['WESTUS2_QUERY_KEY']
admin_key = os.environ['WESTEU_ADMIN_KEY'] if region == 'WESTEU' else os.environ['WESTUS2_ADMIN_KEY']
url = westeu_url if region == "WESTEU" else westus_url
search_client = SearchClient(url, index_name, AzureKeyCredential(query_key))
upload_client = SearchClient(url, index_name, AzureKeyCredential(admin_key))
index_client = SearchIndexClient(url, AzureKeyCredential(admin_key))

def query_index(query):
    return search_client.search(search_text=query)

def ensure_index():
    fields = [
        SimpleField(name="hotelId", type=SearchFieldDataType.String, key=True),
        SimpleField(name="baseRate", type=SearchFieldDataType.Double),
        SearchableField(name="description", type=SearchFieldDataType.String, collection=True),
        SearchableField(name="hotelName", type=SearchFieldDataType.String)
    ]
    cors_options = CorsOptions(allowed_origins=["*"], max_age_in_seconds=60)
    scoring_profiles = [ScoringProfile(name="MyProfile")]
    index = SearchIndex(
        name=index_name,
        fields=fields,
        scoring_profiles=scoring_profiles,
        cors_options=cors_options)

    return index_client.create_or_update_index(index=index)

def upload_document():
    DOCUMENT = {
        'HotelId': '1000',
        'BaseRate': 120.50,
        'Description': 'Simple example',
        'HotelName': 'Azure Inn',
    }

    return upload_client.upload_documents(documents=[DOCUMENT])

@app.route('/')
def index():
    print('Request for index page received')
    return render_template('index.html')

@app.route('/hello', methods=['POST'])
def hello():
    name = request.form.get('name')

    if name:
        print('Request for hello page received with name=%s' % name)
        return render_template('hello.html', name = name)
    else:
        print('Request for hello page received with no name or blank name -- redirecting')
        return redirect(url_for('index'))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/health')
def health():
    return 'OK'

@app.route('/dev')
def dev():
    ensure_index()
    upload_document()

    query = request.args.get('query')
    query_index(query)
    return f"Index ensure, document upload and index query all were successful in {region} on endpoint {url}"

if __name__ == '__main__':
    app.run()