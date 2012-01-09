from sleekxmpp import ClientXMPP
from sleekxmpp.xmlstream import ET
from searchitem import SearchItem 

RPP = 10
RSM_NS = "http://jabber.org/protocol/rsm"
QUERY_NS = "http://buddycloud.com/channel_directory/%s"

def prepRSM(page):
    rsm = ET.Element("{%s}set" % RSM_NS)
    
    max = ET.Element("max")
    max.text = str(RPP)
    rsm.append(max)
    
    index = ET.Element("index")
    index.text = str(page * RPP)
    rsm.append(index)
    
    return rsm

def queryNamespace(q):
    ns = "metadata_query"
    query = q
    
    procType, sep, pQuery = q.partition(':')
    
    if (procType == "post") :
        ns = "content_query"
        query = pQuery.rstrip()
    elif (procType == "metadata") :
        query = pQuery.rstrip()
    
    return ns, query

def parseSearchItem(itemxml, proc):

    searchItem = None

    if (proc == "metadata_query") :
        ns = QUERY_NS % proc
        title = itemxml.find("{%s}title" % ns).text
        print itemxml.attrib
        creation_date = None
        if ('created' in itemxml.attrib) :
            creation_date = itemxml.attrib['created']
            
        channel_id = itemxml.attrib['jid']
        
        searchItem = SearchItem(title, creation_date, channel_id)
    
    elif (proc == "content_query") :
        atomns = "http://www.w3.org/2005/Atom"
        content = itemxml.find("{%s}entry/{%s}content" % (atomns, atomns)).text
        author = itemxml.find("{%s}entry/{%s}author" % (atomns, atomns)).text
        parent = itemxml.find("{%s}entry/{%s}parent_simpleid" % (atomns, atomns)).text
        published = itemxml.find("{%s}entry/{%s}published" % (atomns, atomns)).text
        
        searchItem = SearchItem("%s: %s" % (author, content), published, parent)
        
    return searchItem

class SearchClient : 
    
    def __init__(self, jid, password, client_host, client_port, searchserver) : 
        self.xmpp = ClientXMPP(jid, password)
        self.con_address = client_host, client_port
        self.searchserver = searchserver
    
    def run(self) :
        self.xmpp.connect(address=self.con_address) 
        self.xmpp.process(threaded=True)
        

    def query(self, q, page) :
                
        rsm = prepRSM(page)
        proc, query = queryNamespace(q)
        
        ns = QUERY_NS % proc
        
        search = ET.Element("search")
        search.text = query
        
        iq = self.xmpp.make_iq_get(queryxmlns=ns, ito=self.searchserver, ifrom=self.xmpp.boundjid)

        query = iq.xml.find("{%s}query" % ns)
        query.append(search)
        query.append(rsm)
        
        response = iq.send()
        itemsxml = response.xml.findall("{%s}query/{%s}item" % (ns, ns))
        
        items = []

        for itemxml in itemsxml:
            items.append(parseSearchItem(itemxml, proc))
        
        count = response.find("{%s}query/{%s}set/{%s}count" % (ns, RSM_NS, RSM_NS))
        
        return items, count.text
        
