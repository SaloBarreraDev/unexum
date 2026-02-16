from kivy.utils import platform
from kivy.clock import mainthread

if platform == 'android':
    from kivy.uix.button import Button
    from kivy.uix.modalview import ModalView
    from kivy.clock import Clock
    from android import api_version, mActivity # type: ignore
    from android.permissions import request_permissions, check_permission, Permission # type: ignore

#########################################################################
#
# The start_app callback may occur up to two timesteps after this class
# is instantiated. So the class must exist for two time steps, if not the
# callback will not be called.
#
# To defer garbage collection, instantiate this class with a class variable:
#
#  def on_start(self):
#     self.dont_gc = AndroidPermissions(self.start_app)
#
#  def start_app(self):
#     self.dont_gc = None
#
###########################################################################
#
# Android Behavior:
#
#  If the user selects "Don't Allow", the ONLY way to enable
#  the disallowed permission is with App Settings.
#  This class give the user an additional chance if "Don't Allow" is
#  selected once.
#
###########################################################################

class AndroidPermissions:
    def __init__(self, start_app = None):
        self.permission_dialog_count = 0
        self.start_app = start_app
        if platform == 'android':
            #################################################
            # Customize run time permissions for the app here
            #################################################
            if api_version < 29:
                # Android < 10
                # Permission to write to Shared Storage
                self.permissions = [Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE]
            else:
                # Android >= 10
                self.permissions = [Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE]
                #################################################
            self.permission_status([],[])
        elif self.start_app:
            self.start_app()

    def permission_status(self, permissions, grants):
        granted = True
        for p in self.permissions:
            granted = granted and check_permission(p)
        if granted:
            if self.start_app:
                self.start_app()
        elif self.permission_dialog_count < 2:
            Clock.schedule_once(self.permission_dialog)
            
        
    def permission_dialog(self, dt):
        self.permission_dialog_count += 1
        request_permissions(self.permissions, self.permission_status)

    def bye(self):
        mActivity.finishAndRemoveTask() 
        
