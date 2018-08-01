#!/usr/bin/env python
 
'''Usage:   checkpoint_console


'''


from contextlib import ContextDecorator
from snap import common
import yaml
import docopt


class DataStore(object):
    def __init__(self, service_object_registry, **kwargs):
        self.service_object_registry = service_object_registry


    def write(self, recordset, **kwargs):
        '''write each record in <recordset> to the underlying storage medium.
        Implement in subclass.
        '''
        pass


class RecordBuffer(object):
    def __init__(self, datastore, **kwargs):        
        self.data = []
        self.checkpoint_mgr = None        
        self.datastore = datastore


    def writethrough(self, **kwargs):
        '''write the contents of the record buffer out to the underlying datastore.
        Implement in subclass.
        '''
        self.datastore.write(self.data, **kwargs)


    def register_checkpoint(self, checkpoint_instance):
        self.checkpoint_mgr = checkpoint_instance


    def flush(self, **kwargs):        
        self.writethrough(**kwargs)
        self.data = []


    def write(self, record, **kwargs):
        try:
            self.data.append(record) 
            if self.checkpoint_mgr:
                self.checkpoint_mgr.register_write()          
        except Exception as err: 
            raise err


class checkpoint(ContextDecorator):
    def __init__(self, record_buffer, **kwargs):
        checkpoint_interval = int(kwargs.get('interval') or 1)

        self.interval = checkpoint_interval
        self._outstanding_writes = 0
        self._total_writes = 0
        self.record_buffer = record_buffer
        self.record_buffer.register_checkpoint(self)


    @property
    def total_writes(self):
        return self._total_writes

    @property
    def writes_since_last_reset(self):
        return self._outstanding_writes


    def increment_write_count(self):
        self._outstanding_writes += 1
        self._total_writes += 1


    def reset(self):
        self.outstanding_writes = 0


    def register_write(self):
        self.increment_write_count()
        if self.writes_since_last_reset == self.interval:
            self.record_buffer.flush()
            self.reset()


    def __enter__(self):
        return self


    def __exit__(self, *exc):
        self.record_buffer.writethrough()
        return False


def load_datastore(self, name, transform_config, service_object_registry):
    ds_module_name = transform_config['globals']['datastore_module']

    if not transform_config['datastores'].get(name):
        raise DatastoreNotRegisteredUnderName(name)

    datastore_class_name = transform_config['datastores'][name]['class']
    klass = common.load_class(datasource_class_name, src_module_name)
    
    init_params = {}
    for param in transform_config['datastores'][name]['init_params']:
        init_params[param['name']] = param['value']
        
    return klass(service_object_registry, **init_params)


class TestStore(DataStore):
    def __init__(self, service_object_registry, **kwargs):
        DataStore.__init__(self, service_object_registry, **kwargs)
        self.num_writethrough_events = 0
        self.total_records_received = 0

    def write(self, records, **kwargs):
        self.num_writethrough_events += 1
        self.total_records_received += len(records)


class FileStore(DataStore):
    def __init__(self, service_object_registry, **kwargs):
        DataStore.__init__(self, service_object_registry, **kwargs)
        kwreader = common.KeywordArgReader('filename')
        kwreader.read(**kwargs)
        self.filename = kwreader.get_value('filename')        


    def write(self, records, **kwargs):        
        with open(self.filename, 'a') as f:
            for record in records:
                f.write(record)
                f.write('\n')            


def main(args):
    registry = common.ServiceObjectRegistry({})
    fs = FileStore(registry, filename='dexcrazy.txt')
    buffer = RecordBuffer(fs)

    with checkpoint(buffer, interval=4) as cpt:
        for i in range(9):
            buffer.write('hello world')
        
    print('checkpoint instance recorded %d calls to RecordStore.write()' % cpt.total_writes)


if __name__ == '__main__':
    args = docopt.docopt(__doc__)
    main(args)