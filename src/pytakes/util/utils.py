import collections


def remaining_time(complete, total, start_time, end_time, format_='%Y-%m-%d %H:%M:%S,%f'):
    """
    Utility function for determining average length of time for each unit.

    Parameters:
        complete- int, how many of total have been completed
        total - int, total number of instances to be completed
        start_time - time as string when process started
        end_time - time as string when process completed
        format - format in which times are encoded
    """
    from datetime import datetime, timedelta
    percent = float(total) / float(complete)
    start = datetime.strptime(start_time, format_)
    end = datetime.strptime(end_time, format_)
    diff = end - start
    total_time = timedelta(seconds=int(percent * diff.total_seconds()))
    return str(total_time - diff)


def recursively_output_dictionary(d, out, padding='\t'):
    """
    Recursively list out an embedded dictionary. Write
    the result to out with padding for each level of
    embeddedness.

    Parameters:
        d - embedded dictionary
        out - output file ready for writing, or sys.stdout, etc.
        padding - amount of new indentation for each level of embedding
        :param d:
        :param out:
        :param padding:
    """
    out.write(recursive_dict_to_string(d, padding))


def recursive_dict_to_string(d, padding='\t'):
    """
    Recursively list out an embedded dictionary. Return as string.

    Parameters:
        d - embedded dictionary
        padding - amount of new indentation for each level of embedding

    Return:
        string representation of embedded dictionary
        :param d:
        :param padding:
    """
    return '\n'.join(_recursive_dict_to_string(d, padding))


def _recursive_dict_to_string(d, padding, curr_pad=''):
    """
    Helper method for recursive_dict_to_string containing recursive aspect.

    Parameters:
        d - embedded dictionary
        padding - amount of new indentation for each level of embedding
        curr_pad - the amount of padding for the current depth

    Return:
        list representation of embedded dictionary
        each item represents a newline.
    """
    if isinstance(d, dict):
        results = []
        for key in sorted(d):
            if isinstance(d[key], dict):
                results += [curr_pad + str(key)]
                results += _recursive_dict_to_string(d[key], padding, curr_pad + padding)
            else:
                results += [curr_pad + str(key) + padding + str(d[key])]

        return results
    else:
        return [str(d)]


def get_valid_args(func, dct):
    argnames = func.__code__.co_varnames[:func.__code__.co_argcount]
    return dict((key, val) for key, val in list(dct.items()) if key in argnames)


def flatten(it):
    for x in it:
        if (isinstance(x, collections.Iterable) and
                not isinstance(x, str)):
            yield from flatten(x)
        else:
            yield x
