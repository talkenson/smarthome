import pickle, os, json

history = []

def loadAll():
    global history
    if os.path.exists('messages.pickle'):
        with open('messages.pickle', 'rb') as f:
            history = pickle.load(f)

loadAll()

print(json.dumps(history))
