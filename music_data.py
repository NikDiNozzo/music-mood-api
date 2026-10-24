"""Небольшой демонстрационный каталог музыки без внешних API и базы данных.

Продолжительность композиций указана приблизительно, для учебного проекта.
"""

TRACKS = [
    {"id": 1, "title": "Bohemian Rhapsody", "artist": "Queen", "genre": "rock", "mood": "energetic", "duration_seconds": 354},
    {"id": 2, "title": "Numb", "artist": "Linkin Park", "genre": "rock", "mood": "energetic", "duration_seconds": 187},
    {"id": 3, "title": "Yellow", "artist": "Coldplay", "genre": "rock", "mood": "calm", "duration_seconds": 269},
    {"id": 4, "title": "Get Lucky", "artist": "Daft Punk", "genre": "electronic", "mood": "upbeat", "duration_seconds": 369},
    {"id": 5, "title": "Blinding Lights", "artist": "The Weeknd", "genre": "pop", "mood": "upbeat", "duration_seconds": 200},
    {"id": 6, "title": "ocean eyes", "artist": "Billie Eilish", "genre": "pop", "mood": "calm", "duration_seconds": 200},
    {"id": 7, "title": "Time", "artist": "Hans Zimmer", "genre": "soundtrack", "mood": "focus", "duration_seconds": 275},
    {"id": 8, "title": "Nuvole Bianche", "artist": "Ludovico Einaudi", "genre": "classical", "mood": "focus", "duration_seconds": 357},
    {"id": 9, "title": "Anti-Hero", "artist": "Taylor Swift", "genre": "pop", "mood": "upbeat", "duration_seconds": 200},
    {"id": 10, "title": "Starlight", "artist": "Muse", "genre": "rock", "mood": "upbeat", "duration_seconds": 240},
    {"id": 11, "title": "Midnight City", "artist": "M83", "genre": "electronic", "mood": "energetic", "duration_seconds": 243},
    {"id": 12, "title": "Someone Like You", "artist": "Adele", "genre": "pop", "mood": "calm", "duration_seconds": 285},
]

# Дополнительные композиции: группировка по настроению и жанру помогает
# наполнять длинные плейлисты. Категории субъективны, длительности примерные.
# Никакие аудиофайлы или внешние сервисы не используются.
ADDITIONAL_TRACKS = {
    "calm": {
        "rock": [
            ("Wish You Were Here", "Pink Floyd", 334),
            ("The Scientist", "Coldplay", 309),
            ("Drive", "Incubus", 232),
            ("High and Dry", "Radiohead", 257),
            ("Landslide", "Fleetwood Mac", 199),
        ],
        "pop": [
            ("All of Me", "John Legend", 269),
            ("Lovely", "Billie Eilish & Khalid", 200),
            ("Stay With Me", "Sam Smith", 173),
            ("Let Her Go", "Passenger", 253),
            ("When We Were Young", "Adele", 290),
        ],
        "electronic": [
            ("A Walk", "Tycho", 317),
            ("Kerala", "Bonobo", 237),
            ("Sunset Lover", "Petit Biscuit", 238),
            ("Weightless", "Marconi Union", 485),
            ("Open Eye Signal", "Jon Hopkins", 467),
        ],
        "soundtrack": [
            ("One Summer's Day", "Joe Hisaishi", 186),
            ("Arrival of the Birds", "The Cinematic Orchestra", 157),
            ("Concerning Hobbits", "Howard Shore", 176),
            ("Married Life", "Michael Giacchino", 244),
            ("Merry-Go-Round of Life", "Joe Hisaishi", 311),
        ],
        "classical": [
            ("Clair de lune", "Claude Debussy", 302),
            ("Gymnopédie No. 1", "Erik Satie", 205),
            ("Moonlight Sonata: I", "Ludwig van Beethoven", 337),
            ("Nocturne Op. 9 No. 2", "Frédéric Chopin", 264),
            ("The Swan", "Camille Saint-Saëns", 195),
        ],
    },
    "upbeat": {
        "rock": [
            ("Don't Stop Me Now", "Queen", 209),
            ("Mr. Brightside", "The Killers", 222),
            ("Adventure of a Lifetime", "Coldplay", 263),
            ("Walking on Sunshine", "Katrina and the Waves", 238),
            ("Best Day of My Life", "American Authors", 194),
        ],
        "pop": [
            ("Happy", "Pharrell Williams", 233),
            ("Levitating", "Dua Lipa", 203),
            ("Shake It Off", "Taylor Swift", 219),
            ("Can't Stop the Feeling!", "Justin Timberlake", 236),
            ("Uptown Funk", "Mark Ronson ft. Bruno Mars", 270),
        ],
        "electronic": [
            ("One More Time", "Daft Punk", 320),
            ("Wake Me Up", "Avicii", 247),
            ("Rather Be", "Clean Bandit", 227),
            ("This Girl", "Kungs", 195),
            ("Firestone", "Kygo", 273),
        ],
        "soundtrack": [
            ("You've Got a Friend in Me", "Randy Newman", 124),
            ("The Avengers", "Alan Silvestri", 143),
            ("Test Drive", "John Powell", 156),
            ("The Incredits", "Michael Giacchino", 201),
            ("Friend Like Me", "Robin Williams", 146),
        ],
        "classical": [
            ("Eine kleine Nachtmusik: I", "Wolfgang A. Mozart", 350),
            ("Spring: I (Four Seasons)", "Antonio Vivaldi", 202),
            ("Rondo alla Turca", "Wolfgang A. Mozart", 207),
            ("Hungarian Dance No. 5", "Johannes Brahms", 161),
            ("The Blue Danube", "Johann Strauss II", 340),
        ],
    },
    "energetic": {
        "rock": [
            ("Seven Nation Army", "The White Stripes", 232),
            ("Smells Like Teen Spirit", "Nirvana", 301),
            ("Thunderstruck", "AC/DC", 292),
            ("Uprising", "Muse", 305),
            ("Eye of the Tiger", "Survivor", 246),
        ],
        "pop": [
            ("Physical", "Dua Lipa", 193),
            ("Bad Romance", "Lady Gaga", 294),
            ("Stronger", "Kelly Clarkson", 222),
            ("Run the World (Girls)", "Beyoncé", 236),
            ("Titanium", "David Guetta ft. Sia", 245),
        ],
        "electronic": [
            ("Levels", "Avicii", 199),
            ("Animals", "Martin Garrix", 303),
            ("Sandstorm", "Darude", 225),
            ("Ghosts 'n' Stuff", "deadmau5", 334),
            ("Scary Monsters and Nice Sprites", "Skrillex", 243),
        ],
        "soundtrack": [
            ("Duel of the Fates", "John Williams", 254),
            ("He's a Pirate", "Klaus Badelt", 94),
            ("The Battle", "Hans Zimmer", 610),
            ("Mombasa", "Hans Zimmer", 295),
            ("Portals", "Alan Silvestri", 202),
        ],
        "classical": [
            ("Summer: III (Four Seasons)", "Antonio Vivaldi", 157),
            ("Flight of the Bumblebee", "Nikolai Rimsky-Korsakov", 190),
            ("Symphony No. 5: I", "Ludwig van Beethoven", 425),
            ("In the Hall of the Mountain King", "Edvard Grieg", 174),
            ("Dance of the Knights", "Sergei Prokofiev", 338),
        ],
    },
    "focus": {
        "rock": [
            ("Intro", "The xx", 128),
            ("Your Hand in Mine", "Explosions in the Sky", 496),
            ("First Breath After Coma", "Explosions in the Sky", 573),
            ("A Gallant Gentleman", "We Lost the Sea", 387),
            ("Says", "Nils Frahm", 508),
        ],
        "pop": [
            ("Holocene", "Bon Iver", 336),
            ("Bloom", "The Paper Kites", 210),
            ("Cherry Wine (Live)", "Hozier", 240),
            ("Breathe Me", "Sia", 274),
            ("The Night We Met", "Lord Huron", 208),
        ],
        "electronic": [
            ("A Moment Apart", "ODESZA", 234),
            ("Cirrus", "Bonobo", 352),
            ("Awake", "Tycho", 283),
            ("Kusanagi", "ODESZA", 192),
            ("We Can Make the World Stop", "The Glitch Mob", 325),
        ],
        "soundtrack": [
            ("Cornfield Chase", "Hans Zimmer", 126),
            ("Experience", "Ludovico Einaudi", 315),
            ("The Breaking of the Fellowship", "Howard Shore", 441),
            ("Light of the Seven", "Ramin Djawadi", 586),
            ("The Ludlows", "James Horner", 325),
        ],
        "classical": [
            ("Comptine d'un autre été", "Yann Tiersen", 140),
            ("Arabesque No. 1", "Claude Debussy", 294),
            ("Prelude in C Major", "Johann S. Bach", 150),
            ("Spiegel im Spiegel", "Arvo Pärt", 480),
            ("Piano Sonata No. 16: I", "Wolfgang A. Mozart", 330),
        ],
    },
}

for mood, genres in ADDITIONAL_TRACKS.items():
    for genre, entries in genres.items():
        for title, artist, duration_seconds in entries:
            TRACKS.append(
                {
                    "id": len(TRACKS) + 1,
                    "title": title,
                    "artist": artist,
                    "genre": genre,
                    "mood": mood,
                    "duration_seconds": duration_seconds,
                }
            )
