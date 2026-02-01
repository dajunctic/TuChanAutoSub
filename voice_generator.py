import os
import asyncio
import edge_tts
from pydub import AudioSegment
import json

class VoiceOverGenerator:
    def __init__(self, method="edge-tts", voice="vi-VN-NamMinhNeural", pitch="+0Hz", rate="+0%", 
                 ref_audio=None, ref_text=None, temperature=0.7, top_k=50, max_speed_limit=0.25):
        self.method = method
        self.voice = voice
        self.pitch = pitch
        self.rate = rate
        self.ref_audio = ref_audio
        self.ref_text = ref_text
        self.temperature = temperature
        self.top_k = top_k
        self.max_speed_limit = max_speed_limit # e.g., 0.25 for +25%
        self.vieneu_model = None

    def _get_vieneu(self):
        if self.vieneu_model is None:
            from vieneu import Vieneu
            # Load the default model (0.3B) for speed or we could specify 0.5B
            self.vieneu_model = Vieneu()
        return self.vieneu_model

    async def _generate_single_audio(self, text, output_path, custom_rate=None):
        """Generates a single audio file based on chosen method."""
        if self.method == "vieneu":
            try:
                model = self._get_vieneu()
                audio_data = model.infer(
                    text, 
                    ref_audio=self.ref_audio, 
                    ref_text=self.ref_text,
                    temperature=self.temperature,
                    top_k=self.top_k
                )
                model.save(audio_data, output_path)
            except Exception as e:
                print(f"VieNeu Error: {e}")
                raise e
        elif self.method == "gtts":
            # gTTS method (Google Text-to-Speech)
            from gtts import gTTS
            tts = gTTS(text=text, lang='vi')
            tts.save(output_path)
        else:
            # edge-tts method
            import edge_tts
            final_rate = custom_rate if custom_rate else self.rate
            communicate = edge_tts.Communicate(text, self.voice, rate=final_rate, pitch=self.pitch)
            await communicate.save(output_path)

    def generate_voiceovers(self, subtitles, output_dir, video_duration_ms, progress_callback=None):
        """
        Generates audio files. 
        For edge-tts: uses native rate control.
        For vieneu: uses post-processing speedup if it overflows.
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        else:
            # Clean old files to prevent mix of mp3/wav
            for f in os.listdir(output_dir):
                if f.endswith((".mp3", ".wav")):
                    try: os.remove(os.path.join(output_dir, f))
                    except: pass

        audio_files = []
        total = len(subtitles)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        for i, sub in enumerate(subtitles):
            filename = f"sub_{i}.mp3"
            path = os.path.join(output_dir, filename)
            clean_text = sub['text'].strip()
            if not clean_text: continue

            try:
                # Pass 1: Generate
                loop.run_until_complete(self._generate_single_audio(clean_text, path))
                
                audio = AudioSegment.from_file(path)
                actual_duration = len(audio)
                
                start_ms = int(sub['start'] * 1000)
                if i < len(subtitles) - 1:
                    deadline_ms = int(subtitles[i+1]['start'] * 1000)
                else:
                    deadline_ms = video_duration_ms
                
                allowed_duration = deadline_ms - start_ms

                # Handle speed-up
                if self.method == "edge-tts":
                    # Pass 2 for edge-tts (native)
                    if actual_duration > allowed_duration and allowed_duration > 0:
                        speed_factor = (actual_duration / allowed_duration) - 1.0
                        # Use dynamic limit
                        rate_pct = int(min(speed_factor, self.max_speed_limit) * 100)
                        if rate_pct > 5:
                            loop.run_until_complete(self._generate_single_audio(clean_text, path, custom_rate=f"+{rate_pct}%"))
                            audio = AudioSegment.from_file(path)
                else:
                    # method == vieneu or gtts: use pydub speedup if it overflows
                    if actual_duration > allowed_duration and allowed_duration > 0:
                        speed_factor = actual_duration / allowed_duration
                        # Only speed up if it's more than 5% longer
                        if speed_factor > 1.05:
                            # Use dynamic limit (1.0 + limit)
                            max_playback = 1.0 + self.max_speed_limit
                            speed_factor = min(speed_factor, max_playback)
                            audio = audio.speedup(playback_speed=speed_factor, chunk_size=150, crossfade=25)
                            audio.export(path, format="mp3")

                audio_files.append({
                    'index': i,
                    'path': path,
                    'duration_ms': len(audio),
                    'start_original': sub['start'],
                    'end_original': sub['end']
                })
            except Exception as e:
                print(f"Error voice {i}: {e}")

            if progress_callback:
                progress_callback((i + 1) / total)

        return audio_files

    def create_full_audio_track(self, audio_data, video_duration_ms, output_path):
        """
        Combines individual audio files. 
        Allowed to overlap slightly ('đè') to maintain natural speech speed.
        """
        full_audio = AudioSegment.silent(duration=video_duration_ms)

        for i, item in enumerate(audio_data):
            segment = AudioSegment.from_file(item['path'])
            start_ms = int(item['start_original'] * 1000)
            
            # For the last clip, don't exceed video duration
            if i == len(audio_data) - 1:
                if start_ms + len(segment) > video_duration_ms:
                    fade_len = min(50, len(segment))
                    segment = segment.fade_out(fade_len)[:video_duration_ms - start_ms]
            
            # Simply overlay without strict truncation for intermediate segments
            # self.full_audio.overlay will mix the sounds if they overlap
            full_audio = full_audio.overlay(segment, position=start_ms)

        full_audio.export(output_path, format="mp3")
        return output_path
