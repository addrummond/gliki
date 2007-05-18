import my_utils
import time

LOG_DIR = 'logs'

# Some standard log names.
EDITS_LOG = 'edits'
INTERNAL_LOG = 'internal'

LOGGING_ON = True

def log(logname, text):
    assert not ('/' in logname)
    if LOGGING_ON:
        try:
            f = open(LOG_DIR + '/' + logname, "a")
            f.write(my_utils.standard_date_format(time.gmtime()) + ': ' + text)
            if text[len(text) -1] != '\n':
                f.write('\n')
            f.close()
        except IOError:
            pass

