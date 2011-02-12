"""Read .leo files into a simple python data structure with
h, b, u (unknown attribs), gnx and children information.
Clones and derived files are ignored.  Useful for scanning
multiple .leo files quickly.
"""

from xml.sax.handler import ContentHandler
from xml.sax import parse
from pickle import loads
from binascii import unhexlify

class node:
    """Representation of a Leo node.  Root node has itself as parent.
    
    :IVariables:
        children
          python list of children
        u
          unknownAttributes dict (decoded)
        h
          headline
        b
          body text
        gnx
          node id
        parent
          node's parent
        path
          list of nodes that lead to this one from root, including this one
    """
    
    def __init__(self):
        """Set ivars"""
        self.children = []
        self.u = {}
        self.h = []
        self.b = []
        self.gnx = None
        self.parent = self
        self.path = []
        
    def __str__(self, level=0):
        """Return long text representation of node and
        descendents with indentation"""
        ans = [('  '*(level-1) + self.h)[:78]]
        for k in self.u:
            s = self.u[k]
            ans.append(("%s@%s: %s"%('  '*(level+1), k, repr(s)))[:78])
        for line in self.b[:5]:
            ans.append(('  '*(level+1) + '|' + line)[:78])
        for c in self.children:
            ans.append(c.__str__(level=level+1))
        return '\n'.join(ans)
        
    def UNL(self):
        """Return the UNL string leading to this node"""
        return '-->'.join([i.h for i in self.path])
        
    def flat(self):
        """iterate this node and all its descendants in a flat list, 
        useful for finding things and building an UNL based view"""
        if self.parent != self:
            yield(self)
        for i in self.children:
            for j in i.flat():
                yield j

class LeoReader(ContentHandler):
    """Read .leo files into a simple python data structure with
    h, b, u (unknown attribs), gnx and children information.
    Clones and derived files are ignored.  Useful for scanning
    multiple .leo files quickly.
    
    :IVariables:
        root
          root node
        cur
          used internally during SAX read
        idx
          mapping from gnx to node
        `in_`
          name of XML element we're current in, used for SAX read
        in_attr
          attributes of element tag we're currentl in, used for SAX read
        path
          list of nodes leading to current node
        
    """
    

    def __init__(self, *args, **kwargs):
        """Set ivars"""
        ContentHandler.__init__(self, *args, **kwargs)
        self.root = node()
        
        self.root.h = 'ROOT'  
        # changes type from [] to str, done by endElement() for other vnodes
        
        self.cur = self.root
        self.idx = {}
        self.in_ = None
        self.in_attrs = {}
        self.path = []

    def startElement(self, name, attrs):
        """collect information from v and t elements"""
        self.in_ = name
        self.in_attrs = attrs
        
        if name == 'v':
            nd = node()
            self.cur.children.append(nd)
            nd.parent = self.cur
            self.cur = nd
            self.idx[attrs['t']] = nd
            nd.gnx = attrs['t']
            self.path.append(nd)
            nd.path = self.path[:]
    
        if name == 't':
            for k in attrs.keys():
                if k == 'tx':
                    continue
                self.idx[attrs['tx']].u[k] = attrs[k]
                
    def endElement(self, name):
        """decode unknownAttributes when t element is done"""

	self.in_ = None
        # could maintain a stack, but we only need to know for
        # character collection, so it doesn't matter

        if name == 'v':
            self.cur.h = ''.join(self.cur.h)
            self.cur = self.cur.parent
            if self.path:
                del self.path[-1]
                
        if name == 't':
            nd = self.idx[self.in_attrs['tx']]
            for k in nd.u:
                s = nd.u[k]
                if not k.startswith('str_'):
                    try:
                        s = loads(unhexlify(s))
                    except Exception:
                        pass
                        
                nd.u[k] = s
         
    def characters(self, content):
        """collect body text and headlines"""
        
        if self.in_ == 'vh':
            self.cur.h.append(content)
            
        if self.in_ == 't':
            self.idx[self.in_attrs['tx']].b.append(content)

def get_leo_data(source):
    """Return the root node for the specificed .leo file (path or file)"""
    parser = LeoReader()
    parse(source, parser)
    return parser.root

if __name__ == '__main__':
    import os
    wb = os.path.expanduser(
        os.path.join('~', '.leo', 'workbook.leo')
    )
    leo_data = get_leo_data(wb)
    for i in leo_data.flat():
        print i.UNL()