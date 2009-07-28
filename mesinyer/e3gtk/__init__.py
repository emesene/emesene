
import extension

def main(Controller):
    """
    main method for gtk frontend
    """
    import gtk
    import gobject

    import Login
    import Dialog
    import Header
    import Window
    import TextBox
    import MainMenu
    import TrayIcon
    import UserPanel
    import TabWidget
    import GroupMenu
    import StatusMenu
    import MainWindow
    import AccountMenu
    import ContactMenu
    import ContactList
    import ContactInfo
    import Preferences
    import Conversation
    import WebKitTextBox
    import ConversationManager
    import ConversationToolbar
    import DebugWindow
    import PluginWindow

    setup()
    gobject.threads_init()
    gtk.gdk.threads_init()
    gtk.gdk.threads_enter()
    controller = Controller()
    controller.start()
    gtk.quit_add(0, controller.on_close)
    gtk.main()
    gtk.gdk.threads_leave()

extension.category_register('gtk main', main)

def setup():
    """
    define all the components for a gtk environment
    """
    extension.category_register('dialog', Dialog.Dialog)
    extension.category_register('preferences', Preferences.Preferences)
    extension.category_register('login window', Login.Login)
    extension.category_register('window frame', Window.Window)
    extension.category_register('main window', MainWindow.MainWindow)
    extension.category_register('contact list', ContactList.ContactList)
    extension.category_register('user panel', UserPanel.UserPanel)
    extension.category_register('tray icon', TrayIcon.TrayIcon)
    extension.category_register('debug window', DebugWindow.DebugWindow)

    extension.category_register('main menu', MainMenu.MainMenu)
    extension.category_register('menu file', MainMenu.FileMenu)
    extension.category_register('menu actions', MainMenu.ActionsMenu)
    extension.category_register('menu options', MainMenu.OptionsMenu)
    extension.category_register('menu contact', ContactMenu.ContactMenu)
    extension.category_register('menu group', GroupMenu.GroupMenu)
    extension.category_register('menu account', AccountMenu.AccountMenu)
    extension.category_register('menu help', MainMenu.HelpMenu)
    extension.category_register('menu status', StatusMenu.StatusMenu)

    extension.category_register('conversation window', \
        ConversationManager.ConversationManager)
    extension.category_register('conversation', Conversation.Conversation)
    extension.category_register('conversation header', Header.Header)
    extension.category_register('conversation info', ContactInfo.ContactInfo)
    extension.category_register('conversation tab', TabWidget.TabWidget)
    extension.category_register('conversation input', TextBox.InputText)
    extension.category_register('conversation toolbar', \
        ConversationToolbar.ConversationToolbar)
    extension.category_register('plugin window', \
        PluginWindow.PluginWindow)

    if not WebKitTextBox.ERROR:
        extension.category_register('conversation output', WebKitTextBox.OutputText)
        extension.register('conversation output', TextBox.OutputText)
    else:
        extension.category_register('conversation output', TextBox.OutputText)

