import datetime

from django.db import transaction
import pytz

from vesper.command.command import CommandSyntaxError
from vesper.django.app.models import (
    Algorithm, AlgorithmVersion, Device, DeviceConnection, DeviceInput,
    DeviceModel, DeviceModelInput, DeviceModelOutput, DeviceOutput, Processor,
    Station, StationDevice)
import vesper.command.command_utils as command_utils


# TODO: Recover more gracefully when data are missing, e.g. raise a
# `CommandSyntaxError` rather than a `KeyError`.


class ArchiveDataImporter:
    
    
    extension_name = 'Archive Data Importer'
    
    
    def __init__(self, args):
        self.archive_data = command_utils.get_required_arg('archive_data', args)
    
    
    def execute(self, context):
        
        self._logger = context.job.logger
        
        try:
            with transaction.atomic():
                self._add_stations()
                self._add_device_models()
                self._add_devices()
                self._add_station_devices()
                self._add_algorithms()
                self._add_algorithm_versions()
                self._add_processors()
                
        except Exception:
            self._logger.error(
                'Archive data import failed with an exception. Database '
                'has been restored to its state before the import. See '
                'below for exception traceback.')
            raise
        
        return True
            
            
    def _add_stations(self):
        
        stations_data = self.archive_data.get('stations')
        
        if stations_data is not None:
            
            for data in stations_data:
            
                name = data['name']
                
                self._logger.info('Adding station "{}"...'.format(name))
                
                station = Station(
                    name=name,
                    description=data.get('description', ''),
                    latitude=data['latitude'],
                    longitude=data['longitude'],
                    elevation=data['elevation'],
                    time_zone=data['time_zone'])
                
                station.save()


    def _add_device_models(self):
        
        device_models_data = self.archive_data.get('device_models')
        
        if device_models_data is not None:
            
            for data in device_models_data:
                model = self._add_device_model(data)
                self._add_ports(model, data, 'input', DeviceModelInput)
                self._add_ports(model, data, 'output', DeviceModelOutput)
            
            
    def _add_device_model(self, data):
        
        name = data['name']
        type_ = data['type']
        manufacturer = data['manufacturer']
        model = data['model']
        
        self._logger.info(
            'Adding device model "{}" "{} {} {}"...'.format(
                name, manufacturer, model, type_))
        
        model = DeviceModel(
            name=name,
            type=type_,
            manufacturer=manufacturer,
            model=model,
            description=data.get('description', '')
        )
        
        model.save()
        
        return model
            

    def _add_ports(self, model, data, port_type, port_class):
        
        port_data = self._get_port_data(data, port_type)
        
        for local_name, channel_num in port_data:
            
            self._logger.info(
                'Adding device model {} "{} {} {}"...'.format(
                    port_type, model.name, local_name, channel_num))
            
            port = port_class(
                model=model,
                local_name=local_name,
                channel_num=channel_num)
            
            port.save()


    def _get_port_data(self, data, port_type):

        names = data.get(port_type + 's')
        
        if names is None:
            
            key = 'num_{}s'.format(port_type)
            num_ports = data.get(key, 0)
            
            if num_ports == 0:
                names = []
                
            elif num_ports == 1:
                names = [port_type.capitalize()]
                
            else:
                names = ['{} {}'.format(port_type.capitalize(), i)
                        for i in range(num_ports)]
                
        return [(name, i) for i, name in enumerate(names)]
                
                
    def _add_devices(self):
        
        devices_data = self.archive_data.get('devices')
        
        if devices_data is not None:
            
            models = _create_objects_dict(DeviceModel)
        
            for data in devices_data:
                model = self._get_device_model(data, models)
                device = self._add_device(data, model)
                self._add_device_inputs(device)
                self._add_device_outputs(device)
            
            
    def _get_device_model(self, data, models):
    
        name = data['model']
        try:
            return models[name]
        except KeyError:
            raise CommandSyntaxError(
                'Unrecognized device model name "{}".'.format(name))


    def _add_device(self, data, model):
        
        name = data['name']
        serial_number = data['serial_number']
        
        self._logger.info(
            'Adding device "{}" "{} {}"...'.format(
                name, model.name, serial_number))
        
        device = Device(
            name=name,
            model=model,
            serial_number=serial_number,
            description=data.get('description', ''))
        
        device.save()
        
        return device


    def _add_device_inputs(self, device):
        
        for model_input in device.model.inputs.all():
            
            self._logger.info(
                'Adding device input "{} {}"...'.format(
                    device.name, model_input.local_name))
            
            input_ = DeviceInput(device=device, model_input=model_input)
            input_.save()
            
            
    def _add_device_outputs(self, device):
                
        for model_output in device.model.outputs.all():
            
            self._logger.info(
                'Adding device output "{} {}"...'.format(
                    device.name, model_output.local_name))
            
            output = DeviceOutput(device=device, model_output=model_output)
            output.save()


    def _add_station_devices(self):
        
        station_devices_data = self.archive_data.get('station_devices')
        
        if station_devices_data is not None:
            
            devices = _create_objects_dict(Device)
            inputs = _create_objects_dict(DeviceInput)
            outputs = _create_objects_dict(DeviceOutput)
        
            for data in station_devices_data:
                
                station = self._get_station(data)
                start_time = _get_utc_time(data['start_time'], station)
                end_time = _get_utc_time(data['end_time'], station)
                
                device_names = data['devices']
                for name in device_names:
                    device = self._get_device(name, devices)
                    self._add_station_device(
                        station, device, start_time, end_time)
                
                connections = data['connections']
                for connection in connections:
                    output = self._get_output(connection['output'], outputs)
                    input_ = self._get_input(connection['input'], inputs)
                    self._add_connection(output, input_, start_time, end_time)
                            
    
    def _get_station(self, data):
        name = data['station']
        try:
            return Station.objects.get(name=name)
        except Station.DoesNotExist:
            raise CommandSyntaxError('Unrecognized station "{}".'.format(name))
            

    def _get_device(self, name, devices):
        try:
            return devices[name]
        except KeyError:
            raise CommandSyntaxError('Unrecognized device "{}".'.format(name))
        

    def _add_station_device(self, station, device, start_time, end_time):
        
        self._logger.info(
            'Adding station device "{} at {} from {} to {}"...'.format(
                device.name, station.name, str(start_time), str(end_time)))
    
        station_device = StationDevice(
            station=station,
            device=device,
            start_time=start_time,
            end_time=end_time)
        
        station_device.save()
        

    def _get_output(self, name, outputs):
        try:
            return outputs[name]
        except KeyError:
            raise CommandSyntaxError(
                'Unrecognized device output "{}".'.format(name))


    def _get_input(self, name, inputs):
        try:
            return inputs[name]
        except KeyError:
            raise CommandSyntaxError(
                'Unrecognized device input "{}".'.format(name))


    def _add_connection(self, output, input_, start_time, end_time):
        
        self._logger.info((
            'Adding device connection "{} -> {} '
            'from {} to {}"...').format(
                output.name, input_.name, str(start_time), str(end_time)))
    
        connection = DeviceConnection(
            output=output,
            input=input_,
            start_time=start_time,
            end_time=end_time)
        
        connection.save()


    def _add_algorithms(self):
        
        algorithms_data = self.archive_data.get('algorithms')
        
        if algorithms_data is not None:
            
            for data in algorithms_data:
            
                name = data['name']

                self._logger.info('Adding algorithm "{}"...'.format(name))
                
                algorithm = Algorithm(
                    name=name,
                    type=data['type'],
                    description=data.get('description', ''))
                
                algorithm.save()


    def _add_algorithm_versions(self):
        
        versions_data = self.archive_data.get('algorithm_versions')
        
        if versions_data is not None:
            
            algorithms = _create_objects_dict(Algorithm)
            
            for data in versions_data:
            
                algorithm = algorithms[data['algorithm']]
                version = data['version']

                self._logger.info(
                    'Adding algorithm version "{} {}"...'.format(
                        algorithm.name, version))
                
                algorithm_version = AlgorithmVersion(
                    algorithm=algorithm,
                    version=version,
                    description=data.get('description', ''))
                
                algorithm_version.save()


    def _add_processors(self):
        
        processors_data = self.archive_data.get('processors')
        
        if processors_data is not None:
            
            algorithm_versions = _create_objects_dict(AlgorithmVersion)
            
            for data in processors_data:
            
                name = data['name']
                
                self._logger.info('Adding processor "{}"...'.format(name))
                
                processor = Processor(
                    name=name,
                    algorithm_version=\
                        algorithm_versions[data['algorithm_version']],
                    settings=data.get('settings', ''),
                    description=data.get('description', ''))
                
                processor.save()


def _create_objects_dict(cls):
    objects = {}
    for obj in cls.objects.all():
        objects[obj.name] = obj
        if hasattr(obj, 'long_name'):
            objects[obj.long_name] = obj
    return objects


# TODO: Move this to another module and make it public?
def _get_utc_time(dt, station):
    if isinstance(dt, datetime.date):
        dt = datetime.datetime(dt.year, dt.month, dt.day)
    if dt.tzinfo is None:
        time_zone = pytz.timezone(station.time_zone)
        dt = time_zone.localize(dt)
        dt = dt.astimezone(pytz.utc)
    return dt