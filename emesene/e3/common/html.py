'''classes to ease the creation of html documents'''

import xml.etree.ElementTree as ET

if callable(ET.Element):
    class Element(ET._ElementInterface, object):
        pass
else:
    class Element(ET.Element):
        pass

def quote(text):
    """encode html entities"""
    text = unicode(text)
    return text.translate({
        ord('&'): u'&amp;',
        ord('<'): u'&lt;',
        ord('"'): u'&quot;',
        ord('>'): u'&gt;',
        ord('@'): u'&#64;',
        0xa0: u'&nbsp;'})

def nop(text):
    return text

class TagBase(Element):
    "base class for all tags"

    SELF_CLOSING = False
    COMPACT = False
    QUOTE = True

    def __init__(self, childs, attrs):
        "add childs and call parent constructor"
        clean_attrs = dict([(key.rstrip("_"), val)
            for (key, val) in attrs.iteritems()])

        tag = self.__class__.__name__.lower()

        Element.__init__(self, tag, clean_attrs)

        for child in childs:
            if isinstance(child, basestring):
                if self.text is None:
                    self.text = self.maybe_quote(unicode(child))
                else:
                    self.text += self.maybe_quote(unicode(child))
            else:
                self.append(child)

    def maybe_quote(self, text):
        if self.QUOTE:
            return quote(text)
        else:
            return text

    def append(self, element):
        '''override Element.append to support appending strings'''

        if isinstance(element, basestring):
            if self.text is None:
                self.text = self.maybe_quote(element)
            else:
                self.text += self.maybe_quote(element)
        else:
            Element.append(self, element)

    def _format_child(self, child, level=0, increment=1, be_compact=False):
        """transform childs to string representations"""
        one_indent = " " * increment
        indent = one_indent * level
        cls = self.__class__

        nl = "\n"

        if cls.COMPACT or be_compact:
            nl = ""
            indent = ""
            one_indent = ""

        if isinstance(child, TagBase):
            result = child.format(level + 1, increment)
        else:
            child = unicode(child)

            child = self.maybe_quote(child)

            result = child
            indent = ""
            nl = ""
            one_indent = ""

        return indent + result + nl

    def format(self, level=0, increment=1, be_compact=False):
        "pretty print the object"
        one_indent = " " * increment
        indent = one_indent * level
        cls = self.__class__

        nl = "\n"

        if cls.COMPACT or be_compact:
            nl = ""
            indent = ""
            one_indent = ""

        attrs = " ".join(['%s="%s"' % (name, val)
            for (name, val) in self.attrib.iteritems()])

        if attrs:
            attrs = " " + attrs

        if self.text is None:
            childs = ""
        else:
            childs = self.text

        should_be_compact = False
        formatted = []
        for child in list(self):
            item = self._format_child(child, be_compact=should_be_compact)
            formatted.append(item)
            should_be_compact = isinstance(child, basestring)

        childs += "".join(formatted)

        if childs:
            childs = nl + childs + nl

        return self._format(indent, attrs, childs)

    def _format(self, indent, attrs, childs):
        cls = self.__class__

        if cls.SELF_CLOSING:
            return "%s<%s%s />" % (indent, self.tag, attrs)
        else:
            return "%s<%s%s>%s%s</%s>" % (indent, self.tag, attrs,
                    childs, indent, self.tag)

    def to_string(self, level=0):
        indent = " " * level
        attrs = " ".join(['%s="%s"' % (name, val)
            for (name, val) in self.attrib.iteritems()])

        accum = []

        for child in self:
            if hasattr(child, "to_string"):
                accum.append(child.to_string(level + 1))
            else:
                print "not a tag", child

        childs = "".join(accum)

        return "%s%s(%s) = %s\n%s" % (indent, self.tag, attrs, self.text,
            childs)

    def __repr__(self):
        self.to_string(0)

    def __str__(self):
        "return a string representation"
        return self.format(0)

class Comment(TagBase):

    def __init__(self, *childs, **attrs):
        TagBase.__init__(self, childs, attrs)

    def _format(self, indent, attrs, childs):
        return "%s<!--%s%s-->" % (indent, childs, indent)

TAGS = {
    "a": (True, True, False, "Defines a hyperlink"),
    "abbr": (True, False, False, "Defines an abbreviation"),
    "address": (True, False, False, "Defines an address element"),
    "area": (True, False, False, "Defines an area inside an image map"),
    "article": (True, False, False, "Defines an article"),
    "aside": (True, False, False, "Defines content aside from the page content"),
    "audio": (True, False, False, "Defines sound content"),
    "b": (True, False, False, "Defines bold text"),
    "base": (True, False, False, "Defines a base URL for all the links in a page"),
    "bdi": (True, False, False, "Defines text that is isolated from its surrounding"
        "text direction settings"),
    "bdo": (True, False, False, "Defines the direction of text display"),
    "blockquote": (True, False, False, "Defines a long quotation"),
    "body": (True, False, False, "Defines the body element"),
    "br": (True, False, True, "Inserts a single line break"),
    "button": (True, False, False, "Defines a push button"),
    "canvas": (True, False, False, "Defines graphics"),
    "caption": (True, False, False, "Defines a table caption"),
    "cite": (True, True, False, "Defines a citation"),
    "code": (True, False, False, "Defines computer code text"),
    "col": (True, False, False, "Defines attributes for table columns "),
    "colgroup": (True, False, False, "Defines groups of table columns"),
    "command": (True, False, False, "Defines a command button"),
    "datalist": (True, False, False, "Defines a list of options for an input field"),
    "dd": (True, False, False, "Defines a definition description"),
    "del": (True, False, False, "Defines deleted text"),
    "details": (True, False, False, "Defines details of an element"),
    "dfn": (True, False, False, "Defines a definition term"),
    "div": (True, False, False, "Defines a section in a document"),
    "dl": (True, False, False, "Defines a definition list"),
    "dt": (True, False, False, "Defines a definition term"),
    "em": (True, True, False, "Defines emphasized text "),
    "embed": (True, False, False, "Defines external interactive content or plugin"),
    "fieldset": (True, False, False, "Defines a fieldset"),
    "figcaption": (True, False, False, "Defines the caption of a figure element"),
    "figure": (True, False, False, "Defines a group of media content, and their caption"),
    "footer": (True, False, False, "Defines a footer for a section or page"),
    "form": (True, False, False, "Defines a form "),
    "h1": (True, True, False, "Defines header level 1"),
    "h2": (True, True, False, "Defines header level 2"),
    "h3": (True, True, False, "Defines header level 3"),
    "h4": (True, True, False, "Defines header level 4"),
    "h5": (True, True, False, "Defines header level 5"),
    "h6": (True, True, False, "Defines header level 6"),
    "head": (True, False, False, "Defines information about the document"),
    "header": (True, False, False, "Defines a header for a section or page"),
    "hgroup": (True, False, False, "Defines information about a section in a document"),
    "hr": (True, False, True, "Defines a horizontal rule"),
    "html": (True, False, False, "Defines an html document"),
    "i": (True, True, False, "Defines italic text"),
    "iframe": (True, False, False, "Defines an inline sub window (frame)"),
    "img": (True, False, True, "Defines an image"),
    "input": (True, False, True, "Defines an input field"),
    "ins": (True, False, False, "Defines inserted text"),
    "keygen": (True, False, False, "Defines a key pair generator field (for forms)"),
    "kbd": (True, False, False, "Defines keyboard text"),
    "label": (True, True, False, "Defines a label for a form control"),
    "legend": (True, False, False, "Defines a title in a fieldset"),
    "li": (True, False, False, "Defines a list item"),
    "link": (True, False, True, "Defines a resource reference"),
    "map": (True, False, False, "Defines an image map "),
    "mark": (True, False, False, "Defines marked text"),
    "menu": (True, False, False, "Defines a menu list"),
    "meta": (True, False, True, "Defines meta information"),
    "meter": (True, False, False, "Defines a scalar measurement within a known range"),
    "nav": (True, False, False, "Defines navigation links"),
    "noscript": (True, False, False, "Defines a noscript section"),
    "object": (True, False, False, "Defines an embedded object"),
    "ol": (True, False, False, "Defines an ordered list"),
    "optgroup": (True, False, False, "Defines an option group"),
    "option": (True, False, False, "Defines an option in a drop-down list"),
    "output": (True, False, False, "Defines the result of a calculation"),
    "p": (True, True, False, "Defines a paragraph"),
    "param": (True, False, False, "Defines a parameter for an object"),
    "pre": (True, True, False, "Defines preformatted text"),
    "progress": (True, False, False, "Represents the progress of a task"),
    "q": (True, False, False, "Defines a short quotation"),
    "rp": (True, False, False, "Used in ruby annotations to define what to show if a "
            "browser does not support the ruby element"),
    "rt": (True, False, False, "Defines explanation to ruby annotations"),
    "ruby": (True, False, False, "Defines ruby annotations"),
    "s": (True, True, False, "Defines text that is no longer correct"),
    "samp": (True, False, False, "Defines sample computer code"),
    "script": (False, True, False, "Defines a script"),
    "section": (True, False, False, "Defines a section"),
    "select": (True, False, False, "Defines a selectable list"),
    "small": (True, True, False, "Defines smaller text"),
    "source": (True, False, False, "Defines multiple media resources for media elements, "
            "such as audio and video"),
    "span": (True, True, False, "Defines a section in a document"),
    "strong": (True, True, False, "Defines strong text"),
    "style": (False, False, False, "Defines a style definition"),
    "sub": (True, True, False, "Defines subscripted text"),
    "summary": (True, False, False, "Defines the header of a 'detail' element"),
    "sup": (True, True, False, "Defines superscripted text"),
    "table": (True, False, False, "Defines a table"),
    "tbody": (True, False, False, "Defines a table body"),
    "td": (True, False, False, "Defines a table cell"),
    "textarea": (True, False, False, "Defines a text area"),
    "tfoot": (True, False, False, "Defines a table footer"),
    "th": (True, False, False, "Defines a table header"),
    "thead": (True, False, False, "Defines a table header"),
    "time": (True, False, False, "Defines a date/time"),
    "title": (True, False, False, "Defines the document title"),
    "tr": (True, False, False, "Defines a table row"),
    "track": (True, False, False, "Defines text tracks used in mediaplayers"),
    "ul": (True, False, False, "Defines an unordered list"),
    "var": (True, True, False, "Defines a variable"),
    "video": (True, False, False, "Defines a video or movie"),
    "wbr": (True, False, False, "Defines a possible line-break")
}

def create_tags(ctx):
    "create all classes and put them in ctx"

    for (tag, info) in TAGS.iteritems():
        class_name = tag.title()
        quote, compact, self_closing, docs = info

        def __init__(self, *childs, **attrs):
            TagBase.__init__(self, childs, attrs)

        cls = type(class_name, (TagBase,), {
            "__doc__": docs,
            "__init__": __init__
        })

        cls.SELF_CLOSING = self_closing
        cls.COMPACT = compact
        cls.QUOTE = quote

        ctx[class_name] = cls

create_tags(globals())

HEADINGS = {
    1: H1,
    2: H2,
    3: H3,
    4: H4,
    5: H5,
    6: H6
}
