import errno
import os


def mkdir_p(path, filename_included=False):
    """
    Function: mkdir_p
    Input:
        path - the path of the dir to be created
    Output: none
    Functionality: Emulates mkdir -p functionality in unix which doesn't care
                   if a dir already exists and creates parent dirs if needed
    Author: TZ[omega]TZIOY
    Reference: http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
    :param path:
    :param filename_included:
    """

    if filename_included:
        path = os.path.dirname(path)
    try:
        os.makedirs(path)  # just make all dirs in path
    except OSError as exc:  # unless you get an error... # Python >2.5
        if exc.errno == errno.EEXIST:  # and that errors no is the path exists
            pass  # that you can ignore
        else:
            raise  # otherwise re-raise error

    return path
