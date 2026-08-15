"""
Gemini API handler
"""

import os
import time
import hashlib
from pathlib import Path
from google import genai
from google.genai import types

PROMPT_FUNFACT = """
Analisa video ini dan buatkan naskah voice-over FUNFACT yang mengejutkan.
- Hook di awal
- Narasi runtut
- Santai dan natural
- Durasi video: {duration}

Output FORMAT SRT MURNI (tanpa markdown):

1
00:00:00,000 --> 00:00:04,500
Kalimat pertama

2
00:00:04,500 --> 00:00:09,200
Kalimat kedua

Aturan:
- Format: HH:MM:SS,mmm
- Durasi segmen: 3-6 detik
- Hanya SRT, nothing else
"""

PROMPT_STORYTELLING = """
Analisa video ini dan buatkan naskah voice-over STORYTELLING natural.
- Seolah ngobrol santai dengan teman
- Gunakan filler: "nah", "tuh", "kan", "gitu", "soalnya"
- Natural dan mudah diucapkan
- Durasi video: {duration}

Output FORMAT SRT MURNI:

1
00:00:00,000 --> 00:00:04,500
Kalimat pertama santai

2
00:00:04,500 --> 00:00:09,200
Kalimat kedua follow-up

Aturan:
- Format: HH:MM:SS,mmm
- Durasi segmen: 4-7 detik
- Hanya SRT, nothing else
"""


class GeminiHandler:
    """Handle Gemini API calls."""
    
    def __init__(self, api_key):
        self.api_key = api_key
        os.environ['GEMINI_API_KEY'] = api_key
        self.client = genai.Client(api_key=api_key)
        self.model = 'gemini-2.0-flash-exp'
    
    def get_duration_str(self, video_path):
        """Get video duration string."""
        import subprocess
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
                capture_output=True, text=True, timeout=30
            )
            seconds = float(result.stdout.strip())
            m, s = divmod(int(seconds), 60)
            h, m = divmod(m, 60)
            return f'{h:02d}:{m:02d}:{s:02d}'
        except:
            return '00:05:00'
    
    def upload_video(self, video_path):
        """Upload video to Gemini."""
        display_name = Path(video_path).name
        
        myfile = self.client.files.upload(
            file=video_path,
            config=types.UploadFileConfig(display_name=display_name),
        )
        
        while myfile.state.name == 'PROCESSING':
            time.sleep(2)
            myfile = self.client.files.get(name=myfile.name)
        
        if myfile.state.name == 'FAILED':
            raise RuntimeError('Upload failed')
        
        return myfile
    
    def generate_srt(self, video_path, mode='funfact'):
        """Generate SRT from video."""
        duration_str = self.get_duration_str(video_path)
        prompt_template = PROMPT_STORYTELLING if mode == 'storytelling' else PROMPT_FUNFACT
        prompt = prompt_template.format(duration=duration_str)
        
        # Upload video
        myfile = self.upload_video(video_path)
        
        # Generate SRT
        for attempt in range(1, 4):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=[myfile, prompt],
                    config=types.GenerateContentConfig(
                        temperature=0.4,
                        max_output_tokens=65536,
                        media_resolution=types.MediaResolution.MEDIA_RESOLUTION_LOW,
                    ),
                )
                text = (response.text or '').strip()
                text = text.replace('```srt', '').replace('```', '').strip()
                
                # Cleanup
                try:
                    self.client.files.delete(name=myfile.name)
                except:
                    pass
                
                return text
            
            except Exception as e:
                if attempt == 3:
                    raise
                time.sleep(5)
        
        raise RuntimeError('Failed to generate SRT')


if __name__ == '__main__':
    print('✓ Gemini handler module')
