"""
Module containing NFC bounding interval annotator, version 1.0.

An NFC bounding interval annotator sets values for the `Call Start Index`
and `Call End Index` annotations for a clip containing a nocturnal flight
call (NFC). If the annotations already exist their values are overwritten,
and if they do not already exist they are created. The clip is assumed to
contain an NFC.
"""


from collections import defaultdict
import logging

import resampy

from vesper.command.annotator import Annotator as AnnotatorBase
from vesper.django.app.models import AnnotationInfo
from vesper.mpg_ranch.nfc_bounding_interval_annotator_1_0.inferrer \
    import Inferrer
from vesper.singletons import clip_manager
import vesper.django.app.model_utils as model_utils
import vesper.mpg_ranch.nfc_bounding_interval_annotator_1_0.dataset_utils \
    as dataset_utils
import vesper.util.open_mp_utils as open_mp_utils


_CLASSIFICATION_ANNOTATION_NAME = 'Classification'
_START_INDEX_ANNOTATION_NAME = 'Call Start Index'
_END_INDEX_ANNOTATION_NAME = 'Call End Index'

_MODEL_NAMES = {
    'Tseep':
        ('Tseep_Start_2020-07-08_19.11.45', 'Tseep_End_2020-07-08_19.37.02'),
}


class Annotator(AnnotatorBase):
    
    
    extension_name = 'MPG Ranch NFC Bounding Interval Annotator 1.0'

    
    def __init__(self, *args, **kwargs):
        
        super().__init__(*args, **kwargs)
        
        open_mp_utils.work_around_multiple_copies_issue()
        
        # Suppress TensorFlow INFO and DEBUG log messages.
        logging.getLogger('tensorflow').setLevel(logging.WARN)
        
        self._clip_manager = clip_manager.instance

        self._inferrers = dict(
            (t, _create_inferrer(t))
            for t in ('Tseep',))
               
        self._annotation_infos = _get_annotation_infos()
        
 
    def annotate_clips(self, clips):
        
        clip_lists = self._get_call_clip_lists(clips)
        
        annotated_clip_count = 0
        
        for clip_type, clips in clip_lists.items():
            
            inferrer = self._inferrers.get(clip_type)
            
            if inferrer is not None:
                # have inferrer for this clip type
                
                inference_sample_rate = inferrer.sample_rate
                
                clips, waveform_dataset = \
                    self._get_clip_waveforms(clips, inference_sample_rate)
                
                bounds = inferrer.get_call_bounds(waveform_dataset)
                
                for clip, (start_index, end_index) in zip(clips, bounds):
                    
                    self._annotate_clip(
                        clip, _START_INDEX_ANNOTATION_NAME, start_index,
                        inference_sample_rate)
                    
                    self._annotate_clip(
                        clip, _END_INDEX_ANNOTATION_NAME, end_index,
                        inference_sample_rate)
                    
                annotated_clip_count += len(clips)
                
        return annotated_clip_count
        
        
    def _get_call_clip_lists(self, clips):
        
        """Gets a mapping from clip types to lists of call clips."""
        
        
        # Get mapping from clip types to call clip lists.
        clip_lists = defaultdict(list)
        for clip in clips:
            if _is_call_clip(clip):
                clip_type = model_utils.get_clip_type(clip)
                clip_lists[clip_type].append(clip)
        
        return clip_lists
    
    
    def _get_clip_waveforms(self, clips, inference_sample_rate):
        
        result_clips = []
        waveforms = []

        for clip in clips:
            
            try:
                waveform = self._get_clip_samples(clip, inference_sample_rate)
                
            except Exception as e:
                
                logging.warning(
                    f'Could not annotate clip "{clip}", since its samples '
                    f'could not be obtained. Error message was: {str(e)}')
                
            else:
                # got clip samples
                
                result_clips.append(clip)
                waveforms.append(waveform)
                
        waveforms = \
            dataset_utils.create_waveform_dataset_from_tensors(waveforms)
                        
        return result_clips, waveforms
                
        
    def _get_clip_samples(self, clip, inference_sample_rate):
         
        # Get clip samples.
        samples = self._clip_manager.get_samples(clip)
            
        if clip.sample_rate != inference_sample_rate:
            # need to resample
            
            samples = resampy.resample(
                samples, clip.sample_rate, inference_sample_rate)
             
        return samples


    def _annotate_clip(
            self, clip, annotation_name, index, inference_sample_rate):
        
        # If needed, modify index to account for difference between
        # clip and inference sample rates.
        if clip.sample_rate != inference_sample_rate:
            factor = clip.sample_rate / inference_sample_rate
            index = int(round(index * factor))
            
        # Make index a recording index rather than a clip index.
        index += clip.start_index
            
        annotation_info = self._annotation_infos[annotation_name]
        annotation_value = str(index)
        
        model_utils.annotate_clip(
            clip, annotation_info, annotation_value,
            creating_user=self._creating_user,
            creating_job=self._creating_job,
            creating_processor=self._creating_processor)
        
        
def _create_inferrer(clip_type):
    model_names = _MODEL_NAMES[clip_type]
    return Inferrer(*model_names)


def _get_annotation_infos():
    return dict(
        (name, _get_annotation_info(name))
        for name in (_START_INDEX_ANNOTATION_NAME, _END_INDEX_ANNOTATION_NAME))


def _get_annotation_info(name):
    try:
        return AnnotationInfo.objects.get(name=name)
    except AnnotationInfo.DoesNotExist:
        raise ValueError(f'Unrecognized annotation "{name}".')


def _is_call_clip(clip):
    annotations = model_utils.get_clip_annotations(clip)
    classification = annotations.get(_CLASSIFICATION_ANNOTATION_NAME)
    return classification is not None and classification.startswith('Call')


def _convert_clip_index_to_recording_index(
        clip, clip_index, sample_rate):
    
    if sample_rate != clip.sample_rate:
        clip_index = int(round(clip_index * clip.sample_rate / sample_rate))
        
    return clip.start_index + clip_index
