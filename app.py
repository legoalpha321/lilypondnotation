import streamlit as st
import os
import subprocess
import tempfile
import base64
from pathlib import Path
import platform
import shutil

st.set_page_config(
    page_title="LilyPond to PDF Converter",
    page_icon="🎵",
    layout="wide"
)

# Title and description
st.title("LilyPond to PDF Converter")
st.markdown("""
This app converts LilyPond notation to PDF sheet music. 
You'll need to have LilyPond installed on the server where this Streamlit app is running.
""")

# Check if LilyPond is installed on the server
@st.cache_resource
def find_lilypond():
    """Attempt to find the LilyPond executable on the system."""
    try:
        # Try to get LilyPond version which will fail if not installed
        result = subprocess.run(['lilypond', '--version'], 
                                capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return 'lilypond'  # It's in the PATH
    except FileNotFoundError:
        pass
        
    # Common installation paths to check
    common_paths = []
    
    # Windows common paths
    if os.name == 'nt':
        program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
        program_files_x86 = os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')
        
        for base_dir in [program_files, program_files_x86]:
            common_paths.extend([
                os.path.join(base_dir, 'LilyPond', 'usr', 'bin', 'lilypond.exe'),
                os.path.join(base_dir, 'LilyPond', 'bin', 'lilypond.exe')
            ])
    
    # macOS common paths
    elif platform.system() == 'darwin':
        common_paths.extend([
            '/Applications/LilyPond.app/Contents/Resources/bin/lilypond',
            os.path.expanduser('~/Applications/LilyPond.app/Contents/Resources/bin/lilypond')
        ])
    
    # Linux common paths
    else:
        common_paths.extend([
            '/usr/bin/lilypond',
            '/usr/local/bin/lilypond'
        ])
    
    # Check each path
    for path in common_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
            
    return None

lilypond_path = find_lilypond()

# Display LilyPond status
if lilypond_path:
    st.success(f"✅ LilyPond found at: {lilypond_path}")
else:
    st.error("❌ LilyPond not found. You need to install LilyPond on the server running this app.")
    st.info("Download LilyPond from [lilypond.org](https://lilypond.org/download.html)")

# Piano sheet sample
piano_sheet = r"""\version "2.20.0"

\header {
  title = "Ascension"
  subtitle = "An Epic Piano Journey"
  composer = "Composed for You"
}

\paper {
  #(set-paper-size "letter")
}

global = {
  \key d \major
  \time 4/4
  \tempo "With passion" 4 = 72
}

upper = \relative c'' {
  \global
  \clef treble
  
  % Introduction - Majestic and contemplative
  \partial 4 a4\mp |
  <d fis a>2. <cis e a>4 |
  <b d g>2. <a d fis>4 |
  <g b e>2 <fis a d>2 |
  <e a cis>2. a,4\< |
  
  <d fis a>2.\mf <e g b>4 |
  <fis a d>2. <g b e>4 |
  <a cis e>2 <b d fis>2 |
  <a cis e>2. r4\! |
  
  % Main theme - Hopeful and building
  d,4\mp\< fis a d |
  cis4. b8 a4 fis |
  b4. a8 g4 d |
  e4. fis8 g4\mf a\> |
  
  d,4\mp fis a d |
  e4. d8 cis4 a |
  b4. a8 g4 e |
  fis2\> d2\mp\! |
  
  % First few measures of the piece for brevity
  \bar "|."
}

lower = \relative c {
  \global
  \clef bass
  
  % Introduction
  \partial 4 r4 |
  d4 a' d, a' |
  g,4 d' g, d' |
  e,4 b' e, b' |
  a,4 e' a, e' |
  
  d4 a' d, a' |
  d,4 a' d, a' |
  a,4 e' a, e' |
  a,4 e' a, e' |
  
  % Main theme
  d4 a' fis a |
  a,4 e' a, e' |
  g,4 d' g, d' |
  a4 e' a, e' |
  
  d4 a' fis a |
  a,4 e' a, e' |
  g,4 d' g, d' |
  a4 d fis a |
  
  \bar "|."
}

\score {
  \new PianoStaff <<
    \new Staff = "upper" \upper
    \new Staff = "lower" \lower
  >>
  \layout { }
  \midi { }
}"""

# Create tabs
tab1, tab2 = st.tabs(["Input Text", "Upload File"])

# Initialize session state for storing generated files
if 'pdf_generated' not in st.session_state:
    st.session_state.pdf_generated = False
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None
if 'pdf_filename' not in st.session_state:
    st.session_state.pdf_filename = None
if 'midi_data' not in st.session_state:
    st.session_state.midi_data = None
if 'midi_filename' not in st.session_state:
    st.session_state.midi_filename = None
if 'wav_data' not in st.session_state:
    st.session_state.wav_data = None

with tab1:
    # Text input area
    st.subheader("Enter LilyPond Notation")
    
    # Button to load sample
    if st.button("Load Sample"):
        ly_text = piano_sheet
        # Clear previous generated files when loading new content
        st.session_state.pdf_generated = False
    else:
        ly_text = st.session_state.get('ly_text', '')
    
    text_area = st.text_area("LilyPond Code", value=ly_text, height=400)
    
    # Clear previous generated files if text changes
    if 'ly_text' in st.session_state and st.session_state.ly_text != text_area:
        st.session_state.pdf_generated = False
    
    st.session_state['ly_text'] = text_area
    
    # Output options
    output_filename = st.text_input("Output Filename", value="my_sheet_music")
    
    # Convert button
    convert_text = st.button("Convert to PDF", key="convert_text")

with tab2:
    # File upload
    st.subheader("Upload LilyPond File")
    uploaded_file = st.file_uploader("Choose a LilyPond file", type=['ly'])
    
    # Clear previous generated files if a new file is uploaded
    if uploaded_file is not None and 'last_uploaded_file' in st.session_state:
        if st.session_state.last_uploaded_file != uploaded_file.name:
            st.session_state.pdf_generated = False
            st.session_state.last_uploaded_file = uploaded_file.name
    elif uploaded_file is not None:
        st.session_state.last_uploaded_file = uploaded_file.name
    
    # Output options for file upload
    if uploaded_file is not None:
        # Default filename from uploaded file
        default_name = os.path.splitext(uploaded_file.name)[0]
    else:
        default_name = "output"
        
    output_filename_file = st.text_input("Output Filename", value=default_name, key="file_output")
    
    # Convert button
    convert_file = st.button("Convert to PDF", key="convert_file")

# Function to find FluidSynth
@st.cache_resource
def find_fluidsynth():
    """Attempt to find the FluidSynth executable on the system."""
    try:
        # Try to get FluidSynth version which will fail if not installed
        result = subprocess.run(['fluidsynth', '--version'], 
                                capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return 'fluidsynth'  # It's in the PATH
    except FileNotFoundError:
        pass
        
    # Common installation paths to check
    common_paths = []
    
    # Windows common paths
    if os.name == 'nt':
        program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
        program_files_x86 = os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')
        
        for base_dir in [program_files, program_files_x86]:
            common_paths.extend([
                os.path.join(base_dir, 'FluidSynth', 'bin', 'fluidsynth.exe'),
            ])
    
    # macOS common paths
    elif platform.system() == 'darwin':
        common_paths.extend([
            '/usr/local/bin/fluidsynth',
            '/opt/homebrew/bin/fluidsynth'
        ])
    
    # Linux common paths
    else:
        common_paths.extend([
            '/usr/bin/fluidsynth',
            '/usr/local/bin/fluidsynth'
        ])
    
    # Check each path
    for path in common_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
            
    return None

# Function to find SoundFont file
@st.cache_resource
def find_soundfont():
    """Attempt to find a suitable SoundFont file on the system."""
    # Common SoundFont paths
    common_paths = []
    
    # Windows common paths
    if os.name == 'nt':
        program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
        program_files_x86 = os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')
        
        for base_dir in [program_files, program_files_x86]:
            common_paths.extend([
                os.path.join(base_dir, 'FluidSynth', 'share', 'soundfonts', 'default.sf2'),
            ])
    
    # macOS common paths
    elif platform.system() == 'darwin':
        common_paths.extend([
            '/usr/local/share/soundfonts/default.sf2',
            '/opt/homebrew/share/soundfonts/default.sf2'
        ])
    
    # Linux common paths
    else:
        common_paths.extend([
            '/usr/share/sounds/sf2/FluidR3_GM.sf2',
            '/usr/share/soundfonts/default.sf2',
            '/usr/share/soundfonts/FluidR3_GM.sf2'
        ])
    
    # Check each path
    for path in common_paths:
        if os.path.isfile(path):
            return path
            
    return None

# Function to convert MIDI to WAV
def midi_to_wav(midi_path):
    """Convert a MIDI file to WAV using FluidSynth."""
    fluidsynth_path = find_fluidsynth()
    soundfont_path = find_soundfont()
    
    if not fluidsynth_path:
        st.warning("FluidSynth not found. Audio preview unavailable.")
        return None
        
    if not soundfont_path:
        st.warning("SoundFont not found. Audio preview unavailable.")
        return None
    
    output_dir = os.path.dirname(midi_path)
    wav_path = os.path.splitext(midi_path)[0] + '.wav'
    
    try:
        command = [
            fluidsynth_path,
            '-ni',
            soundfont_path,
            midi_path,
            '-F', wav_path
        ]
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            st.warning(f"Error converting MIDI to WAV: {result.stderr}")
            return None
            
        return wav_path
    except Exception as e:
        st.warning(f"Error in MIDI to WAV conversion: {str(e)}")
        return None

# Processing logic
if (convert_text or convert_file) and lilypond_path:
    # Create a status container
    status_container = st.empty()
    status_container.info("Starting conversion...")
    
    try:
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Get LilyPond content
            if convert_text:
                ly_content = text_area
                output_name = output_filename
            else:  # convert_file
                if uploaded_file is None:
                    st.error("Please upload a LilyPond file.")
                    st.stop()
                    
                # Read uploaded file
                ly_content = uploaded_file.getvalue().decode("utf-8")
                output_name = output_filename_file
            
            # Create temporary LilyPond file
            temp_ly_path = os.path.join(temp_dir, "score.ly")
            with open(temp_ly_path, 'w') as f:
                f.write(ly_content)
            
            # Run LilyPond
            status_container.info("Running LilyPond...")
            result = subprocess.run(
                [lilypond_path, '--output=' + temp_dir, temp_ly_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                status_container.error(f"LilyPond Error: {result.stderr}")
                st.stop()
            
            # Check if PDF was generated
            temp_pdf_path = os.path.join(temp_dir, "score.pdf")
            if not os.path.exists(temp_pdf_path):
                status_container.error("LilyPond did not generate a PDF.")
                st.stop()
            
            # Copy to a more permanent location within the streamlit cache
            cache_dir = os.path.join(tempfile.gettempdir(), "streamlit_lilypond_cache")
            os.makedirs(cache_dir, exist_ok=True)
            final_pdf_path = os.path.join(cache_dir, f"{output_name}.pdf")
            
            import shutil
            shutil.copy2(temp_pdf_path, final_pdf_path)
            
            # Store PDF data in session state
            with open(final_pdf_path, "rb") as pdf_file:
                pdf_data = pdf_file.read()
                st.session_state.pdf_data = pdf_data
                st.session_state.pdf_filename = f"{output_name}.pdf"
            
            # Also generate MIDI if available
            temp_midi_path = os.path.join(temp_dir, "score.midi")
            if os.path.exists(temp_midi_path):
                final_midi_path = os.path.join(cache_dir, f"{output_name}.midi")
                shutil.copy2(temp_midi_path, final_midi_path)
                
                with open(final_midi_path, "rb") as midi_file:
                    midi_data = midi_file.read()
                    st.session_state.midi_data = midi_data
                    st.session_state.midi_filename = f"{output_name}.midi"
                
                # Try to convert MIDI to WAV for audio playback
                wav_path = midi_to_wav(final_midi_path)
                if wav_path and os.path.exists(wav_path):
                    with open(wav_path, "rb") as wav_file:
                        st.session_state.wav_data = wav_file.read()
                else:
                    st.session_state.wav_data = None
            else:
                st.session_state.midi_data = None
                st.session_state.midi_filename = None
                st.session_state.wav_data = None
            
            # Mark as successful
            st.session_state.pdf_generated = True
            
            # Remove status message as we'll show success in the permanent UI
            status_container.empty()
            
            # Force a rerun to show the download buttons
            st.rerun()
    
    except Exception as e:
        st.error(f"Error during conversion: {str(e)}")

# Footer with instructions
st.markdown("---")
st.markdown("""
### How to Use This App
1. Enter LilyPond notation or upload a .ly file
2. Set your desired output filename
3. Click "Convert to PDF"
4. Download the generated PDF

### About LilyPond
[LilyPond](https://lilypond.org/) is an open-source music engraving program that produces beautiful sheet music. 
This app requires LilyPond to be installed on the server where Streamlit is running.
""")