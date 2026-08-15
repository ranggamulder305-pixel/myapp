"""
Video/Audio processing utilities
"""

import os
import subprocess
import tempfile
import shutil
import asyncio
import srt
from pathlib import Path


class VideoProcessor:
    """Handle video/audio processing."""
    
    def __init__(self, output_folder):
        self.output_folder = Path(output_folder)
        self.temp_dir = tempfile.mkdtemp(prefix='vo_')
    
    def get_duration(self, path):
        """Get duration in seconds."""
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1', path],
                capture_output=True, text=True, timeout=30
            )
            return float(result.stdout.strip())
        except:
            return 0.0
    
    async def generate_tts(self, text, voice, out_path):
        """Generate TTS using edge-tts."""
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(out_path)
    
    def stretch_audio(self, in_path, out_path, target_duration):
        """Stretch audio to target duration."""
        actual_duration = self.get_duration(in_path)
        if actual_duration <= 0:
            shutil.copy(in_path, out_path)
            return
        
        factor = actual_duration / target_duration
        factor = max(0.75, min(1.5, factor))
        
        atempo = self.build_atempo(factor)
        subprocess.run(
            ['ffmpeg', '-y', '-i', in_path, '-filter:a', atempo, out_path],
            capture_output=True
        )
    
    def build_atempo(self, factor):
        """Build atempo filter."""
        filters = []
        remaining = factor
        if remaining <= 0:
            return 'atempo=1.0'
        while remaining > 2.0:
            filters.append('atempo=2.0')
            remaining /= 2.0
        while remaining < 0.5:
            filters.append('atempo=0.5')
            remaining /= 0.5
        filters.append(f'atempo={remaining:.6f}')
        return ','.join(filters)
    
    def assemble_vo(self, segments, output_file):
        """Assemble audio segments."""
        if not segments:
            return
        
        input_args = []
        filter_parts = []
        for i, (start, path) in enumerate(segments):
            input_args += ['-i', path]
            delay_ms = int(round(start * 1000))
            filter_parts.append(f'[{i}:a]adelay={delay_ms}|{delay_ms}[a{i}]')
        
        mix_inputs = ''.join(f'[a{i}]' for i in range(len(segments)))
        filter_complex = ';'.join(filter_parts) + f';{mix_inputs}amix=inputs={len(segments)}:normalize=0[out]'
        
        cmd = ['ffmpeg', '-y'] + input_args + [
            '-filter_complex', filter_complex,
            '-map', '[out]',
            output_file
        ]
        subprocess.run(cmd, capture_output=True)
    
    def generate_vo(self, srt_file, voice):
        """Generate VO from SRT file."""
        output_file = str(self.output_folder / f"{Path(srt_file).stem}_vo.wav")
        
        with open(srt_file, 'r', encoding='utf-8') as f:
            subs = list(srt.parse(f.read()))
        
        segments = []
        valid_subs = [s for s in subs if s.content.strip() and not s.content.startswith('[')]
        
        for i, sub in enumerate(valid_subs):
            text = sub.content.strip()
            start = sub.start.total_seconds()
            end = sub.end.total_seconds()
            target_duration = end - start
            
            if target_duration <= 0:
                continue
            
            if i + 1 < len(valid_subs):
                next_start = valid_subs[i + 1].start.total_seconds()
                max_allowed_duration = max(target_duration, next_start - start - 0.05)
            else:
                max_allowed_duration = target_duration + 3.0
            
            raw_path = os.path.join(self.temp_dir, f'seg_{sub.index:04d}_raw.mp3')
            final_path = os.path.join(self.temp_dir, f'seg_{sub.index:04d}.wav')
            
            # Generate TTS
            asyncio.run(self.generate_tts(text, voice, raw_path))
            self.stretch_audio(raw_path, final_path, target_duration)
            segments.append((start, final_path))
        
        self.assemble_vo(segments, output_file)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        return output_file
    
    def merge_video_vo(self, video_path, vo_path, output_path):
        """Merge video + VO."""
        subprocess.run([
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', vo_path,
            '-c:v', 'copy', '-c:a', 'aac',
            '-map', '0:v:0', '-map', '1:a:0',
            '-shortest',
            output_path
        ], capture_output=True)


if __name__ == '__main__':
    print('✓ Processor module')
