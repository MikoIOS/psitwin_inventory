"""Persistent CPU worker. Stdout is reserved for the private JSON protocol.

No audio/text is uploaded. Model files are downloaded by the official libraries
on first use; prewarm them before switching to an offline deployment.
"""
import base64
import contextlib
import io
import json
import os
import sys
import wave

# Optional isolated package directory for portable Windows Python installations.
if os.environ.get('SAIKI_VOICE_SITE_PACKAGES'):
    sys.path.insert(0, os.environ['SAIKI_VOICE_SITE_PACKAGES'])

pipeline = None
whisper = None
piper = None


def run(data):
    global pipeline, whisper, piper
    if data['operation'] == 'transcribe':
        import av
        import numpy as np
        samples, count = [], 0
        with av.open(io.BytesIO(base64.b64decode(data['audio']))) as container:
            resampler = av.AudioResampler(format='s16', layout='mono', rate=16000)
            for frame in container.decode(audio=0):
                for converted in resampler.resample(frame):
                    array = converted.to_ndarray().flatten()
                    count += len(array)
                    if count > 35 * 16000:
                        raise ValueError('audio too long')
                    samples.append(array)
            for converted in resampler.resample(None):
                samples.append(converted.to_ndarray().flatten())
        if not samples:
            return {'text': ''}
        audio = np.concatenate(samples).astype(np.float32) / 32768
        from faster_whisper import WhisperModel
        if whisper is None:
            whisper = WhisperModel(os.environ.get('SAIKI_STT_MODEL', 'base'), device='cpu', compute_type='int8', cpu_threads=4)
        segments, info = whisper.transcribe(audio, language='es',
            vad_filter=True, beam_size=1, condition_on_previous_text=False)
        text = ' '.join(s.text.strip() for s in segments if s.no_speech_prob < .6 and s.avg_logprob > -1).strip()
        if info.duration > 35:
            raise ValueError('audio too long')
        return {'text': text}
    provider = os.environ.get('SAIKI_TTS_PROVIDER', 'kokoro')
    buffer = io.BytesIO()
    if provider == 'piper':
        from piper import PiperVoice, SynthesisConfig
        if piper is None:
            piper = PiperVoice.load(os.environ['SAIKI_PIPER_MODEL'])
        with wave.open(buffer, 'wb') as output:
            piper.synthesize_wav(data['text'], output, syn_config=SynthesisConfig(length_scale=1 / data['speed']))
    else:
        import numpy as np
        import soundfile as sf
        from kokoro import KPipeline
        if pipeline is None:
            import torch
            torch.set_num_threads(4)
            pipeline = KPipeline(lang_code='e', repo_id=os.environ.get('SAIKI_TTS_MODEL', 'hexgrad/Kokoro-82M'), device='cpu')
        # load_voice verifies that the requested voice artifact really exists.
        pipeline.load_voice(data['voice'])
        if data['operation'] == 'probe':
            return {'voice': data['voice'], 'available': True}
        chunks = [audio.numpy() if hasattr(audio, 'numpy') else audio
                  for _, _, audio in pipeline(data['text'], voice=data['voice'], speed=data['speed'])]
        if not chunks:
            raise ValueError('empty synthesis')
        sf.write(buffer, np.concatenate(chunks), 24000, format='WAV', subtype='PCM_16')
    return {'audio': base64.b64encode(buffer.getvalue()).decode('ascii')}


if __name__ == '__main__':
    for line in sys.stdin:
        operation = 'unknown'
        try:
            with contextlib.redirect_stdout(sys.stderr):
                data = json.loads(line)
                operation = data.get('operation') if data.get('operation') in {'transcribe', 'synthesize', 'probe'} else 'unknown'
                result = run(data)
            print(json.dumps(result), flush=True)
        except Exception as exc:
            # Do not echo user text, audio or filesystem credentials.
            print(json.dumps({'error': type(exc).__name__, 'operation': operation,
                              'dependency': exc.name if isinstance(exc, ImportError) else None}), flush=True)
