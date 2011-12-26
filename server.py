from flask import Flask, render_template, request
from searchclient import SearchClient
from searchclient import RPP
import logging
from ConfigParser import ConfigParser

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('search.html')

@app.route('/search')
def search():
    q = request.args.get('q', '')
    page = request.args.get('page', '')
    items, count = client.query(q, int(page))
    return render_template('results.html', items=items, maxpage=int(count)/RPP, q=q, this_page=int(page))

if __name__ == '__main__':
    
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')
    
    config = ConfigParser()
    config.readfp(open('search.cfg'))
    client_jid = config.get('searchclient', 'jid')
    client_pass = config.get('searchclient', 'password')
    server_address = config.get('channeldirectory', 'address')
    
    client = SearchClient(client_jid, client_pass, server_address)
    client.run() 
    
    app.run()