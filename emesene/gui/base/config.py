
class Base(object):
    '''the base class for the config items'''

    def __init__(self, name, description):
        self.name = name
        self.description = description

class Group(Base):
    '''a class that represents a group of items'''

    def __init__(self, name, description, *items):
        Base.__init__(self, name, description)
        self.items = list(items)

    def add(self, item):
        '''add an item to the group'''
        self.items.append(item)

    def validate(self):
        '''validate all the childs'''

        for child in self.items:
            result = child.validate()

            if not result[0]:
                return result

        return (True, 'OK')

class Logic(Group):
    '''a class that represents a group of items'''

    def __init__(self, name, description, *items):
        Group.__init__(self, name, description, *items)
        self.frame_hint = False

class Sections(Group):
    '''a class that represents a group of items'''

    def __init__(self, name, description, *items):
        Group.__init__(self, name, description, *items)

class Options(Group):
    '''a class that represents a group of items'''

    def __init__(self, name, description, radio_hint, *items):
        Group.__init__(self, name, description, *items)
        self.radio_hint = radio_hint

class Item(Base):
    '''a class that represents a item that can contain a value'''

    def __init__(self, name, description, value=None, default=None):
        Base.__init__(self, name, description)
        self.value = value
        self.default = default
        self.validators = []

    def validate(self):
        '''validate all the childs'''
        new_value = self._get_gui_value()

        for validator in self.validators:
            result = validator(new_value)

            if not result[0]:
                return result

        self.value = new_value
        return (True, 'OK')

    def add_validator(self, validator):
        '''add a method that receives the value as paramenter and returns a
        tuple with a boolean as first element that is True if the validation
        passed and false if not. the second is a string representing a message
        to be show if the validation fails'''
        self.validators.append(validator)

    def _get_gui_value(self):
        '''return the new value from the gui, you must overload this method
        on your gui implementations'''
        return self.value

class Text(Item):
    '''a config item that contains text'''

    def __init__(self, name, description, value=None, default=None):
        Item.__init__(self, name, description, value, default)

class Bool(Item):
    '''a config item that contains a boolean value'''

    def __init__(self, name, description, value=None, default=None):
        Item.__init__(self, name, description, value, default)

class Password(Item):
    '''a config item that contains a password'''

    def __init__(self, name, description, value=None, default=None):
        Item.__init__(self, name, description, value, default)

class Option(Item):
    '''a config item that contains an option'''

    def __init__(self, name, description, value=None, default=None):
        Item.__init__(self, name, description, value, default)

class Info(Base):
    '''a config item that contains a information (no value is inserted)'''

    def __init__(self, name, description):
        Base.__init__(self, name, description)

    def validate(self):
        '''dummy method'''
        return (True, '')

