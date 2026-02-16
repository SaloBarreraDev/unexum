from .api import AdmobAPI
from .backends import AdmobBackend #type: ignore

class AdmobManager:
    def __init__(self, callback=None):
        self.platform_manager: AdmobAPI = AdmobBackend(callback)

    def load_banner(self, ad_unit_id, top=True):
        return self.platform_manager.load_banner(ad_unit_id, top)

    def show_banner(self):
        return self.platform_manager.show_banner()

    def hide_banner(self):
        return self.platform_manager.hide_banner()

    def load_interstitial(self, ad_unit_id):
        return self.platform_manager.load_interstitial(ad_unit_id)

    def show_interstitial(self):
        return self.platform_manager.show_interstitial()

    def load_rewarded(self, ad_unit_id):
        return self.platform_manager.load_rewarded(ad_unit_id)

    def show_rewarded(self):
        return self.platform_manager.show_rewarded()
    
class TestIDs:
    # Google-provided test ad unit IDs
    APP = "ca-app-pub-3940256099942544~3347511713"
    BANNER = "ca-app-pub-3940256099942544/6300978111"
    INTERSTITIAL = "ca-app-pub-3940256099942544/1033173712"
    REWARDED = "ca-app-pub-3940256099942544/5224354917"