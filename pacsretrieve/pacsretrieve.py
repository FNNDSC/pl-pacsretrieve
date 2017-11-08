#!/usr/bin/env python3
#
# (c) 2016 Fetal-Neonatal Neuroimaging & Developmental Science Center
#                   Boston Children's Hospital
#
#              http://childrenshospital.org/FNNDSC/
#                        dev@babyMRI.org
#

str_version = "1.1.2"

str_name = """
    NAME

        pacsretrieve.py
"""
str_synposis = """

    SYNOPSIS

        pacsretrieve.py --pfdcm <PACserviceIP:port>             \\
                        [--version]                             \\
                        [--msg <jsonMsgString>]                 \\
                        [--action retrieve|query]               \\
                        # For retrieve...                       \\
                        [--priorHitsTable <hitsTable>]          \\
                        [--indexList <commaseparatedlist>]      \\
                        # For query...                          \\
                        [--patientID <patientID>]               \\
                        [--PACSservice <PACSservice>]           \\
                        [--summaryKeys <keylist>]               \\
                        [--summaryFile <summaryFile>]           \\
                        [--resultFile <resultFile>]             \\
                        [--numberOfHitsFile <numberOfHitsFile>] \\
                        # Mandatory positional args             \\                       
                        <inputdir>
                        <outputdir>
"""
str_description = """

    DESCRIPTION

    'pacsretrieve.py' is a "DataService" (DS) ChrisApp plugin that is used
    to retrieve data from a PACS. Although it is called explicitly a 'retrieve'
    plugin, please note that it actually contains all the code from the
    pacsquery plugin and as such can also perform queries and understands
    all the pacsquery command line parameters, too. This is 
    a design choice to accommodate multiple uses in a single plugin and
    a possible future combined use case.

    Importantly, this app does *not* actually talk to a PACS directly;
    instead it interacts with an intermediary service, typically 'pfdcm'.
    This intermediary service actually connects to a PACS and performs
    retrieves. This app can poll the service for status of a retrieve.

    Thus, it is important to understand that this app does not need 
    specific details on the PACS IP, port, AETITLE, etc. All of this
    information is managed by 'pfdcm'. This does mean of course, that
    'pfdcm' needs to be intantiated correctly. Please see the 'pfdcm'
    github wiki for specific instructions. 

    Note though that it is possible to pass to this app a 'pfdcm' 
    compliant message string using the [--msg <jsonMsgString>]. This
    <jsonMsgString> can be used to set 'pfdcm' internal lookup and 
    add new PACS entries. This <jsonMsgString> can also be used to 
    perform a retrieve.

    However, most often, the simplest mechanism of retrieve will be through
    the --priorHitsTable and --indexList command line flags that rely
    on the output of a previously run 'pacsretrieve.py' plugin.

    The <input> positional argument is MANDATORY and defines
    the output directory (or relative dir when called through the
    CHRIS API) of a previously run 'pacsretrieve.py' plugin that contains
    a priorHitsTable. 

    The <outputdir> positional argument is MANDATORY and defines
    the output directory (or relative dir when called through the
    CHRIS API) for the resultant DICOM files.
    
"""
str_results = """

    RESULTS

    Results from a retrieve operation are DICOM files in the <outputdir>.

    Results from a query operation are (in <outputdir>/query:
        o summary file of the hits, using <keyList>, <summaryFile>
        o JSON formatted results from 'pfdcm', <resultFile>
        o hit file containing number of hits, <numberOfHitsFile>


"""
str_args = """

    ARGS

    --pfdcm <PACserviceIP:port> 

        The IP and port specifier of the 'pfdcm' service. 

    --msg <jsonMsgString>    

        A 'pfdcm' conforming message string. If sent to this app,
        the message string is passed through unaltered to 'pfdcm'.
        This allows for setting up internals of 'pfdcm' and/or
        doing queries and interactions directly. 

        USE WITH CARE.

    --PACSservice <PACSservice> 

        The "name" of the PACS to retrieve within 'pfdcm'. This is 
        used to look up the PACS IP, port, AETitle, etc.

    --action retrieve|query

        The actual action to perform. Default is 'retrieve'.

    QUERY ARGS:

    --patientID <patientID>] 

        The <patientID> string to query.

    --PACSservice <PACSservice>] 

        The "name" of the PACS to query within 'pfdcm'. This is 
        used to look up the PACS IP, port, AETitle, etc.

    --summaryKeys <keylist>]
    
        A comma separated list of 'keys' to include in the 
        summary report. Typically:

        PatientID,PatientAge,StudyDescription,StudyInstanceUID,SeriesDescription,SeriesInstanceUID,NumberOfSeriesRelatedInstances

    --summaryFile <summaryFile>] 

        The name of the file in the <outputdir> to contain the summary report.

    --resultFile <resultFile>]

        The name of the file in the <outputdir> to contain the results.
    
    --numberOfHitsFile <numberOfHitsFile>]

        The name of the file in the <outputdir> to contain the number of hits.


    RETRIEVE ARGS:

    --priorHitsTable <hitsTable>    

        The JSON table of hits from a prior call to pacsretrieve.

    --indexList <commaseparatedlist>      

        A comma separated list of series in the <hitsTable> to actually
        retrieve.

    <inputdir>

        The input directory of a previous 'pacsretrieve.py' run.

    <outputdir>

        The output directory.

"""

import os
import sys
import json
import pprint
import pypx
import pfurl
import pfmisc
import pudb
import shutil
import time

# import the Chris app superclass
from chrisapp.base import ChrisApp

class PacsRetrieveApp(ChrisApp):
    AUTHORS = 'FNNDSC (dev@babyMRI.org)'
    SELFPATH = os.path.dirname(__file__)
    SELFEXEC = os.path.basename(__file__)
    EXECSHELL = 'python3'
    TITLE = 'PACS Retrieve'
    CATEGORY = ''
    TYPE = 'ds'
    DESCRIPTION = 'An app to initiate a retrieve on series of interest'
    DOCUMENTATION = 'http://wiki'
    LICENSE = 'Opensource (MIT)'
    VERSION = '1.0.0'

    # Fill out this with key-value output descriptive info (such as an output file path
    # relative to the output dir) that you want to save to the output meta file when
    # called with the --saveoutputmeta flag
    OUTPUT_META_DICT = {}
    
    def __init__(self, *args, **kwargs):
        ChrisApp.__init__(self, *args, **kwargs)

        self.__name__           = 'PACSRetrieveApp'

        # Debugging control
        self.b_useDebug         = False
        self.str_debugFile      = '/tmp/pacsretrieve.txt'
        self.b_quiet            = True
        self.dp                 = pfmisc.debug(    
                                            verbosity   = 0,
                                            level       = -1,
                                            within      = self.__name__
                                            )
        self.pp                 = pprint.PrettyPrinter(indent=4)

        # Input/Output dirs
        self.str_inputDir       = ''
        self.str_outputDir      = ''

        # Service and payload vars
        self.str_pfdcm          = ''
        self.str_msg            = ''
        # list holder for commands
        self.l_dmsg             = []
        # a single retrieve command
        self.d_msg              = {}
        # list holder for successful retrieves
        self.l_retrieveOK       = []

        # Alternate, simplified CLI flags
        self.str_patientID      = ''
        self.str_PACSservice    = ''
        # Retrieve
        self.str_priorHitsTable = ''
        self.l_indexList        = []
        # Query
        self.str_patientID      = ''
        self.str_PACSservice    = ''

        # Control
        self.b_canRun           = False

        # Prior hits JSON dictionary
        self.d_query            = {}

        # Summary report
        self.b_summaryReport    = False
        self.str_summaryKeys    = ''
        self.l_summaryKeys      = []
        self.str_summaryFile    = ''

        # Result report
        self.str_resultFile     = ''
       
    def define_parameters(self):
        """
        Define the CLI arguments accepted by this plugin app.
        """

        # The space of input parameters is very straightforward
        #   1. The IP:port of the pfdcm service
        #   2. A 'msg' type string / dictionary to send to the service.

        # PACS settings
        self.add_argument(
            '--pfdcm',
            dest        = 'str_pfdcm',
            type        = str,
            default     = '',
            optional    = True,
            help        = 'The PACS Q/R intermediary service IP:port.')
        self.add_argument(
            '--msg',
            dest        = 'str_msg',
            type        = str,
            default     = '',
            optional    = True,
            help        = 'The actual complete JSON message to send to the Q/R intermediary service.')
        self.add_argument(
            '--indexList',
            dest        = 'str_indexList',
            type        = str,
            default     = '',
            optional    = True,
            help        = 'A comma separated list of indices into the priorHitsTable.')
        self.add_argument(
            '--priorHitsTable',
            dest        = 'str_priorHitsTable',
            type        = str,
            default     = '',
            optional    = True,
            help        = 'A JSON formatted file returned by a prior call to pacsquery.')
        self.add_argument(
            '--PatientID',
            dest        = 'str_patientID',
            type        = str,
            default     = '',
            optional    = True,
            help        = 'The PatientID to query.')
        self.add_argument(
            '--PACSservice',
            dest        = 'str_PACSservice',
            type        = str,
            default     = 'orthanc',
            optional    = True,
            help        = 'The PACS service to use. Note this a key to a lookup in "pfdcm".')
        self.add_argument(
            '--summaryKeys',
            dest        = 'str_summaryKeys',
            type        = str,
            default     = '',
            optional    = True,
            help        = 'If specified, generate a summary report based on a comma separated key list.')
        self.add_argument(
            '--summaryFile',
            dest        = 'str_summaryFile',
            type        = str,
            default     = '',
            optional    = True,
            help        = 'If specified, save (overwrite) a summary report to passed file (in outputdir).')
        self.add_argument(
            '--numberOfHitsFile',
            dest        = 'str_numberOfHitsFile',
            type        = str,
            default     = '',
            optional    = True,
            help        = 'If specified, save (overwrite) the number of hits (in outputdir).')
        self.add_argument(
            '--resultFile',
            dest        = 'str_resultFile',
            type        = str,
            default     = '',
            optional    = True,
            help        = 'If specified, save (overwrite) all the hits to the passed file (in outputdir).')
        self.add_argument(
            '--man',
            dest        = 'str_man',
            type        = str,
            default     = '',
            optional    = True,
            help        = 'If specified, print help on the passed key entry. Use "entries" for all key list')
        self.add_argument(
            '--action',
            dest        = 'str_action',
            type        = str,
            default     = 'retrieve',
            optional    = True,
            help        = 'The action to perform. Default is "retrieve".')
        self.add_argument(
            '--pfurlQuiet',
            dest        = 'b_pfurlQuiet',
            type        = bool,
            default     = False,
            action      = 'store_true',
            optional    = True,
            help        = 'Silence pfurl noise.'),
        self.add_argument(
            '--version',
            dest        = 'b_version',
            type        = bool,
            default     = False,
            action      = 'store_true',
            optional    = True,
            help        = 'Show .')

    def df_print(self, adict):
        """
        Return a nicely formatted string representation of a dictionary
        """
        return self.pp.pformat(adict).strip()

    def service_call(self, *args, **kwargs):

        d_msg   = {}
        for k, v in kwargs.items():
            if k == 'msg':  d_msg   = v

        serviceCall = pfurl.Pfurl(
            msg                     = json.dumps(d_msg),
            http                    = self.str_pfdcm,
            verb                    = 'POST',
            b_raw                   = True,
            b_quiet                 = self.b_pfurlQuiet,
            b_httpResponseBodyParse = True,
            jsonwrapper             = 'payload',
            debugFile               = self.str_debugFile,
            useDebug                = self.b_useDebug
        )
        
        self.dp.qprint('Sending d_msg ==>\n %s' % self.df_print(d_msg), comms='tx')
        d_response      = json.loads(serviceCall())
        self.dp.qprint('Received d_response <==\n %s' % self.df_print(d_response), comms='rx')
        return d_response

    def man_get(self):
        """
        return a simple man/usage paragraph.
        """

        d_ret = {
            "man":  str_name + str_synposis + str_description + str_results + str_args,
            "synopsis":     str_synposis,
            "description":  str_description,
            "results":      str_results,
            "args":         str_args,
            "overview": """
            """,
            "callingSyntax1": """
                python3 pacsretrieve.py --pfdcm ${HOST_IP}:5015 --msg \
                '{  
                    "action": "PACSinteract",
                    "meta": 
                        {
                            "do":  "retrieve",
                            "on" : 
                            {
                                "series_uid": "<someSeriesUID>"
                            },
                            "PACS" : "orthanc"
                        }
                }' /tmp
            """,
            "callingSyntax2": """
                python3 pacsretrieve.py --pfdcm ${HOST_IP}:5015         \\
                                        --PatientID LILLA-9731          \\
                                        --PACSservice orthanc
            """,
            "callingSyntax3": """
                python3 pacsretrieve.py --pfdcm ${HOST_IP}:5015         \\
                                        --PACSservice orthanc           \\
                                        --pfurlQuiet                    \\
                                        --priorHitsTable results.json   \\
                                        --indexList 1,2,3               \\
                                        /tmp/query                      \\
                                        /tmp/data
            """
        }

        return d_ret

    def manPage_checkAndShow(self, options):
        """
        Check if the user wants inline help. If so, present requested help

        Return a bool based on check.
        """

        ret = False
        if len(options.str_man):
            ret = True
            d_man = self.man_get()
            if options.str_man in d_man:
                str_help    = d_man[options.str_man]
                print(str_help)
            if options.str_man == 'entries':
                print(d_man.keys())

        return ret

    def numberOfHitsReport_process(self, *args, **kwargs):
        """
        Save number of hits
        """
        str_hitsFile    = ''
        hits            = 0
        for k,v in kwargs.items():
            if k == 'hitsFile':     str_hitsFile    = v
            if k == 'hits':         hits            = v

        if len(str_hitsFile):
            str_FQhitsFile    = os.path.join(self.str_outputDir, str_hitsFile)
            self.dp.qprint('Saving number of hits to %s' % str_FQhitsFile )
            f = open(str_FQhitsFile, 'w')
            f.write('%d' % hits)
            f.close()

    def queryTable_read(self, *args, **kwargs):
        """
        Read a JSON formatted query table generated by 'pacsquery'.
        """

        d_results       = {}
        options         = None
        for k,v in kwargs.items():
            if k == 'priorHitsTable':   self.str_priorHitsTable = v

        if len(self.str_priorHitsTable):
            str_FQresultFile    = os.path.join(self.str_inputDir, self.str_priorHitsTable)
            self.dp.qprint('Reading prior data results from %s' % str_FQresultFile )
            f = open(str_FQresultFile, 'r')
            self.d_query = json.load(f)
            f.close()

    def dataReport_process(self, *args, **kwargs):
        """
        Process data report based on the return from the query.
        """

        d_results       = {}
        for k,v in kwargs.items():
            if k == 'resultFile':   self.str_resultFile     = v
            if k == 'results':      d_results               = v

        if len(self.str_resultFile):
            str_FQresultFile    = os.path.join(self.str_outputDir, self.str_resultFile)
            self.dp.qprint('Saving data results to %s' % str_FQresultFile )
            f = open(str_FQresultFile, 'w')
            js_results  = json.dumps(d_results, sort_keys = True, indent = 4)
            f.write('%s' % js_results)
            f.close()

    def summaryReport_process(self, *args, **kwargs):
        """
        Generate a summary report based on CLI specs
        """

        l_data                  = []
        self.str_summaryKeys    = ''
        for k,v in kwargs.items():
            if k == 'summaryKeys':  self.str_summaryKeys    = v
            if k == 'summaryFile':  self.str_summaryFile    = v
            if k == 'data':         l_data                  = v
        
        str_report      = ''
        l_summaryKeys   = self.str_summaryKeys.split(',')

        if len(l_data):
            # Header
            for key in l_summaryKeys:
                str_report  = str_report + "%-60s\t" % key

            # Body
            for entry in l_data:
                str_report  = str_report + "\n"
                for key in l_summaryKeys:
                    str_report  = str_report + "%-60s\t" % (entry[key]['value'])

        if len(self.str_summaryFile):
            str_FQsummaryFile   = os.path.join(self.str_outputDir, self.str_summaryFile) 
            self.dp.qprint('Saving summary to %s' % str_FQsummaryFile )
            f = open(str_FQsummaryFile, 'w')
            f.write(str_report)
            f.close()

    def directMessage_checkAndConstruct(self, options):
        """
        Checks if user specified a direct message to the 'pfdcm' service, 
        and if so, construct the message.

        Return True/False accordingly
        """

        ret = False
        if len(options.str_msg):
            ret = True
            self.str_msg        = options.str_msg
            try:
                self.d_msg      = json.loads(self.str_msg)
                self.l_dmsg.append(self.d_msg)
                self.b_canRun   = True
            except:
                self.b_canRun   = False
        return ret

    def queryMessage_checkAndConstruct(self, options):
        """
        Checks if user specified a query from a pattern of command line flags,
        and if so, construct the message.

        Return True/False accordingly
        """

        if len(options.str_patientID) and len(options.str_PACSservice):
            self.str_patientID      = options.str_patientID
            self.str_PACSservice    = options.str_PACSservice
            self.d_msg  = {
                'action':   'PACSinteract',
                'meta': {
                    'do':   'query',
                    'on': {
                        'PatientID': self.str_patientID
                    },
                    "PACS": self.str_PACSservice
                }
            }
            self.b_canRun   = True

    def retrieveMessage_checkAndConstruct(self, options):
        """
        Checks if user specified a retrieve from a pattern of command line flags,
        and if so, construct the message.

        Return True/False accordingly
        """

        if len(options.str_priorHitsTable) and len(options.str_indexList):
            self.l_indexList = options.str_indexList.split(',')
            self.str_PACSservice    = options.str_PACSservice
            for series in self.l_indexList:
                str_seriesUID       = self.d_query['query']['data'][int(series)]['SeriesInstanceUID']['value']
                self.l_dmsg.append({
                    'action':   'PACSinteract',
                    'meta': {
                        'do':   'retrieve',
                        'on': {
                            'series_uid': str_seriesUID
                        },
                        "PACS": self.str_PACSservice
                    }
                })
            self.b_canRun   = True
            return self.b_canRun

    def retrieveMessageStatus_checkAndConstruct(self):
        """
        Construct a status check on a retrieve event. Essentially, this replaces the
        'retrieve' string with a 'retrieveStatus' in the already existing message
        payload. 

        PRECONDITIONS
        * A populated self.l_dmsg list of dictionaries -- typically created by a 
          prior call to self.retrieveMessage_checkAndConstruct()

        POSTCONDITIONS
        * Return True/False accordingly
        """

        for d in self.l_dmsg:
            d['meta']['do'] = 'retrieveStatus'
        return self.b_canRun

    def retrieveMessageCopy_checkAndConstruct(self):
        """
        Construct a message that will ask the pfdcm to copy a dirtree
        from one location to another in its filesystem space.

        PRECONDITIONS
        * Successful retrieve call.

        POSTCONDITIONS
        * Return True/False accordingly
        """
    
        self.b_canRun   = False
        self.l_dmsg     = []
        for d_copy in self.l_retrieveOK:
            str_seriesUID       = d_copy['retrieveStatus']['seriesUID']
            self.l_dmsg.append({
                'action':   'pullPath',
                'meta': {
                    'on': {
                        'series_uid': str_seriesUID
                    },
                    'to': {
                        'path':         os.path.join(self.str_outputDir, str_seriesUID),
                        "createDir":    True
                    }                }
            })
        self.b_canRun   = True
        return self.b_canRun

    def outputFiles_generate(self, options, hits, d_ret, l_data):
        """
        Check and generate output files.
        """
        if len(options.str_numberOfHitsFile):
            self.numberOfHitsReport_process(
                                        hits        = hits,
                                        hitsFile    = options.str_numberOfHitsFile
                                        )

        if len(options.str_resultFile):
            self.dataReport_process     (    
                                        results     = d_ret,
                                        resultFile  = options.str_resultFile
                                        )

        if len(options.str_summaryKeys):
            self.summaryReport_process  ( 
                                        data        = l_data,
                                        summaryKeys = options.str_summaryKeys,
                                        summaryFile = options.str_summaryFile
                                        )
       
    def query_run(self, options):
        """
        Run a query
        """
        d_ret       = {} 
        self.queryMessage_checkAndConstruct(options)

        if self.b_canRun:
            d_ret   = self.service_call(msg = self.d_msg)
            l_data  = d_ret['query']['data']
            hits    = len(l_data) 
            self.dp.qprint('Query returned %d study hits' % hits)
            self.outputFiles_generate(options, hits, d_ret, l_data)

        return d_ret

    def retrieveStatus_callCheck(self, al_call):
        """
        Cycle once through the scheduled retrieves and 
        build a list of return status.

        """
        l_ret           = []

        if self.b_canRun:
            for self.d_msg in al_call:
                self.dp.qprint('Asking the dcm service for updates on reception of PACS data...')
                l_ret.append(self.service_call(msg = self.d_msg))
        return l_ret
        
    def retrieveStatus_filterPending(self, al_checkCall, al_checkResult):
        """
        Builds a list of status checks that have pending results
        """
        l_pendingCall       = []
        l_pendingResult     = []
        l_doneResult        = []
        b_pending           = False

        # pudb.set_trace()
        for d_call, d_result in zip(al_checkCall, al_checkResult):
            if not d_result['status']:
                l_pendingResult.append(d_result)
                l_pendingCall.append(d_call)
                b_pending    = True 
            else:
                l_doneResult.append(d_result)
        self.dp.qprint('pendingCalls = %d' % len(l_pendingCall))
        self.dp.qprint('doneResults  = %d' % len(l_doneResult))
        self.dp.qprint('b_pending    = %d' % b_pending)
        return {
            'status':               b_pending,
            'pendingResults':       l_pendingResult,
            'doneResults':          l_doneResult,
            'pendingCalls':         l_pendingCall
        }

    def retrieveStatus_callAndFilter(self, al_checkCall):
        """
        Perform a call to the remote service on retrieve status
        and filter the results into 'done' and 'pending'.
        """
        l_retrieveStatus        = []
        l_checkCall             = []
        d_ret                   = {}

        # First, check on the current status
        l_checkCall             = list(al_checkCall)
        l_retrieveStatus        = self.retrieveStatus_callCheck(l_checkCall)
        d_ret                   = self.retrieveStatus_filterPending(
                                                l_checkCall, 
                                                l_retrieveStatus)
        return d_ret

    def retrieveStatus_process(self, al_checkCall):
        """
        Process the retrieve status by waiting until 
        all asynchronous retrieves have completed.
        """
        
        b_jobsPending           = True
        b_breakCondition        = False
        sleepInterval           = 5
        l_retrieveStatus        = []
        l_checkCall             = []

        # pudb.set_trace()

        d_ret                   = self.retrieveStatus_callAndFilter(al_checkCall)
        b_jobsPending           = d_ret['status']
        for done in d_ret['doneResults']: self.l_retrieveOK.append(done)
        self.dp.qprint('Done list len = %d' % len(self.l_retrieveOK))

        while b_jobsPending and not b_breakCondition:
            self.dp.qprint('Pending retrieve jobs detected. Sleeping for %d seconds...' % sleepInterval)
            time.sleep(sleepInterval)

            self.dp.qprint('Reprocessing retrieve status for pending jobs...')
            d_ret               = self.retrieveStatus_callAndFilter(d_ret['pendingCalls'])
            b_jobsPending       = d_ret['status']

            # Update a master list of done results...
            for done in d_ret['doneResults']: self.l_retrieveOK.append(done)
            self.dp.qprint('Done list len = %d' % len(self.l_retrieveOK))

    def retrieve_initiate(self, options):
        """
        Initiate the actual retrieve calls to the PACS of interest.
        """
        l_ret = []

        if self.b_canRun:
            for self.d_msg in self.l_dmsg:
                self.dp.qprint('Messaging the dcm service to ask the PACS service to push data to us...')
                l_ret.append(self.service_call(msg = self.d_msg))
        return l_ret

    def retrieve_resultsCopy(self, ald_msg):
        """
        Call the pfdcm service to copy outputs from its internal unpack location
        to the output dir of this script.

        PRECONDITIONS
        * The filesystem of this script and that of pfdcm are logically the same.
        """
        l_ret = []

        if self.b_canRun:
            for self.d_msg in ald_msg:
                self.dp.qprint('Messaging the dcm service copy received DICOM data...')
                l_ret.append(self.service_call(msg = self.d_msg))
        return l_ret

    def retrieve_run(self, options):
        """
        Run a retrieve
        """
        # pudb.set_trace()

        self.queryTable_read(priorHitsTable = options.str_priorHitsTable)
        self.retrieveMessage_checkAndConstruct(options)

        # Start the retrieves...
        l_init  = self.retrieve_initiate(options)

        # Check/block on the status...
        self.retrieveMessageStatus_checkAndConstruct()
        l_check = self.retrieveStatus_process(self.l_dmsg)

        # Copy the results to the output dir
        # pudb.set_trace()
        self.retrieveMessageCopy_checkAndConstruct()
        l_copy  = self.retrieve_resultsCopy(self.l_dmsg)

    def run(self, options):
        """
        Define the code to be run by this plugin app.
        """

        d_ret                   = {
            'status': False
        }
        self.b_pfurlQuiet       = options.b_pfurlQuiet
        self.str_outputDir      = options.outputdir
        self.str_inputDir       = options.inputdir

        if options.b_version:
            print(str_version)

        # pudb.set_trace()

        if not self.manPage_checkAndShow(options) and not options.b_version:
            if len(options.str_pfdcm):
                self.str_pfdcm      = options.str_pfdcm
                if not self.directMessage_checkAndConstruct(options):
                    if options.str_action == 'query':
                            d_ret = self.query_run(options)
                    if options.str_action == 'retrieve': 
                            d_ret = self.retrieve_run(options)
        return d_ret

class PacsRetrieveAppOld(ChrisApp):
    '''
    Create file out.txt witht the directory listing of the directory
    given by the --dir argument.
    '''
    AUTHORS = 'FNNDSC (dev@babyMRI.org)'
    SELFPATH = os.path.dirname(__file__)
    SELFEXEC = os.path.basename(__file__)
    EXECSHELL = 'python3'
    TITLE = 'Pacs Retrieve'
    CATEGORY = ''
    TYPE = 'ds'
    DESCRIPTION = 'An app to find data of interest on the PACS'
    DOCUMENTATION = 'http://wiki'
    LICENSE = 'Opensource (MIT)'
    VERSION = '0.1'

    # Fill out this with key-value output descriptive info (such as an output file path
    # relative to the output dir) that you want to save to the output meta file when
    # called with the --saveoutputmeta flag
    OUTPUT_META_DICT = {}

    def define_parameters(self):
        """
        Define the CLI arguments accepted by this plugin app.
        """
        # PACS settings
        self.add_argument(
            '--aet',
            dest='aet',
            type=str,
            default=DICOM['calling_aet'],
            optional=True,
            help='aet')

        self.add_argument(
            '--aec',
            dest='aec',
            type=str,
            default=DICOM['called_aet'],
            optional=True,
            help='aec')

        self.add_argument(
            '--aetListener',
            dest='aet_listener',
            type=str,
            default=DICOM['calling_aet'],
            optional=True,
            help='aet listener')

        self.add_argument(
            '--serverIP',
            dest='server_ip',
            type=str,
            default=DICOM['server_ip'],
            optional=True,
            help='PACS server IP')

        self.add_argument(
            '--serverPort',
            dest='server_port',
            type=str,
            default=DICOM['server_port'],
            optional=True,
            help='PACS server port')

        # Retrieve settings
        self.add_argument(
            '--dataLocation',
            dest='data_location',
            type=str,
            default=DICOM['dicom_data'],
            optional=True,
            help='Location where the DICOM Listener receives the data.')

        self.add_argument(
            '--seriesFile',
            dest='series_file',
            type=str,
            default='',
            optional=True,
            help='Location of the file containing the series description.')

        self.add_argument(
            '--seriesUIDS',
            dest='series_uids',
            type=str,
            default=',',
            optional=True,
            help='Series UIDs to be retrieved')

    def run(self, options):
        """
        Define the code to be run by this plugin app.
        """
        # options.inputdir

        # common options between all request types
        # aet
        # aec
        # aet_listener
        # ip
        # port
        pacs_settings = {
            'aet': options.aet,
            'aec': options.aec,
            'aet_listener': options.aet_listener,
            'server_ip': options.server_ip,
            'server_port': options.server_port
        }

        # echo the PACS to make sure we can access it
        pacs_settings['executable'] = '/usr/bin/echoscu'
        echo = pypx.echo(pacs_settings)
        if echo['status'] == 'error':
            with open(os.path.join(options.outputdir, echo['status'] + '.txt'), 'w') as outfile:
                json.dump(echo, outfile, indent=4, sort_keys=True, separators=(',', ':'))
            return

        # create dummy series file with all series
        series_file = os.path.join(options.inputdir, 'success.txt')
        if options.series_file != '':
            series_file = options.series_file

        # uids to be fetched from success.txt
        uids = options.series_uids.split(',')
        uids_set = set(uids)

        # parser series file
        data_file = open(series_file, 'r')
        data = json.load(data_file)
        data_file.close()
        filtered_uids = [
            series for series in data['data'] if str(series['uid']['value']) in uids_set]

        path_dict = []
        data_directory = options.data_location

        # create destination directories and move series
        pacs_settings['executable'] = '/usr/bin/movescu'

        for series in filtered_uids:
            patient_dir = pypx.utils.patientPath(
                '', series['PatientID']['value'],
                series['PatientName']['value'])
            study_dir = pypx.utils.studyPath(
                patient_dir, series['StudyDescription']['value'],
                series['StudyDate']['value'],
                series['StudyInstanceUID']['value'])
            series_dir = pypx.utils.seriesPath(
                study_dir, series['SeriesDescription']['value'],
                series['SeriesDate']['value'],
                series['SeriesInstanceUID']['value'])

            source = os.path.join(data_directory, series_dir)
            series_info = os.path.join(source, 'series.info')
            destination_study = os.path.join(options.outputdir, study_dir)
            destination_series = os.path.join(options.outputdir, series_dir)

            path_dict.append(
                {'source': source,
                 'destination_study': destination_study,
                 'destination_series': destination_series,
                 'info': series_info})

            # move series
            pacs_settings['series_uid'] = series['SeriesInstanceUID']['value']
            output = pypx.move(pacs_settings)


        print('Receiving data...')

        # wait for files to arrive!
        timer = 0

        while timer < 100: # 1h
            for path in path_dict[:]:

                # what if pulling an existing dataset
                # (.info file already there? need extra flag to force re=pull?)
                if os.path.isfile(path['info']):

                    if not os.path.exists(path['destination_study']):
                        os.makedirs(path['destination_study'])
                    else:
                        print(path['destination_study'] + ' already exists.')

                    # copy series to output
                    shutil.copytree(path['source'], path['destination_series'])

                    # create jpgs directory
                    destination_jpgs = os.path.join(path['destination_series'], 'jpgs')
                    if not os.path.exists(destination_jpgs):
                        os.makedirs(destination_jpgs)
                    else:
                        print(destination_jpgs + ' already exists.')

                    # generate jpgs for all dcm files
                    for filename in os.listdir(path['destination_series']):
                        name, extension = os.path.splitext(filename)
                        if extension == '.dcm':
                            basename = os.path.basename(filename)
                            source = os.path.join(path['destination_series'], basename)
                            output = os.path.join(destination_jpgs, basename)
                            exec_location = os.path.dirname(pacs_settings['executable'])
                            executable = os.path.join(exec_location, 'dcmj2pnm')
                            command = executable + ' +oj +Wh 15 +Fa ' + source + ' ' + output + '.jpg';
                            response = subprocess.run(
                                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

                    # resize all jpgs
                    executable = '/usr/bin/mogrify'
                    options = '-resize 96x96 -background none -gravity center -extent 96x96'
                    source = os.path.join(destination_jpgs, '*')
                    command = executable + ' ' + options + ' ' + source
                    response = subprocess.run(
                        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

                    # create preview
                    executable = '/usr/bin/convert'
                    options = '-append'
                    output = os.path.join(path['destination_series'], 'preview.jpg')
                    command = executable + ' ' + options + ' ' + source + ' ' + output
                    response = subprocess.run(
                        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

                    # remove from dictionnary
                    path_dict.remove(path)

            if len(path_dict) == 0:
                break

            time.sleep(1)
            timer += 1

        print('Done.')

# ENTRYPOINT
if __name__ == "__main__":
    app = PacsRetrieveApp()
    app.launch()
