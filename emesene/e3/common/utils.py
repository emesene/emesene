import MessageFormatter

def add_style_to_message(text, stl, escape=True):
    '''add the style in a xhtml like syntax to text'''
    style_start = ''
    style_end = ''
    style = 'color: #' + stl.color.to_hex() + ';'

    if stl.bold:
        style_start = style_start + '<b>'
        style_end = '</b>' + style_end

    if stl.italic:
        style_start = style_start + '<i>'
        style_end = '</i>' + style_end

    if stl.underline:
        style_start = style_start + '<u>'
        style_end = '</u>' + style_end

    if stl.strike:
        style_start = style_start + '<s>'
        style_end = '</s>' + style_end

    if stl.font:
        style += 'font-family: ' + stl.font

    style_start += '<span style="%s; ">' % (style, )
    style_end = '</span>' + style_end

    if escape:
        text = MessageFormatter.escape(text)

    return style_start + text + style_end

