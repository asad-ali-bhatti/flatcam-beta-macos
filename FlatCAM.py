import sys
import os

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QSettings, Qt
from app_Main import App
from appGUI import VisPyPatches

# Qt 5.15 segfaults in QScrollArea::ensureWidgetVisible() when takeWidget() reparents
# a widget whose child still has focus. Move focus out of the scroll area first.
_orig_take_widget = QtWidgets.QScrollArea.takeWidget


def _safe_take_widget(self):
    w = self.widget()
    if w is not None:
        focused = QtWidgets.QApplication.focusWidget()
        if focused is not None and (focused is w or w.isAncestorOf(focused)):
            focused.clearFocus()
            self.setFocus()
    return _orig_take_widget(self)


QtWidgets.QScrollArea.takeWidget = _safe_take_widget


# PyQt5 aborts the whole app on any unhandled exception raised in a slot or Qt virtual
# (e.g. an empty entry fed to float()). Print the traceback and keep running instead.
def _log_unhandled(exc_type, exc_value, exc_tb):
    import traceback
    traceback.print_exception(exc_type, exc_value, exc_tb)


sys.excepthook = _log_unhandled


# On macOS QFormLayout defaults to FieldsStayAtSizeHint; FlatCAM's spinners use an 'Ignored'
# horizontal size policy, so they collapse to zero width (e.g. Panelize Columns/Rows).
class _GrowingFormLayout(QtWidgets.QFormLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)


QtWidgets.QFormLayout = _GrowingFormLayout

from multiprocessing import freeze_support
# import copyreg
# import types

if sys.platform == "win32":
    # cx_freeze 'module win32' workaround
    pass

MIN_VERSION_MAJOR = 3
MIN_VERSION_MINOR = 5


def debug_trace():
    """
    Set a tracepoint in the Python debugger that works with Qt
    :return: None
    """
    from PyQt5.QtCore import pyqtRemoveInputHook
    # from pdb import set_trace
    pyqtRemoveInputHook()
    # set_trace()


if __name__ == '__main__':
    # All X11 calling should be thread safe otherwise we have strange issues
    # QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_X11InitThreads)
    # NOTE: Never talk to the GUI from threads! This is why I commented the above.
    freeze_support()

    major_v = sys.version_info.major
    minor_v = sys.version_info.minor
    # Supported Python version is >= 3.5
    if major_v >= MIN_VERSION_MAJOR:
        if minor_v >= MIN_VERSION_MINOR:
            pass
        else:
            print("FlatCAM BETA uses PYTHON 3 or later. The version minimum is %s.%s\n"
                  "Your Python version is: %s.%s" % (MIN_VERSION_MAJOR, MIN_VERSION_MINOR, str(major_v), str(minor_v)))

            if minor_v >= 8:
                os._exit(0)
            else:
                sys.exit(0)
    else:
        print("FlatCAM BETA uses PYTHON 3 or later. The version minimum is %s.%s\n"
              "Your Python version is: %s.%s" % (MIN_VERSION_MAJOR, MIN_VERSION_MINOR, str(major_v), str(minor_v)))
        sys.exit(0)

    debug_trace()
    # VisPyPatches.apply_patches()

    # apply High DPI support
    settings = QSettings("Open Source", "FlatCAM")
    if settings.contains("hdpi"):
        hdpi_support = settings.value('hdpi', type=int)
    else:
        hdpi_support = 0

    if hdpi_support == 2:
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    else:
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"

    # if hdpi_support == 2:
    #     tst_screen = QtWidgets.QApplication(sys.argv)
    #     if tst_screen.screens()[0].geometry().width() > 1930 or tst_screen.screens()[1].geometry().width() > 1930:
    #         QGuiApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    #         del tst_screen
    # else:
    #     QGuiApplication.setAttribute(Qt.AA_EnableHighDpiScaling, False)

    if hdpi_support == 2:
        QtWidgets.QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    else:
        QtWidgets.QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, False)

    app = QtWidgets.QApplication(sys.argv)
    # on macOS this also sets the Dock icon (otherwise the generic Python icon is shown)
    app.setWindowIcon(QtGui.QIcon('assets/resources/flatcam_icon256.png'))

    # apply style
    settings = QSettings("Open Source", "FlatCAM")
    if settings.contains("style"):
        style = settings.value('style', type=str)
        app.setStyle(style)

    fc = App(qapp=app)
    sys.exit(app.exec_())
    # app.exec_()
