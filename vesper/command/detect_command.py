"""Module containing class `DetectCommand`."""


import itertools

from vesper.command.command import Command, CommandExecutionError
from vesper.django.app.models import Processor, Recording, Station
import vesper.command.command_utils as command_utils


class DetectCommand(Command):
    
    
    extension_name = 'detect'
    
    
    def __init__(self, args):
        super().__init__(args)
        get = command_utils.get_required_arg
        self._detector_names = get('detectors', args)
        self._station_names = get('stations', args)
        self._start_date = get('start_date', args)
        self._end_date = get('end_date', args)
        
        
    def execute(self, context):
        
        self._logger = context.job.logger
        
        detectors = self._get_detectors()
        
        recordings = self._get_recordings()
            
        for recording in recordings:
            self._logger.info(
                'running detectors on recording {}...'.format(str(recording)))
            self._run_detectors(detectors, recording)
            
        return True
    
    
    def _get_detectors(self):
        
        try:
            return [self._get_detector(name) for name in self._detector_names]
        
        except Exception as e:
            self._logger.error((
                'Collection of detectors to run on recordings on failed with '
                    'an exception.\n'
                'The exception message was:\n'
                '    {}\n'
                'The archive was not modified.\n'
                'See below for exception traceback.').format(str(e)))
            raise
            
            
    def _get_detector(self, name):
        try:
            return Processor.objects.get(name=name)
        except Processor.DoesNotExist:
            raise CommandExecutionError(
                'Unrecognized detector "{}".'.format(name))
            
            
    def _get_recordings(self):
        
        try:
            return itertools.chain.from_iterable(
                self._get_station_recordings(
                    name, self._start_date, self._end_date)
                for name in self._station_names)
            
        except Exception as e:
            self._logger.error((
                'Collection of recordings to run detectors on failed with '
                    'an exception.\n'
                'The exception message was:\n'
                '    {}\n'
                'The archive was not modified.\n'
                'See below for exception traceback.').format(str(e)))
            raise

            
    def _get_station_recordings(self, station_name, start_date, end_date):

        # TODO: Test behavior for an unrecognized station name.
        # I tried this on 2016-08-23 and got results that did not
        # make sense to me. An exception was raised, but it appeared
        # to be  raised from within code that followed the except clause
        # in the `execute` method above (the code logged the sequence of
        # recordings returned by the `_get_recordings` method) rather
        # than from within that clause, and the error message that I
        # expected to be logged by that clause did not appear in the log.
        
        try:
            station = Station.objects.get(name=station_name)
        except Station.DoesNotExist:
            raise CommandExecutionError(
                'Unrecognized station "{}".'.format(station_name))
        
        time_interval = station.get_night_interval_utc(start_date, end_date)
        
        return Recording.objects.filter(
            station_recorder__station=station,
            start_time__range=time_interval)


    def _run_detectors(self, detectors, recording):
        pass
        