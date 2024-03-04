from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile , QWebEnginePage
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QUrl, QSettings
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtGui import QIcon
from PyQt5 import QtWidgets

from controller import Controller
import shutil
import os

class Webview(QWebEngineView):
    def __init__(self, parent: QtWidgets.QWidget | None = ...) -> None:
        self.controller_channel:QWebChannel = None
        super().__init__(parent)
    
    def reload(self) -> None:
        self.page().setWebChannel(self.controller_channel)
        return super().reload()

# sobrescreve as funções de log javascript do QWebEnginePage para que as saídas geradas ignoradas
# é assim que o programa consegue executar sem precisar de stdout do terminal

class LogCapturingPage(QWebEnginePage):
    def consoleMessage(self, level, message, lineNumber, sourceID):
        pass
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        pass
    

class MainWindow(QMainWindow):
    def __init__(self, accounts_page, signals, app, controller:Controller):
        super().__init__()
        self.app = app
        self.settings = QSettings("maturador", "cache")
        try:
            self.move(self.settings.value('win_dashboard_position'))
            accounts_page.move(self.settings.value('win_accounts_position'))
        except:
            pass
        self.accounts_page = accounts_page
        self.signals = signals
        self.setWindowTitle("Maturador de chips - Dashboard")
        self.main_engine:QWebEnginePage
        self.setFixedSize(767, 620)
        self.webview = Webview(self)
        cache_dir = os.getcwd() + "/sessions/cache"
        profile = QWebEngineProfile("gui_cache", self.webview)
        profile.setCachePath(cache_dir)
        profile.setPersistentStoragePath(cache_dir)
        profile.setDownloadPath(cache_dir)
        profile.setPersistentCookiesPolicy(QWebEngineProfile.AllowPersistentCookies)
        profile.setHttpAcceptLanguage("pt-br")
        engine = LogCapturingPage(profile, self.webview)
        channel = QWebChannel(engine)
        channel.registerObject("controller",controller)
        self.webview.controller_channel = channel
        engine.setWebChannel(channel)
        self.webview.setPage(engine)
        self.webview.load(QUrl.fromLocalFile("/pages/dashboard.html"))
        self.webview.page().action(QWebEnginePage.Back).setVisible(False)
        self.webview.page().action(QWebEnginePage.Reload).setVisible(False)
        self.webview.page().action(QWebEnginePage.WebAction.SavePage).setVisible(False)
        self.webview.page().action(QWebEnginePage.WebAction.CopyImageToClipboard).setVisible(False)
        self.webview.page().action(QWebEnginePage.WebAction.CopyImageUrlToClipboard).setVisible(False)
        self.webview.page().action(QWebEnginePage.WebAction.Forward).setVisible(False)
        self.webview.page().action(QWebEnginePage.WebAction.ViewSource).setVisible(False)
        self.webview.page().action(QWebEnginePage.WebAction.CopyLinkToClipboard).setVisible(False)
        self.webview.page().action(QWebEnginePage.WebAction.OpenLinkInNewTab).setVisible(False)
        self.webview.page().action(QWebEnginePage.WebAction.OpenLinkInThisWindow).setVisible(False)
        self.webview.page().action(QWebEnginePage.WebAction.DownloadLinkToDisk).setVisible(False)
        self.webview.page().action(QWebEnginePage.WebAction.OpenLinkInNewBackgroundTab).setVisible(False)
        self.webview.page().action(QWebEnginePage.WebAction.OpenLinkInNewWindow).setVisible(False)
        self.setWindowIcon(QIcon("pages/assets/medias/icon.ico"))
        self.setCentralWidget(self.webview)
        self.main_engine = engine
    
    def closeEvent(self, event):
        self.signals.stop_maturation.emit()
        {engine.deleteLater() for engine in self.accounts_page.webs_engine}
        self.accounts_page.close()
        self.main_engine.deleteLater()
        self.app.destroyed.connect(
            lambda _: [shutil.rmtree(session_path) for session_path in self.accounts_page.sessions_waiting_to_be_disconnected]
        )
        self.settings.setValue(
            'win_dashboard_position',
            self.pos()
        )
        self.settings.setValue(
            'win_accounts_position',
            self.accounts_page.pos()
        )
        event.accept()