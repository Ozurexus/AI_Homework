# to calculate the execution time of the program
from time import time
# to generate random numbers and shuffle population
from numpy.random import randint, shuffle
# to work with midi file
from mido import Message, MidiFile, MidiTrack
# to parse the midi file and find key of the original song
from music21.converter import parse


# calculate the mean note of each quarter of a bar and return a list of the mean notes
def mean(song: list) -> list:
    per_quarter = []
    per_second = []
    rest_time = 0
    counter = 0
    note = 0
    # go through the song to create a list of notes at each second
    for i in range(len(song)):
        for _ in range((song[i][1])):
            per_second.append(song[i][0])
    # go through the list of notes in each second to calculate mean note of the quarter
    for i in range(0, len(per_second)):
        if per_second[i] == 0:
            rest_time += 1
        counter += 1
        note += per_second[i]
        if counter == 384:
            if rest_time == 384:
                per_quarter.append(0)
            else:
                per_quarter.append((note/(384-rest_time))-12)
            rest_time = 0
            counter = 0
            note = 0
    if per_quarter[0] != 0:
        per_quarter[0] -= 12
    return per_quarter


# generate a scale from a note
def generate_scale(note: str, is_major: bool) -> list:
    notes_list = ["C", "C#", "D", "D#", "E",
                  "F", "F#", "G", "G#", "A", "A#", "B"]
    i = notes_list.index(note)
    if is_major:
        # major scale
        tmp = [i, i + 2, i + 4, i + 5, i + 7, i + 9, i + 11]
    else:
        # minor scale
        tmp = [i, i + 2, i + 3, i + 5, i + 7, i + 8, i + 10]
    scale = [notes_list[x % 12] for x in tmp]
    return scale


# calculate the fitness of an individual
def fitness_score(candidate: list, mean_notes: list, good_notes: list) -> float:
    notes_list = ["C", "C#", "D", "D#", "E", "F", "F#",
                  "G", "G#", "A", "A#", "B"]
    fitness = 0.0
    for i in range(len(candidate)):
        # 1. Presence of the chords among the good sounding notes
        chord = candidate[i]
        fitness_before = fitness
        for j in range(len(good_notes)):
            fitness += 10*(notes_list.index(str(good_notes[j % 7])) == (chord[0] % 12) and
                           notes_list.index(str(good_notes[(j + 2) % 7])) == (chord[1] % 12) and
                           notes_list.index(str(good_notes[(j + 4) % 7])) == (chord[2] % 12))
        if fitness == fitness_before:  # the chord doesn't exist
            fitness -= 50

        # 2. Check dissonance of chords by checking the difference
        #  between the notes of the mean and the individual
        for k in [abs(chord[x] % 12 - mean_notes[i]) for x in range(3)]:
            match k:
                case 0 | 7:
                    # perfect consonance
                    fitness += 10
                case 5:
                    # major consonance
                    fitness += 5
                case 2 | 10:
                    # minor consonance -> no change in fitness
                    pass
                case 3 | 4 | 8 | 9:
                    # major dissonance
                    fitness -= 5
                case 6:
                    # minor dissonance
                    fitness -= 10
                case 1 | 11:
                    # perfect dissonance
                    fitness -= 15

    # 3. Likeness to the original song's mean notes of each quarter
    for i in range(1, len(mean_notes)):
        chord = candidate[i]
        if mean_notes[i] > 0:
            flag = False
            if chord[0] == mean_notes[0]:
                fitness -= 10
            elif abs(chord[0]-mean_notes[i]) < 3:
                fitness += 3*(3 - abs(chord[0]-mean_notes[i]))
                flag = True
            if chord[1] == mean_notes[0]:
                fitness -= 10
            elif abs(chord[1]-mean_notes[i]) < 3:
                fitness += 3*(3 - abs(chord[1]-mean_notes[i]))
                flag = True
            if chord[2] == mean_notes[0]:
                fitness -= 10
            elif abs(chord[2]-mean_notes[i]) < 3:
                fitness += 3*(3 - abs(chord[2]-mean_notes[i]))
                flag = True
            if flag == False:
                fitness -= 30
        else:
            # if there is nothing playing in the song at this quarter
            # the accompaniment should be silent as well
            if chord[0] == -1 and chord[1] == -1 and chord[2] == -1:
                fitness += 10
            else:
                fitness -= 1000
    return fitness


# generate a random chord
def random_chord() -> list:
    # rest is chosen so often, because I wanted to improve fitness for
    # songs, where there is a lot of silence (input3 for example)
    i = randint(0, 100)
    if i < 10:
        return [-1, -1, -1]  # rest
    # choose a random chord type
    j = randint(0, 9)
    match j:
        case 0:
            # major triad
            triad = [i, i + 4, i + 7]
        case 1:
            # minor triad
            triad = [i, i + 3, i + 7]
        case 2:
            # diminished chord
            triad = [i, i + 3, i + 6]
        case 3:
            # suspended second chord
            triad = [i, i + 2, i + 7]
        case 4:
            # suspended fourth chord
            triad = [i, i + 5, i + 7]
        case 5:
            # first inversion major triad
            triad = [i + 12, i + 4, i + 7]
        case 6:
            # first inversion minor triad
            triad = [i + 12, i + 3, i + 7]
        case 7:
            # second inversion major triad
            triad = [i + 12, i + 16, i + 7]
        case 8:
            # second inversion minor triad
            triad = [i + 12, i + 15, i + 7]
    return triad


# evolution algorithms function that performs selection, crossover and mutation
def evolution(population: list, mean_notes: list, chords: list) -> list:
    sorted_populatiom = []
    # selection of best 50% of the population
    for i in range(len(population)):
        # calculate the fitness of each individual and add it to the list
        sorted_populatiom.append((population[i], fitness_score(
            population[i], mean_notes, chords)))
    # sort by fitness score
    sorted_populatiom.sort(key=lambda x: x[1], reverse=True)
    # clear the population to add only the best 50% of the population
    population = []
    for i in range(int(len(sorted_populatiom) * 0.5)):
        population.append(sorted_populatiom[i][0])

    # here starts crossover of the 50% of the remaining population
    # shuffle the population to get random pairs of parents
    # each pair of parents will produce 2 children
    shuffle(population)
    for i in range(0, len(population), 2):
        if i + 1 < len(population):
            parent1 = population[i]
            parent2 = population[i + 1]
            child1 = []
            child2 = []
            for j in range(len(parent1)):
                # randomly choose a parent
                if randint(0, 2) == 0:
                    child1.append(parent1[j])
                    child2.append(parent2[j])
                else:
                    child1.append(parent2[j])
                    child2.append(parent1[j])

            # here starts mutation of the children
            if len(child1) == len(child2):
                for j in range(len(child1)):
                    if randint(0, 10) == 1:
                        # generate a random chords for children in 10% of the cases
                        child1[j] = random_chord()
                    if randint(0, 10) == 1:
                        child2[j] = random_chord()
            # add children to the population after mutation
            population.extend([child1, child2])
    return population


# construct output midi file
def create_output(input_name: MidiFile, best: list, output_name: str) -> MidiFile:
    track = MidiTrack()
    output = MidiFile()
    # append the first MetaMessage
    track.append(input_name.tracks[1][0])
    rest = 0
    # append the chords to the track
    for x in best:
        if x[0] == -1 and x[1] == -1 and x[2] == -1:
            rest += 384
        else:
            for i in range(6):
                if i < 3:
                    if i == 0:
                        t = rest
                    else:
                        t = 0
                    v = 55
                    mode = 'note_on'
                else:
                    if i == 5:
                        t = 384
                    v = 0
                    mode = 'note_off'
                track.append(Message(mode, note=x[i % 3], velocity=v, time=t))
            rest = 0
    # append the last MetaMessage
    track.append(input_name.tracks[1][-1])
    # append tracks of the input file and the new track
    for i in range(len(input_name.tracks)):
        output.tracks.append(input_name.tracks[i])
    output.tracks.append(track)
    # set the same ticks per beat as in the original
    output.ticks_per_beat = input_name.ticks_per_beat
    # save the file as a midifile
    output.save(output_name)
    return output


# create accompaniment for the input midi file
def create_accompaniment(input_name: str, output_name: str, gen_number: int, size: int):
    # start the time measurement
    start = time()
    notes = ["C", "C#", "D", "D#", "E",
                  "F", "F#", "G", "G#", "A", "A#", "B"]
    # parse input using music21 library
    input_song = parse(input_name)
    # read the input file
    input_name = MidiFile(input_name)
    keys = []  # list of notes and their time
    population = []  # list of individuals
    # get the notes and their time
    for i in range(len(input_name.tracks)):
        for j in range(len(input_name.tracks[i])):
            if input_name.tracks[i][j].time != 0:
                if input_name.tracks[i][j].type == 'note_on':
                    keys.append([0, input_name.tracks[i][j].time])
                else:
                    keys.append([input_name.tracks[i][j].note,
                                input_name.tracks[i][j].time])
    # get the key of the input song
    input_key = input_song.analyze('key')
    # get the mean note of each quarter of the input song
    mean_note = mean(keys)
    string_input_key = str(input_key).capitalize()
    print("Key: " + string_input_key)
    scale = [[x, generate_scale(x, input_key.type == 'major')]for x in notes]
    for message in scale:
        if message[0] == string_input_key.split()[0]:
            # list of notes that we can compose good sounding chords from
            chords = message[1]
            break
        # create the initial population
    for _ in range(size):
        j = []
        for _ in range(len(mean_note)):
            # generate a random chord and append it to the individual
            j.append(random_chord())
        # append the individual to the population
        population.append(j)
    # run the genetic algorithms for the specified number of generations
    for i in range(gen_number):
        population = evolution(population, mean_note, chords)
        if i % 20 == 0 or i == gen_number - 1:
            maximum = -10000000000
            for j in population:
                fit = fitness_score(j, mean_note, chords)
                if fit > maximum:
                    maximum = fit
            if i == gen_number-1:
                print("Last Generation", "Maximum",
                      maximum)
            else:
                print("Generation", i, "Maximum", maximum)
      # fitness score of the best individual
    maximum = -10000000000
    for melody in population:
        fit = fitness_score(melody, mean_note, chords)
        if fit > maximum:
            maximum = fit
            best = melody
    if maximum > -1000:
        create_output(input_name, best, output_name)
        print("\nDone, please check", output_name, "for the result.")
    else:
        print("\nNo good result was found.")
    print("Time taken:", round(time() - start, 2), "seconds.")
    return None


# get the key of the song to create a name for the output file
def output_name(input_name: str, i: int) -> str:
    input_song = parse(input_name)
    input_key = input_song.analyze('key')
    if input_key.type == 'minor':
        key = str(input_key).capitalize().split()[0] + 'm'
    else:
        key = str(input_key).capitalize().split()[0]
    return str("MaximPiniaginOutput" + str(i)+"-"+key+".mid")


def main():
    print("Do you want to manually input the parameters or use the default ones?")
    print("Type 1 for default, 2 for manual.")
    print("1. Default: 500 generations, 1000 individuals forInput1.mid, Input2.mid")
    print("and 1000 generations for Input3.mid.")
    print("2. Manual")
    choice = str(input())
    if choice == "1":
        i = 1
        create_accompaniment("Input1.mid", output_name(
            "Input1.mid", i), 500, 1000)
        i += 1
        create_accompaniment("Input2.mid", output_name(
            "Input2.mid", i), 500, 1000)
        i += 1
        create_accompaniment("Input3.mid", output_name(
            "Input3.mid", i), 1000, 1000)
    elif choice == "2":
        print("Enter the number of tracks:")
        tracks = int(input())
        print("Enter the number of generations:")
        number = int(input())
        print("Enter the size of the population:")
        size = int(input())
        for j in range(tracks):
            print("Enter the name of the ", j+1, " input file:")
            input_file = input()
            print("Enter the name of the ", j+1, " output file:")
            output_file = input()
        for _ in range(tracks):
            print(create_accompaniment(input_file, output_file, number, size))
        return None
    else:
        print("Error! Invalid input, please try again.")
        return None


main()
