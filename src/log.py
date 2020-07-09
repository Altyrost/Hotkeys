from PySide2.QtWidgets import QApplication

def require_qapp_verbose(func):
    def wrapper(args):
        if QApplication.instance() == None or not QApplication.instance().verbose:
            return
        func(args)
    return wrapper

@require_qapp_verbose
def log(content):
    print(content)

