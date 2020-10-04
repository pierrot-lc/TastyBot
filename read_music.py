import os
import pandas as pd

def read_dir(path, album, data):
    for f in os.listdir(path):
        if os.path.isfile(os.path.join(path, f)) and f.endswith('.wav'):
            song_name = f.split('.wav')[0]
            if ' - ' in song_name:
                song_name = song_name.split(' - ')
                song_id, song_name = int(song_name[0]), song_name[1]
            else:
                song_id = None

            data['artist'].append('Tastycool')
            data['album'].append(album)
            data['song_name'].append(song_name)
            data['song_id'].append(song_id)
            data['path'].append(os.path.join(path, f))

if __name__ == '__main__':
    data = {'artist': [],
            'album': [],
            'song_name': [],
            'song_id': [],
            'path': []}
    base_path = os.path.join('.', 'songs')
    read_dir(base_path, 'EP', data)
    for f in os.listdir(base_path):
        if not os.path.isfile(os.path.join(base_path, f)):
            read_dir(os.path.join(base_path, f), f, data)

    df = pd.DataFrame(data=data)
    df.to_csv('songs.csv', index=False)
