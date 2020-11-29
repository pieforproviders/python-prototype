def pad_hour(string):
    '''Adds leading zero to 12 hour time string'''
    try:
        if len(string.split(':')[0]) == 1:
            string = '0' + string
    # do nothing for nan
    except AttributeError:
        pass
    return string

if __name__ == '__main__':
    pass