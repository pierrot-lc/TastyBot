"""
Read songs infos from a specified directory.
Creates a DataFrame into a csv file.
"""
import os
import pandas as pd


def read_dir(path, album, data):
    for f in os.listdir(path):
        if os.path.isfile(os.path.join(path, f)) and f.endswith('.mp3'):
            song_info = f.split('.mp3')[0]
            song_info = song_info.split('0')[1]
            song_info = song_info.split(' ')
            song_id, song_name = int(song_info[0]), song_info[1:]
            song_name = ' '.join(song_name)

            data['artist'].append('Tastycool')
            data['album'].append(album)
            data['song_name'].append(song_name)
            data['song_id'].append(song_id)
            data['path'].append(os.path.join(path, f))


def create_csv(songs_path, csv_path):
    """
    Read all songs from the specified songs_path.

    Write the data to a csv file.
    """
    data = {'artist': [],
            'album': [],
            'song_name': [],
            'song_id': [],
            'path': []}
    read_dir(songs_path, 'EP', data)
    for f in os.listdir(songs_path):
        if not os.path.isfile(os.path.join(songs_path, f)):
            read_dir(os.path.join(songs_path, f), f, data)

    df = pd.DataFrame(data=data)
    df.to_csv(csv_path, index=False)


if __name__ == '__main__':
    create_csv('songs', 'songs.csv')
