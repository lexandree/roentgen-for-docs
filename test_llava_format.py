import inspect
try:
    from llama_cpp.llama_chat_format import Llava15ChatHandler
    print(inspect.getsource(Llava15ChatHandler))
except Exception as e:
    print(e)
