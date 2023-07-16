import pickle

class KV(dict):
    "super simple key-value store"

    @classmethod
    def open(self, filename):
        db = KV()
        db.filename = filename
        try:
            data = pickle.load(open(filename, 'rb'))
        except FileNotFoundError:
            data = {}
        db.update(data)
        return db

    def sync(self):
        pickle.dump(dict(self), open(self.filename, 'wb'))

    def close(self):
        self.sync()
