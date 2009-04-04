import gtk

import gui.config as config

SPACING = 2
BORDER = 2

def build(item):
    '''build an item'''

    itype = type(item)

    if itype == config.Logic:
        return build_logic(item)
    elif itype == config.Sections:
        return build_sections(item)
    elif itype == config.Options:
        return build_options(item)
    elif itype == config.Text:
        return build_text(item)
    elif itype == config.Bool:
        return build_bool(item)
    elif itype == config.Password:
        return build_password(item)
    elif itype == config.Info:
        return build_info(item)

def build_logic(item):
    '''create the gtk representation of the item as a collection of widgets'''
    widget = gtk.VBox()
    widget.set_spacing(SPACING)
    widget.set_border_width(BORDER)

    for child in item.items:
        expand = True

        if type(child) == config.Options and not child.radio_hint:
            expand = False

        widget.pack_start(build(child), expand)

    if item.frame_hint:
        frame = gtk.Frame(item.name)
        frame.add(widget)
        frame.set_border_width(SPACING)
        return frame

    return widget

def build_sections(item):
    '''create the gtk representation of the item as a set of tabs'''
    widget = gtk.Notebook()
    widget.set_scrollable(True)

    for child in item.items:
        page = build(child)
        widget.append_page(page, gtk.Label(child.name))
        widget.set_tab_reorderable(page, True)

    return widget

def build_options(item):
    '''create the gtk representation of the item as a set of options'''
    if item.radio_hint:
        return build_radios(item)
    else:
        return build_combo(item)

def build_radios(item):
    '''create the gtk representation of the item as a set of radio items'''
    widget = gtk.VBox()
    widget.set_spacing(SPACING)
    widget.set_border_width(BORDER)
    first_radio = gtk.RadioButton(None, item.items[0].name)
    item.items[0]._get_gui_value = lambda: first_radio.get_active()
    widget.pack_start(first_radio, False)

    for child in item.items[1:]:
        radio = gtk.RadioButton(first_radio, child.name)

        child._get_gui_value = lambda: radio.get_active()
        radio.set_active(child.value)
        widget.pack_start(radio)

    frame = gtk.Frame(item.name)
    frame.add(widget)
    frame.set_border_width(SPACING)
    return frame

def build_combo(item):
    '''create a gtk representation of the item as a combo'''
    widget = _box_and_label(item.name)
    combo = gtk.combo_box_new_text()
    selected = 0

    for (index, child) in enumerate(item.items):
        combo.append_text(child.name)

        def get_value(combo, child):
            def get():
                return combo.get_active_text() == child.name

            return get

        child._get_gui_value = get_value(combo, child)
        
        if child.value:
            selected = index

    combo.set_active(selected)

    widget.pack_start(combo)
    return widget

def build_text(item):
    '''create the gtk representation of the item as a text field and a label'''
    widget = _box_and_label(item.name)

    entry = gtk.Entry()
    entry.set_text(item.value)
    
    item._get_gui_value = lambda: entry.get_text()

    widget.pack_start(entry)

    return widget

def build_bool(item):
    '''create the gtk representation of the item as a checkbox with a label'''
    widget = gtk.CheckButton(item.name)
    widget.set_active(item.value)

    item._get_gui_value = lambda: widget.get_active()

    return widget

def build_password(item):
    '''create the gtk representation of the item as a textfield and a label
    where the textfield hides the content'''
    widget = _box_and_label(item.name)

    entry = gtk.Entry()
    entry.set_text(item.value)
    entry.set_visibility(False)

    item._get_gui_value = lambda: entry.get_text()

    widget.pack_start(entry)

    return widget

def build_info(item):
    '''create the gtk representation of the item as a label with some text'''
    widget = gtk.Label(item.name)

    return widget

def build_window(item):
    '''build a window and add the item to the window, add buttons and
    validations'''
    window = gtk.Window()
    window.set_title(item.name)

    box = gtk.VBox()
    box.set_spacing(SPACING)
    box.set_border_width(BORDER)
    box.pack_start(build(item), True, True)

    buttons = gtk.HButtonBox()
    b_ok = gtk.Button(stock=gtk.STOCK_OK)
    b_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)

    b_ok.connect('clicked', _validate, window, item)
    b_cancel.connect('clicked', lambda widget: window.hide())

    buttons.pack_start(b_cancel)
    buttons.pack_start(b_ok)

    box.pack_start(buttons, False)

    window.add(box)
    box.show_all()

    return window

def _validate(widget, window, item):
    '''validate and update all the items'''
    item.validate()
    window.hide()

def _box_and_label(text):
    '''build a hbox with a label'''
    widget = gtk.HBox(homogeneous=True)
    widget.set_spacing(SPACING)
    widget.set_border_width(BORDER)

    label = gtk.Label(text)
    label.set_alignment(0.0, 0.5)

    widget.pack_start(label)

    return widget

if __name__ == '__main__':
    main = config.Sections('Configuration', '')
    gui = config.Logic('Gui', 'the gui configuration')
    plugins = config.Logic('Plugins', 'plugins stuff')

    user = config.Text('user', 'the username', 'foo@bar.com', 'foo@bar.com')
    passwd = config.Password('password', 'the passwd', 'secret', 'default')
    use_proxy = config.Bool('use proxy', 'Check if you use proxy', False, False)

    proxy_group = config.Logic('Proxy settings', 'the config of the proxy')
    proxy_group.frame_hint = True

    host = config.Text('host', '', '192.168.0.1', '127.0.0.1')
    port = config.Text('port', '', '3127', '3127')

    proxy_group.add(host)
    proxy_group.add(port)

    gui.add(user)
    gui.add(passwd)
    gui.add(use_proxy)
    gui.add(proxy_group)

    info = config.Info('this is just information', 'some more information')

    combo = config.Options('allow plugins?', '...', False)
    yeah = config.Option('yeah!', '', False)
    nope = config.Option('nope..', '', True)

    combo.add(yeah)
    combo.add(nope)

    radio = config.Options('Orly?', '', True)
    rly = config.Option('rly', '', False)
    yeahrly = config.Option('yeah rly', '', True)
    radio.add(rly)
    radio.add(yeahrly)

    plugins.add(info)
    plugins.add(combo)
    plugins.add(radio)

    main.add(gui)
    main.add(plugins)

    build_window(main).show()
    gtk.main()
