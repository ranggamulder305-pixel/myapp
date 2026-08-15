#!/usr/bin/env python3
"""
🎬 MEGA PIPELINE - KIVY APK VERSION
====================================
Native Android App - 100% Local Processing
Processing di lokal device, hanya upload video ke Gemini
"""

import os
import json
import asyncio
from pathlib import Path
from threading import Thread

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.checkbox import CheckBox

from src.processor import VideoProcessor
from src.gemini_handler import GeminiHandler

# ======================== CONFIG ========================
Window.size = (540, 960)  # Mobile size
STORAGE_PATH = Path.home() / "MEGA_PIPELINE"
UPLOAD_FOLDER = STORAGE_PATH / "uploads"
OUTPUT_FOLDER = STORAGE_PATH / "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ======================== SCREENS ========================

class HomeScreen(Screen):
    """Home/Dashboard screen."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.processor = None
        self.gemini = None
        
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # Header
        header = BoxLayout(size_hint_y=0.15, orientation='vertical')
        header.add_widget(Label(
            text='🎬 MEGA PIPELINE',
            font_size='28sp',
            bold=True,
            color=(0.4, 0.5, 1, 1)
        ))
        header.add_widget(Label(
            text='Video → SRT → VO → Final',
            font_size='12sp',
            color=(0.6, 0.6, 0.6, 1)
        ))
        layout.add_widget(header)
        
        # API Key Section
        api_box = BoxLayout(orientation='vertical', size_hint_y=0.2, spacing=5)
        api_box.add_widget(Label(text='🔐 API Key Setup', bold=True, size_hint_y=0.3))
        
        api_input_box = BoxLayout(spacing=5)
        self.api_input = TextInput(
            text=self.load_api_key() or '',
            multiline=False,
            password=True,
            size_hint_x=0.7
        )
        api_input_box.add_widget(self.api_input)
        
        save_api_btn = Button(text='✓ Save', size_hint_x=0.3)
        save_api_btn.bind(on_press=self.save_api_key)
        api_input_box.add_widget(save_api_btn)
        
        api_box.add_widget(api_input_box)
        
        show_pass_box = BoxLayout(size_hint_y=0.3)
        self.show_pass_check = CheckBox(size_hint_x=0.1)
        self.show_pass_check.bind(active=self.toggle_password)
        show_pass_box.add_widget(self.show_pass_check)
        show_pass_box.add_widget(Label(text='Show password', size_hint_x=0.9))
        api_box.add_widget(show_pass_box)
        
        layout.add_widget(api_box)
        
        # Status
        self.status_label = Label(
            text='Ready to process',
            size_hint_y=0.1,
            color=(0.2, 0.8, 0.2, 1)
        )
        layout.add_widget(self.status_label)
        
        # Mode & Voice Selection
        config_box = BoxLayout(orientation='vertical', size_hint_y=0.25, spacing=5)
        
        config_box.add_widget(Label(text='⚙️ Configuration', bold=True, size_hint_y=0.2))
        
        # Mode spinner
        mode_box = BoxLayout(size_hint_y=0.4)
        mode_box.add_widget(Label(text='Mode:', size_hint_x=0.3))
        self.mode_spinner = Spinner(
            text='FUNFACT',
            values=('FUNFACT', 'STORYTELLING'),
            size_hint_x=0.7
        )
        mode_box.add_widget(self.mode_spinner)
        config_box.add_widget(mode_box)
        
        # Voice spinner
        voice_box = BoxLayout(size_hint_y=0.4)
        voice_box.add_widget(Label(text='Voice:', size_hint_x=0.3))
        self.voice_spinner = Spinner(
            text='id-ID-ArdiNeural',
            values=(
                'id-ID-ArdiNeural',
                'id-ID-GadisNeural',
                'en-US-GuyNeural',
                'en-US-AriaNeural'
            ),
            size_hint_x=0.7
        )
        voice_box.add_widget(self.voice_spinner)
        config_box.add_widget(voice_box)
        
        layout.add_widget(config_box)
        
        # Buttons
        button_box = BoxLayout(size_hint_y=0.2, spacing=10)
        
        upload_btn = Button(text='📁 Select Video')
        upload_btn.bind(on_press=self.open_file_chooser)
        button_box.add_widget(upload_btn)
        
        process_btn = Button(text='▶️ Process')
        process_btn.bind(on_press=self.process_video)
        button_box.add_widget(process_btn)
        
        layout.add_widget(button_box)
        
        # Progress
        self.progress_bar = ProgressBar(value=0, size_hint_y=0.08)
        layout.add_widget(self.progress_bar)
        
        # Progress text
        self.progress_text = Label(
            text='',
            size_hint_y=0.08,
            font_size='11sp',
            color=(0.5, 0.5, 0.5, 1)
        )
        layout.add_widget(self.progress_text)
        
        self.add_widget(layout)
        self.selected_video = None
    
    def load_api_key(self):
        """Load saved API key."""
        try:
            config_file = STORAGE_PATH / "config.json"
            if config_file.exists():
                with open(config_file) as f:
                    data = json.load(f)
                    return data.get('api_key', '')
        except:
            pass
        return ''
    
    def save_api_key(self, instance):
        """Save API key."""
        api_key = self.api_input.text.strip()
        if not api_key:
            self.status_label.text = '❌ API key kosong'
            self.status_label.color = (1, 0.2, 0.2, 1)
            return
        
        config_file = STORAGE_PATH / "config.json"
        with open(config_file, 'w') as f:
            json.dump({'api_key': api_key}, f)
        
        os.environ['GEMINI_API_KEY'] = api_key
        
        self.status_label.text = '✓ API key saved'
        self.status_label.color = (0.2, 0.8, 0.2, 1)
    
    def toggle_password(self, instance, value):
        """Toggle password visibility."""
        self.api_input.password = not value
    
    def open_file_chooser(self, instance):
        """Open file chooser."""
        chooser = FileChooserListView(
            filters=['*.mp4', '*.mov', '*.webm', '*.avi']
        )
        popup = Popup(
            title='Select Video',
            content=chooser,
            size_hint=(0.9, 0.9)
        )
        
        def on_select(path, filename):
            if filename:
                self.selected_video = os.path.join(path, filename[0])
                self.status_label.text = f'✓ Selected: {filename[0]}'
                self.status_label.color = (0.2, 0.8, 0.2, 1)
            popup.dismiss()
        
        chooser.bind(on_selection=on_select)
        popup.open()
    
    def process_video(self, instance):
        """Start video processing."""
        if not self.selected_video:
            self.status_label.text = '❌ Select video first'
            self.status_label.color = (1, 0.2, 0.2, 1)
            return
        
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            self.status_label.text = '❌ Set API key first'
            self.status_label.color = (1, 0.2, 0.2, 1)
            return
        
        # Start processing in background thread
        mode = self.mode_spinner.text.lower()
        voice = self.voice_spinner.text
        
        thread = Thread(
            target=self.run_processing,
            args=(self.selected_video, mode, voice, api_key)
        )
        thread.daemon = True
        thread.start()
    
    def run_processing(self, video_path, mode, voice, api_key):
        """Run processing (in background thread)."""
        try:
            self.processor = VideoProcessor(OUTPUT_FOLDER)
            self.gemini = GeminiHandler(api_key)
            
            # Update status
            self.update_status('🧠 Generating SRT...', 0)
            
            # Generate SRT
            srt_text = self.gemini.generate_srt(video_path, mode)
            self.update_status('✓ SRT Generated', 30)
            
            # Save SRT
            srt_path = OUTPUT_FOLDER / f"{Path(video_path).stem}.srt"
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write(srt_text)
            self.update_status('🎙️ Generating VO...', 50)
            
            # Generate VO
            vo_path = self.processor.generate_vo(str(srt_path), voice)
            self.update_status('✓ VO Generated', 75)
            
            # Merge
            self.update_status('🎬 Merging...', 85)
            output_path = OUTPUT_FOLDER / f"{Path(video_path).stem}_FINAL.mp4"
            self.processor.merge_video_vo(video_path, vo_path, str(output_path))
            self.update_status('✓ Done!', 100)
            
            # Show download message
            Clock.schedule_once(
                lambda dt: self.show_download_popup(str(output_path)),
                0.5
            )
        
        except Exception as e:
            self.update_status(f'❌ Error: {str(e)[:50]}', 0)
    
    def update_status(self, text, progress):
        """Update UI from background thread."""
        Clock.schedule_once(
            lambda dt: self._update_ui(text, progress),
            0
        )
    
    def _update_ui(self, text, progress):
        """Update UI (must be called from main thread)."""
        self.status_label.text = text
        self.progress_bar.value = progress
        self.progress_text.text = f'{progress}%'
    
    def show_download_popup(self, output_path):
        """Show download popup."""
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(Label(text='✓ Video processed successfully!'))
        layout.add_widget(Label(text=f'Saved at:\n{output_path}'))
        
        btn_box = BoxLayout(size_hint_y=0.3, spacing=5)
        
        open_btn = Button(text='📁 Open Folder')
        open_btn.bind(on_press=lambda x: os.system(f'am start -a android.intent.action.VIEW -d file://{OUTPUT_FOLDER}'))
        btn_box.add_widget(open_btn)
        
        close_btn = Button(text='✓ Close')
        btn_box.add_widget(close_btn)
        
        layout.add_widget(btn_box)
        
        popup = Popup(title='Download', content=layout, size_hint=(0.9, 0.6))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()


class SettingsScreen(Screen):
    """Settings screen."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        layout.add_widget(Label(text='⚙️ Settings', bold=True, size_hint_y=0.1))
        
        scroll = ScrollView()
        content = GridLayout(cols=1, spacing=10, size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        # Info
        info_text = """
🎬 MEGA PIPELINE v1.0

📱 Native Android App
🔄 Local Processing
⚡ Fast & Efficient

VIDEO PROCESSING:
1. Upload video
2. Generate SRT (via Gemini API)
3. Generate VO (TTS)
4. Merge video + VO

STORAGE:
📁 /sdcard/MEGA_PIPELINE/

FEATURES:
✓ Offline processing
✓ Multiple voices
✓ FUNFACT/STORYTELLING modes
✓ Fast local processing

REQUIREMENTS:
- Internet (for Gemini API only)
- 500MB storage min
- 2GB RAM min

Made with ❤️ using Kivy
        """
        
        content.add_widget(Label(
            text=info_text,
            size_hint_y=None,
            height=400,
            text_size=(300, None)
        ))
        
        scroll.add_widget(content)
        layout.add_widget(scroll)
        
        self.add_widget(layout)


class MegaPipelineApp(App):
    """Main Kivy Application."""
    
    def build(self):
        self.title = '🎬 MEGA PIPELINE'
        
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(SettingsScreen(name='settings'))
        
        # Main layout with navigation
        main_layout = BoxLayout(orientation='vertical')
        
        # Screen manager
        main_layout.add_widget(sm)
        
        # Bottom navigation
        nav_box = BoxLayout(size_hint_y=0.1, spacing=5, padding=5)
        
        home_btn = Button(text='🏠 Home')
        home_btn.bind(on_press=lambda x: setattr(sm, 'current', 'home'))
        nav_box.add_widget(home_btn)
        
        settings_btn = Button(text='⚙️ Settings')
        settings_btn.bind(on_press=lambda x: setattr(sm, 'current', 'settings'))
        nav_box.add_widget(settings_btn)
        
        main_layout.add_widget(nav_box)
        
        return main_layout


if __name__ == '__main__':
    MegaPipelineApp().run()
