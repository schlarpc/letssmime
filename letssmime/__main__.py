import os
import sys
import importlib

if __name__ == '__main__' and __package__ is None:
    package_path = os.path.dirname(os.path.abspath(__file__))
    __package__ = os.path.basename(package_path)
    loader = importlib.find_loader(__package__, os.path.join(package_path, '..'))
    module = loader.load_module(__package__)
    loader.exec_module(module)

if __name__ == '__main__':
    from . import main
    main()
