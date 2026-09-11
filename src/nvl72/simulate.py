from .cli import main
if __name__=='__main__': main(['simulate']+__import__('sys').argv[1:])
