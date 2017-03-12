import os

class DataStore(object):
    def __init__(self, email_address, root_directory=None):
        self.email_address = email_address
        self.root_directory = root_directory or os.getcwd()

    @property
    def storage_path(self):
        directory = os.path.join(self.root_directory, self.email_address)
        os.makedirs(directory, exist_ok=True)
        return directory

    def __contains__(self, item):
        return os.path.exists(os.path.join(self.storage_path, item))

    def __setitem__(self, item, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        with open(os.path.join(self.storage_path, item), 'wb') as f:
            return f.write(data)

    def __getitem__(self, item):
        with open(os.path.join(self.storage_path, item), 'rb') as f:
            return f.read()

    def path(self, item):
        return os.path.join(self.storage_path, item)
