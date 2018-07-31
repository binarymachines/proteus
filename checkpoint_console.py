#!/usr/bin/env python

from contextlib import ContextDecorator


class RecordStore(object):
    def __init__(self, service_object_registry, **kwargs):        
        self.record_buffer = []
        self.checkpoint_mgr = None


    def writethrough(self, record, **kwargs):
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
        print('### DOING THE THING...')
        return self

    def __exit__(self, *exc):
        self.record_store.writethrough()
        return False


class FileStore(RecordStore):
    def __init__(self, filename):
        RecordStore.__init__(self, None)
        self.filename = filename


    def writethrough(self, **kwargs):
        print('>>> Executing writethrough...')
        with open(self.filename, 'a') as f:
            for record in self.record_buffer:
                f.write(record)
                f.write('\n')
            self.record_buffer = []


def main():

    record_store_instance = FileStore('dexcrazy.txt')
    
    with checkpoint(record_store_instance, 4) as cp:
        print(cp)
        for i in range(8):
            record_store_instance.write('hello world')
        

    print(cp)
    print('buffer contents:')
    print('\n'.join([r for r in record_store_instance.record_buffer]))

    print('checkpoint instance records %d calls to RecordStore.write()' % cp.num_writes)


if __name__ == '__main__':
    main()