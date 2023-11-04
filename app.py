import streamlit as st
import pafy # optionally depends on youtube_dl
import pandas as pd
import subprocess
import pytube
import whisper
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

def transcribe_asr(vd_url):
    print("Video Downloading Started....")
    # Extract the YouTube video using Pytube
    yt_video = pytube.YouTube(vd_url)
    #list = youtube.streams.filter(file_extension='wav')
    audio = yt_video.streams.get_by_itag(139)
    audio.download('','temp.mp4')

    # Convert the downloaded video to WAV format
    try:
        subprocess.run(["ffmpeg", "-i", "temp.mp4", "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", "temp.wav"],check=True)

    except subprocess.CalledProcessError as e:
        print('An error occurred:', e)

    print("Video Downloading Started....")

    print("Transcription Process Started....")
    model = whisper.load_model('base.en')
    whisper.DecodingOptions(fp16=False)
    result = model.transcribe('temp.wav')

    print("Transcription Completed...")

    return result['segments']

def transcript_preprocess(vd_url):

    # Filter out unwanted columns
    filtered_text = [{k: v for k, v in entry.items() if k in ['id', 'start', 'end', 'text']} for entry in
                     transcribe_asr(vd_url)]
    print("Preprocessing transcript Started....")
    # Convert seconds to 'm's and 's's format according to youtube time format
    for entry in filtered_text:
        entry['start'] = f"{int(entry['start']) // 60}m{int(entry['start']) % 60}s"
        entry['end'] = f"{int(entry['end']) // 60}m{int(entry['end']) % 60}s"

    df = pd.DataFrame(filtered_text)

    # Rename columns for clarity
    df = df.rename(columns={'id': 'ID', 'start': 'Start Timestamp', 'end': 'End Timestamp', 'text': 'Sentences'})


    grouped_paragraphs = []
    grouped_paragraphs_topic = []
    start_timestamps = []
    end_timestamps = []
    group_size = 5

    for i in range(0, len(df), group_size):
        # Ensure range for extracting sentences doesn't exceed the dataFrame's index
        end_index = min(i + group_size, len(df))
        sentences = df['Sentences'].iloc[i:end_index].tolist()
        paragraph = ' '.join(sentences)
        grouped_paragraphs.append(paragraph)


        # Aggregate start and end timestamps for the group
        start = df['Start Timestamp'].iloc[i]
        end = df['End Timestamp'].iloc[end_index - 1]
        start_timestamps.append(start)
        end_timestamps.append(end)

    grouped_df = pd.DataFrame({'Start Timestamp': start_timestamps,
                               'End Timestamp': end_timestamps, 'Paragraphs': grouped_paragraphs})

    print("Preprocessing transcript Completed...")
    #grouped_df.head(10)
    return grouped_df


def generate_video_topic_transcription(vd_url):

    # Initialize BERTopic model with custom models
    vectorizer = CountVectorizer(stop_words="english")
    dim_model = PCA(n_components=1)
    cluster_model = KMeans(n_clusters=1)

    print("Topic model [RUNNING]...")

    topic_model = BERTopic(language="english", verbose=True, umap_model=dim_model, hdbscan_model=cluster_model,
                           vectorizer_model=vectorizer)

    # Define a function to get words without scores
    def get_words(paragraph):
        topics, _ = topic_model.fit_transform([paragraph])
        words = topic_model.get_topic(0)  # considering topic 0 is the topic with highest relevance
        just_words = [word[0] for word in words]  # Extracting words without scores
        return just_words

    grouped_df = transcript_preprocess(vd_url)

    # Apply the function to each paragraph and store the result in a new column 'Keywords'
    grouped_df['Keywords'] = grouped_df['Paragraphs'].apply(get_words)
    print("Topic model [Completed]...")

    return grouped_df

###########################################################################
st.title("Topic search in lecture video and transcript generator")

video_id = st.text_input("Enter lecture video ID:")
if video_id:
    #start_time = "1m30s"  # Replace this with your desired start time  # roq8N_AqcIA
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    if video_url:
        try:
            # Fetch video details using pafy
            video = pafy.new(video_url)

            # Display the YouTube video
            st.video(video_url)

            # Display video details
            st.subheader("Video Details")
            st.write(f"Title: {video.title}")
            st.write(f"Author: {video.author}")
            st.write(f"Duration: {video.duration}")

            st.subheader("Topic wise lecture Transcript")
            # Streamlit input for transcribed text
            #st.write(generate_video_topic_transcription(video_url))
            struct_data = generate_video_topic_transcription(video_url)
            print(struct_data.head(10))

            col1, col2 = st.columns([2,3])
            for idx, row in struct_data.iterrows():
                # Display keywords as buttons with associated start timestamps in the second column
                with col1:
                    st.subheader(f"Topic-[Section {idx + 1}]")
                    keywords = row['Keywords']
                    timestamps = row['Start Timestamp']
                    print(timestamps)
                    timestamps_concat = "".join(timestamps)
                    timestamp_link = f"{video_url}&t={timestamps_concat}"
                    st.markdown(f'<a href="{timestamp_link}" target="_blank" style="padding: 5px; margin: 5px; border: 1px solid #ffafaf; border-radius: 5px; background-color: #ffc0cb; color: #ff0000;">{keywords}</a>', unsafe_allow_html=True)


                # Display paragraphs in the first column
                with col2:
                    st.subheader(f"Section {idx + 1}")
                    st.write(row['Paragraphs'])


        except Exception as e:
            st.write("Error fetching video information. Please enter a valid YouTube video URL.")


