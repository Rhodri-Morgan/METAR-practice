def get_url(request_path):
    path = [{'traversal' : 'RhodriThomasMorgan.com', 'url' : '/'}]
    for traversal in request_path:
        path.append({'traversal' : traversal, 'url' : '{0}/{1}'.format(path[-1]['url'], traversal)})
    return path
