#!/usr/bin/env python3
import logging
import os
import sys
import inspect
from logging.handlers import RotatingFileHandler
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
####################################
# written by:   Tim Smith
# e-mail:       tismith@extremenetworks.com
# date:         28 Aug 2025
# version:      3.0.0
####################################


# check for logs directory and create if missing
os.makedirs('{}/script_logs'.format(current_dir), exist_ok=True) 
log_dir = '{}/script_logs'.format(current_dir)

# Custom filter to exclude file-only messages from StreamHandler
class NoFileOnlyFilter(logging.Filter):
    def filter(self, record):
        # Return False to exclude the record, True to include it
        return not getattr(record, 'file_only', False)
    
class CustomFormatter(logging.Formatter):
	# Git Shell Coloring - https://gist.github.com/vratiu/9780109
	GREY = "\x1b[38;20m"
	RED   = "\033[1;31m"  
	BLUE  = "\033[1;34m"
	GREEN = "\033[0;32m"
	YELLOW = "\033[0;33m"
	BOLD_RED = "\x1b[31;1m"
	RESET = "\033[0;0m"
	format = '%(levelname)s: %(message)s'
	
	FORMATS = {
	        logging.DEBUG: GREEN + format + RESET,
	        logging.INFO: BLUE + format + RESET,
	        logging.WARNING: YELLOW + format + RESET,
	        logging.ERROR: RED + format + RESET,
	        logging.CRITICAL: BOLD_RED + format + RESET
	    }
	
	def format(self, record):
		log_fmt = self.FORMATS.get(record.levelno)
		formatter = logging.Formatter(log_fmt)
		return formatter.format(record)
	
logger = logging.getLogger()
logger.setLevel(logging.DEBUG) # this is needed to get all levels, and therefore filter on each handler


PATH = os.path.dirname(os.path.abspath(__file__))
log_formatter = logging.Formatter('%(asctime)s: %(name)s - %(levelname)s - %(message)s')

logFile = '{}/XIQ-GSuite-PPSK-sync.log'.format(log_dir)

fileHandler = RotatingFileHandler(logFile, mode='a', maxBytes=5*1024*1024*1024,
                                 backupCount=5, encoding=None, delay=0)

fileHandler.setFormatter(log_formatter)
fileHandler.setLevel(logging.DEBUG)
logger.addHandler(fileHandler)


# create console handler for logger.
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setLevel(level=logging.INFO)
consoleHandler.addFilter(NoFileOnlyFilter())  # Exclude file-only messages
consoleHandler.setFormatter(CustomFormatter())
logger.addHandler(consoleHandler)