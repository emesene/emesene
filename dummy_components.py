# a dummy implementation of extensions until we decide some details
# on the extension framework

categories = {}

def get_default(category_name):
    """
    return the default extension for the category name
    category_name -- the name of the category
    """
    return categories[category_name]

