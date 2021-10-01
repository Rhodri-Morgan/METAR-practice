def get_url(request_path):
    path = [{'traversal' : 'RhodriThomasMorgan.com', 'url' : '/'}]
    for traversal in request_path:
        if path[-1] == '/':
            path.append({'traversal' : traversal, 'url' : '{0}/{1}'.format(path[-1]['url'], traversal)})
        else:
            path.append({'traversal' : traversal, 'url' : '/{0}'.format(traversal)})
    return path
