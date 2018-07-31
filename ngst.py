#!/usr/bin/env python

'''Usage:
            ngst --config <configfile> --target <target_datastore> [--datafile <datafile>] [--limit=<max_records>]           
            ngst --config <configfile> --list-targets

   Options:            
            -i --interactive   Start up in interactive mode
'''

#
# ngst: command line utility for pushing extracted records into a Mercury data pipeline
#


import docopt
from docopt import docopt as docopt_func
from docopt import DocoptExit
import os, sys
from contextlib import ContextDecorator
import csv
import json
from snap import snap, common
import datamap as dmap
import yaml
import logging



class RecordStore(object):
    def __init__(self, service_object_registry, **kwargs):        
        self.record_buffer = []
        self.checkpoint_mgr = None


    def writethrough(self, **kwargs):
        '''implement in subclass'''
        pass


    def register_checkpoint(self, checkpoint_instance):
        self.checkpoint_mgr = checkpoint_instance


    def checkpoint(self, **kwargs):        
        for record in self.record_buffer:
            self.writethrough(record, **kwargs)
        self.record_buffer = []


    def write(self, record, **kwargs):
        try:
            self.record_buffer.append(record) 
            if self.checkpoint_mgr:
                self.checkpoint_mgr.register_write()          
        except Exception as err: 
            raise err


class checkpoint(ContextDecorator):
    def __init__(self, record_store, checkpoint_interval):
        print('creating an instance of checkpoint with interval of %d...' % checkpoint_interval)
        self.interval = checkpoint_interval
        self.num_writes = 0
        self.record_store = record_store
        self.record_store.register_checkpoint(self)


    def increment_write_count(self):
        self.num_writes += 1


    def reset(self):
        self.num_writes = 0


    def register_write(self):
        self.num_writes += 1
        if self.num_writes == self.interval:
            self.record_store.writethrough()
            self.reset()


    def __enter__(self):        
        return self


    def __exit__(self, *exc):
        self.record_store.writethrough()
        return False


class FileStore(RecordStore):
    def __init__(self, filename, service_object_registry):
        RecordStore.__init__(self, service_object_registry)
        self.filename = filename


    def writethrough(self, record, **kwargs):
        with open(self.filename, 'a') as f:
            f.write(record)
            f.write('\n')



def main(args):
    print(common.jsonpretty(args))

    default_record_store = FileStore('tarif_records.txt', common.ServiceObjectRegistry({}))

    limit = -1
    if args.get('--limit') is not None:
        limit = int(args['--limit'])
    list_mode = False
    stream_input_mode = False

    if args['--target'] == True and args['<datafile>'] is None:
        print('Streaming mode enabled.')
        record_count = 0
        while True:
            if record_count == limit:
                break
            raw_line = sys.stdin.readline()
            line = raw_line.lstrip().rstrip()
            if not len(line):
                break            
            record_count += 1
            print('read record #%s from standard input.' % record_count)

            default_record_store.write(line)
    elif args['<datafile>']:
        input_file = args['<datafile>']
        print('File input mode enabled. Reading from input file %s...' % input_file)
        record_count = 0
        with open(input_file) as f:
            for line in file:
                if record_count == limit:
                    break
                record_count += 1


if __name__ == '__main__':
    args = docopt.docopt(__doc__)
    main(args)



