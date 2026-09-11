from .cli import main
if __name__=='__main__': main(['report']+__import__('sys').argv[1:])
