import os
import sys
import importlib

if __name__ == '__main__' and __package__ is None:
    if hasattr(sys, "_MEIPASS"):  # pyinstaller deployed
        print(sys._MEIPASS)
    print(__file__)
    package_path = os.path.dirname(os.path.abspath(__file__))
    print(package_path)
    __package__ = os.path.basename(package_path)
    print(__package__)
    loader = importlib.find_loader(__package__, os.path.join(package_path, '..'))
    module = loader.load_module(__package__)
    loader.exec_module(module)

if __name__ == '__main__':
    from . import main
    main()
