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

def prepMetadataNode(query):
    search = ET.Element("search")
    search.text = query
        
    return "metadata_query", search 

def prepContentNode(query):
    search = ET.Element("search")
    search.text = query
        
    return "content_query", search

def prepRecommendationNode(query):
    search = ET.Element("user-jid")
    search.text = query
        
    return "recommendation_query", search

def prepSimilarityNode(query):
    search = ET.Element("channel-jid")
    search.text = query
        
    return "similar_channels", search

def prepSearchNode(q):
    procType, sep, pQuery = q.partition(':')
    
    if (not sep) :
        return prepMetadataNode(q)
    
    query = pQuery.strip()
    
    if (procType == "metadata") :
        return prepMetadataNode(query)
    
    if (procType == "post") :
        return prepContentNode(query)

    if (procType == "recommend") :
        return prepRecommendationNode(query)

    if (procType == "similar") :
        return prepSimilarityNode(query)

def parseSearchItem(itemxml, proc):

    searchItem = None

    if (proc == "metadata_query" or proc == "recommendation_query" or proc == "similar_channels") :
        ns = QUERY_NS % proc
        title = itemxml.find("{%s}title" % ns).text
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
        proc, node = prepSearchNode(q)
        
        ns = QUERY_NS % proc
        iq = self.xmpp.make_iq_get(queryxmlns=ns, ito=self.searchserver, ifrom=self.xmpp.boundjid)

        query = iq.xml.find("{%s}query" % ns)
        query.append(node)
        query.append(rsm)
        
        try :
            response = iq.send()
        except :
            return [], "0"
        
        itemsxml = response.xml.findall("{%s}query/{%s}item" % (ns, ns))
        
        items = []

        for itemxml in itemsxml:
            items.append(parseSearchItem(itemxml, proc))
        
        count = response.find("{%s}query/{%s}set/{%s}count" % (ns, RSM_NS, RSM_NS))
        
        return items, count.text
        
