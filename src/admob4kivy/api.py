from typing import Protocol, runtime_checkable, Callable

import inspect

@runtime_checkable
class AdmobAPI(Protocol):
    
    def load_banner(self, ad_unit: str, top: bool):
        pass

    def show_banner(self):
        pass

    def hide_banner(self):
        pass
    
    def load_interstitial(self, ad_unit: str):
        pass

    def show_interstitial(self):
        pass

    def load_rewarded(self, ad_unit: str):
        pass

    def show_rewarded(self):
        pass


def check_api(cls: AdmobAPI):
    api = AdmobAPI
    if not isinstance(cls, api):
        print(f"[Error]:\n\t{cls.__class__.__name__} has wrong api")
        #raise Exception
        return
    
    
    __class__ = cls.__class__
    proto_dir = dir(api)
    
    for item in dir(__class__):
        obj = getattr(__class__, item)
        if not inspect.isfunction(obj): continue
        if not (item.startswith("__") and item.endswith("__")):
            if item in proto_dir:
                
                cls_sig = inspect.signature(obj)
                print(f"checking {item}{cls_sig}")
                api_sig = inspect.signature(getattr(api, item))
                cls_parameters = cls_sig.parameters
                api_parameters = api_sig.parameters
                if cls_parameters != api_parameters:
                    print(f"[Error]:\n\t{__class__.__name__}.{item}{cls_sig}\n\n\t\t is not matching \n\n\t{api.__name__}.{item}{api_sig}")
                    return
    print("api is ok")