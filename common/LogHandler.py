#-----------------------------------------------------------------------
# Script run and Audit log function for all scripts
# nram, Solace PSG
#

import os, sys, traceback
import logging
import time
import json

def ts(mode=1):
    if mode == 0:
        return 'now'
    return time.strftime("%Y%m%d-%H%M%S")

class LogHandler :
   'Common Logger wrapper implementtion'

   # ------------------t
   # init
   #
   def __init__ (self, cfg):
         
         self.m_appname = cfg['script_name']
         self.m_verbose = cfg['verbose']
         logdir = cfg['system']['system']['logDir']

         #ts = 'now' # for testing
         self.m_logfile = './{}/{}-{}.log'.format(logdir, self.m_appname, ts())
         print (f'opening log file for appname: {self.m_appname} logfile: {self.m_logfile}')
         self.m_init = False
         # create log dir if it doesn't exist
         os.makedirs(logdir, exist_ok=True)
         self.setup()

    #   def notice(self, message, *args, **kws):
    #   logger takes its '*args' as 'args'.
    #       if self.isEnabledFor(DEBUG_LEVELV_NUM):
    #           self._log(DEBUG_LEVELV_NUM, message, args, **kws) 
   
   # ------------------------------------------------------------------------------
   # setup logger 
   # logger levels:
   # CRIT   - 50 
   # ERROR  - 40 
   # NOTICE - 34 	(custom)
   # AUDIT -  33 	(custom)
   # STATUS - 32 	(custom)
   # WARN   - 30
   # INFO   - 20
   # DEBUG  - 10
   # ENTER  - 6	  (custom)
   # TRACE  - 5   (custom)
   # NOTSET - 0

   def setup(self):
      # custom levels

      logging.TRACE = 5  # trace 
      logging.addLevelName(logging.TRACE, 'TRACE') 
      logging.ENTER = 6  # trace - enter funciton 
      logging.addLevelName(logging.ENTER, 'ENTER') 
      logging.STATUS = 32  # status 
      logging.addLevelName(logging.STATUS, 'STATUS') 
      #logging.AUDIT = 33  # audit log 
      #logging.addLevelName(logging.STATUS, 'AUDIT') 
      logging.NOTICE = 34  # positive yet important 
      logging.addLevelName(logging.NOTICE, 'NOTICE')
      logging.addLevelName(logging.CRITICAL, 'FATAL') # rename existing

      self.m_logger = logging.getLogger(self.m_appname)

      self.m_logger.trace = lambda msg, *args: self.m_logger._log(logging.TRACE, msg, args)
      # additional traces
      self.m_logger.dump_json = lambda msg, *args: self.m_logger._log(logging.TRACE, msg, json.dumps(args, indent=2))
      self.m_logger.dump_list = lambda msg, *args: self.m_logger._log(logging.TRACE, msg, json.dumps(list(args), indent=2))
      self.m_logger.dump_yaml = lambda msg, *args: self.m_logger._log(logging.TRACE, msg, json.dumps(args, indent=2))
      self.m_logger.dump_xml = lambda msg, *args: self.m_logger._log(logging.TRACE, msg, json.dumps(args, indent=2))

      #self.m_logger.audit = lambda msg, *args: self.m_logger._log(logging.AUDIT, msg, args)
      self.m_logger.notice = lambda msg, *args: self.m_logger._log(logging.NOTICE, msg, args)
      self.m_logger.status = lambda msg, *args: self.m_logger._log(logging.STATUS, msg, args)
      self.m_logger.enter = lambda msg, *args: self.m_logger._log(logging.ENTER, msg, args)
      self.m_logger.setLevel(logging.INFO)

      formatter = logging.Formatter('%(asctime)s : %(name)s [%(levelname)s] %(message)s')

      stream_formatter = logging.Formatter('[%(levelname)s] %(message)s')

      #stream_formatter = logging.Formatter('%(message)s')

      # file handler
      fh = logging.FileHandler(self.m_logfile)
      fh.setLevel(logging.INFO)
      if self.m_verbose > 2 :
         print ("** Setting file log level to TRACE ***")
         fh.setLevel(logging.TRACE)
         self.m_logger.setLevel(logging.TRACE)
      elif self.m_verbose > 0 :
         print ("** Setting file log level to DEBUG ***")
         fh.setLevel(logging.DEBUG)
         self.m_logger.setLevel(logging.DEBUG)
      fh.setFormatter(formatter)
      self.m_logger.addHandler(fh)

      # stream handler -- log at higher level
      ch1 = logging.StreamHandler(sys.stdout)
      ch1.setLevel(logging.WARNING)
      
      ch2 = logging.StreamHandler(sys.stderr)
      ch2.setLevel(max(logging.DEBUG, logging.ERROR))

      if self.m_verbose > 0 :
         #print ("** Setting stream log level to INFO ***")
         ch1.setLevel(logging.INFO)
         #self.m_logger.setLevel(logging.INFO)
      ch1.setFormatter(stream_formatter)
      self.m_logger.addHandler(ch1)
      self.m_logger.addHandler(ch2)

      self.m_init = True

   # ------------------------------------------------------------------------------
   # returen logging.logger to apps
   #
   def get(self, name=None):
      if not self.m_init:
         print ("Logging not initialized")
         return None
      if name == None:
         #print "Returning saved logger"
         return self.m_logger
      #print "Returning logger for ", name
      return logging.getLogger(name)

   def logfile(self):
          return self.m_logfile ;
   
   # this should be called on log_h object, not log object
   # log_h.crit_exit ('string')  
   def crit_exit (self, s):
      log = self.log
      log.crit('*** Exiting on CRITICAL Error ***')
      log.error(s)
      log.debug('------------ STACK TRACE ------------')
      log.debug(' '.join(traceback.format_stack()))
      exit()
      
   def err_exit (self, s, e = None):
      log = self.m_logger
      log.error('*** Exiting on Error ***')

      log.error(s)
      if e:
         log.error(str(e))
         log.notice(f'Please see logfile {self.m_logfile} for trace info')
         log.debug('------------ CALL TRACE ------------')
         log.debug(' '.join(traceback.format_stack()))
         
         log.debug('------------ STACK TRACE ------------')
         fh = open(self.m_logfile, 'a')
         traceback.print_exc(file=fh)
         fh.close()

      sys.exit(2)