import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import datetime
import whisper
import spacy
from spacy.lang.en import English
import gensim
from gensim import corpora
import pydub
import os
import pafy
#import vlc
import youtube_dl
import subprocess
import pytube
import webbrowser
from tkinterhtml import HtmlFrame
import tkinterweb as tkweb

import gensim.downloader as api

#model = api.load("lda_enwiki")
# View available models
#print(api.info())

# Load the Gensim LDA model
#lda_model = gensim.models.LdaModel.load('lda_model')
#lda_model = api.load('lda_multicore')


# Load the Whisper ASR model
model = whisper.load_model('base.en')

# Load the spaCy English language model
nlp = English()
#nlp = spacy.load("en_core_web_sm")



# Function to transcribe the audio using the ASR model
def transcribe_audio(audio_path):
    # Load the audio file using PyDub
    audio = pydub.AudioSegment.from_file(audio_path)
    audio = audio.set_channels(1) # Convert to mono channel

    # Export the audio to a WAV file
    temp_path = os.path.join(os.path.dirname(audio_path), 'temp.wav')
    audio.export(temp_path, format='wav')

    # Transcribe the audio using the ASR model
    result = model.transcribe(temp_path)

    # Delete the temporary audio file
    os.remove(temp_path)

    return result['text']

# Function to perform topic modeling on the transcribed text
def perform_topic_modeling(text, num_topics=5):
    # Tokenize the text using spaCy
    doc = nlp(text)
    tokens = [token.text for token in doc]

    # Create a Gensim dictionary and corpus
    dictionary = gensim.corpora.Dictionary([tokens])
    corpus = [dictionary.doc2bow(tokens)]

    # Train LDA on the corpus
    lda_model = gensim.models.LdaModel(corpus, num_topics=num_topics, id2word=dictionary)

    # Perform LDA on the corpus
    lda_result = lda_model[corpus][0]

    # Get the most probable topic and its time stamp
    topic = max(lda_result, key=lambda x: x[1])
    topic_id = topic[0]
    topic_prob = topic[1]
    topic_words = [word for word, prob in lda_model.show_topic(topic_id)]

    # Get the time stamp of the most probable topic
    start_time = text.find(topic_words[0])
    end_time = text.find(topic_words[-1]) + len(topic_words[-1])
    time_stamp = str(datetime.timedelta(seconds=start_time)) + ' - ' + str(datetime.timedelta(seconds=end_time))

    return topic_id, topic_prob, topic_words, time_stamp

# Function to search for a YouTube video using its ID
def search_youtube():
    # Get the video ID from the search input
    video_id = search_input.get()
    url = "https://www.youtube.com/watch?v=" + video_id

    try:
        # Load the video using the pafy library
        video = pafy.new(url)

        # Display the metadata for the video
        display_metadata(video)

        # Transcribe the video
        transcribe_youtube(url)
    except:
        # If an error occurs, display a message in the status bar
        #tk.status_bar.configure(text="Error: Unable to load video")
        print('unable to load video')

# Function to display the metadata for a YouTube video
def display_metadata(video):
    # Get the video metadata
    title = video.title
    author = video.author
    video_id = video.videoid
    duration = video.duration
    rating = video.rating
    views = video.viewcount
    thumbnail = video.thumb

    # Display the metadata in a text widget
    metadata_text.delete('1.0', tk.END)
    metadata_text.insert(tk.END, f'Title: {title}\n')
    metadata_text.insert(tk.END, f'Author: {author}\n')
    metadata_text.insert(tk.END, f'ID: {video_id}\n')
    metadata_text.insert(tk.END, f'Duration: {duration}\n')
    metadata_text.insert(tk.END, f'Rating: {rating}\n')
    metadata_text.insert(tk.END, f'Views: {views}\n')
    metadata_text.insert(tk.END, f'Thumbnail: {thumbnail}\n')

# Function to transcribe a YouTube video
def transcribe_youtube(video_url):
    # Download the audio from the YouTube video in WAV format
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
    }
    #with youtube_dl.YoutubeDL(ydl_opts) as ydl:
       ## audio_path = ydl.prepare_filename(info_dict['formats'][0]['ext'])
    # Download the YouTube video using Pytube
    youtube = pytube.YouTube(video_url)
    #list = youtube.streams.filter(file_extension='wav')
    audio= youtube.streams.get_by_itag(139)
    audio.download('','temp.mp4')

    # Convert the downloaded video to WAV format
    try:
        subprocess.run(["ffmpeg", "-i", "temp.mp4", "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", "temp.wav"],check=True)

    except subprocess.CalledProcessError as e:
        print('An error occurred:', e)

    # Transcribe the audio using the ASR model
    text = transcribe_audio('temp.wav')

    # Perform topic modeling on the transcribed text
    topic_id, topic_prob, topic_words, time_stamp = perform_topic_modeling(text)

    # Display the transcribed text in the text widget
    transcribed_text.delete('1.0', tk.END)
    transcribed_text.insert(tk.END, text)

    # Display the topic and time stamp in the label
    topic_label.configure(text=f'Topic: {topic_id} ({topic_prob:.2f})')
    time_stamp_label.configure(text=f'Time Stamp: {time_stamp}')

# Function to export the transcribed text to a file
def export_text():
    # Get the filename from the user
    filename = filedialog.asksaveasfilename(defaultextension=".txt")

    # Write the transcribed text to the file
    with open(filename, 'w') as file:
        file.write(transcribed_text.get('1.0', tk.END))


"""
# Create the main window
root = tk.Tk()
root.title("YouTube Topic Extractor")

# Create the search frame
search_frame = ttk.Frame(root, padding=20)
search_frame.pack(fill=tk.BOTH, expand=True)

# Create the search label and input
search_label = ttk.Label(search_frame, text="Enter YouTube Video ID:")
search_label.pack(side=tk.LEFT, padx=(0, 10))

search_input = ttk.Entry(search_frame)
search_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# create a new webview
webview = tkweb.WebView(root)


# set the size of the webview
webview.set_size(640, 480)

# set the URL of the YouTube video
webview.load_url('https://www.youtube.com/watch/?v=roq8N_AqcIA')

# add the webview to the window
webview.pack(fill=tk.BOTH, expand=tk.YES)

# Create the search button
search_button = ttk.Button(search_frame, text="Search", command=search_youtube)
search_button.pack(side=tk.LEFT, padx=(10, 0))

# Create the metadata frame
metadata_frame = ttk.Frame(root, padding=20)
metadata_frame.pack(fill=tk.BOTH, expand=True)

# Create the metadata label and text widget
metadata_label = ttk.Label(metadata_frame, text="Video Metadata")
metadata_label.pack()

metadata_text = tk.Text(metadata_frame, height=10)
metadata_text.pack(fill=tk.BOTH, expand=True)

# Create the transcribed text frame
transcribed_frame = ttk.Frame(root, padding=20)
transcribed_frame.pack(fill=tk.BOTH, expand=True)

# Create the transcribed text label and text widget
transcribed_label = ttk.Label(transcribed_frame, text="Transcribed Text")
transcribed_label.pack()

transcribed_text = tk.Text(transcribed_frame, height=10)
transcribed_text.pack(fill=tk.BOTH, expand=True)

# Create the topic and time stamp label
topic_label = ttk.Label(root, text="")
topic_label.pack()

time_stamp_label = ttk.Label(root, text="")
time_stamp_label.pack()

# Create the export button
export_button = ttk.Button(root, text="Export Text", command=export_text)
export_button.pack(pady=20)
root.mainloop()

"""

# start the tkinter main loop
#window.mainloop()

"""
# Open a YouTube video in the default web browser
url = 'https://www.youtube.com/watch?v=roq8N_AqcIA' # Replace with your video URL
webbrowser.open(url)

# Embed the browser window in your Tkinter application using tkinterhtml
frame = HtmlFrame(root, width=640, height=480)
frame.grid(row=0, column=0)
frame.load_url(url)
"""


# Create the status bar
#status_bar = ttk.Label(root, text="", relief=tk.SUNKEN, anchor=tk.W)
#status_bar.pack(side=tk.BOTTOM, fill=tk.X)


# Create the main window
window = tk.Tk()
window.title('Lecture Notes Transcription')

# Create the search input and search button
search_label = ttk.Label(window, text='Enter YouTube Video ID:')
search_label.pack(padx=5, pady=5)
search_input = ttk.Entry(window)
search_input.pack(padx=5, pady=5)
search_button = ttk.Button(window, text='Search', command=search_youtube)

search_button.pack(padx=5, pady=5)

# Create the metadata display area
metadata_label = ttk.Label(window, text='Metadata:')
metadata_label.pack(padx=5, pady=5)
metadata_text = tk.Text(window, height=7, width=60)
metadata_text.pack(padx=5, pady=5)

# Create the transcribed text display area
transcribed_text_label = ttk.Label(window, text='Transcribed Text:')
transcribed_text_label.pack(padx=5, pady=5)
transcribed_text = tk.Text(window, height=15, width=60)
transcribed_text.pack(padx=5, pady=5)

# Create the topic and time stamp display area
topic_label = ttk.Label(window, text='Topic:')
topic_label.pack(padx=5, pady=5)
time_stamp_label = ttk.Label(window, text='Time Stamp:')
time_stamp_label.pack(padx=5, pady=5)


# Create the export button
export_button = ttk.Button(window, text='Export', command=export_text)
export_button.pack(padx=5, pady=5)

# Start the main event loop
window.mainloop()


"""

window = tk.Tk()
window.title("YouTube Lecture Transcriber")

# Create search input box
search_input = ttk.Entry(window, width=40)
search_input.grid(row=0, column=0, padx=5, pady=5)

# Create search button
search_button = ttk.Button(window, text="Search")
search_button.grid(row=0, column=1, padx=5, pady=5)

# Create metadata box
metadata_box = tk.Text(window, height=5, width=60)
metadata_box.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
metadata_box.configure(state='disabled')
"""




# Bind the search button to the search_video function
#search_button.config(command=search_youtube)

# Create a VLC instance and media player
#instance = vlc.Instance()
#player = instance.media_player_new()

# Create a function to handle the clickable timestamps
#def seek(timestamp):
 #   media = instance.media_new(url)
  #  media.parse()
   # player.set_media(media)
   # player.play()
   # player.set_time(timestamp)

# Implement the clickable timestamps using tagging in the transcribed text box
#transcribed_text.tag_configure("timestamp", foreground="blue", underline=True)
#transcribed_text.tag_bind("timestamp", "<Button-1>", lambda event: seek(int(event.widget.tag_prevrange("timestamp", event.widget.index(tk.CURRENT))[1])))

# Populate the transcribed text box with the output of your speech recognition model
#transcribed_text.insert(tk.END, "Transcribed text goes here...")



# Bind the export button to the export_text function
#export_button.config(command=export_text)