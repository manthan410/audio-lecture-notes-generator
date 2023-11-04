import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
#from tkinterweb import WebView
from pytube import YouTube
from moviepy.editor import VideoFileClip

def download_video(video_url):
    try:
        # Download the video using pytube
        yt = YouTube(video_url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
        filename = stream.default_filename
        stream.download()

        # Convert the video to a format that can be displayed in tkinter
        clip = VideoFileClip(filename)
        clip.write_videofile('temp.mp4')

        # Delete the original video file
        stream.download(filename)
    except Exception as e:
        messagebox.showerror('Error', str(e))

def play_video():
    # Download and convert the video
    download_video(video_url.get())

    # Create a tkinter window
    window = tk.Toplevel(root)

    # Create a canvas to display the video
    canvas = tk.Canvas(window, width=560, height=315)
    canvas.pack()

    # Load the video into the canvas
    player = tk.PhotoImage(file='temp.mp4')
    canvas.create_image(0, 0, anchor=tk.NW, image=player)

# Create the main tkinter window
root = tk.Tk()

# Create a label and entry for the YouTube video URL
ttk.Label(root, text='Enter YouTube video URL:').grid(row=0, column=0, padx=10, pady=10)
video_url = tk.StringVar()
ttk.Entry(root, textvariable=video_url, width=50).grid(row=0, column=1, padx=10, pady=10)

# Create a button to play the video
ttk.Button(root, text='Play', command=play_video).grid(row=1, column=0, columnspan=2, padx=10, pady=10)

# Start the tkinter event loop
root.mainloop()
