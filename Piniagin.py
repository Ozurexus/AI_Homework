import time  # to calculate the execution time of the program
import numpy  # for random number generation
from mido import Message, MidiFile, MidiTrack  # to work with midi file
from music21.converter import parse  # to parse the midi file
NotesList = ["C", "C#", "D", "D#", "E", "F", "F#",
             "G", "G#", "A", "A#", "B"]  # list of all notes


# generate a major scale from a note
def generate_major_scale(note: str) -> list:
    major_scale = []
    for i in range(len(NotesList)):
        if note == NotesList[i]:
            major_number = [i, i + 2, i + 4, i + 5, i + 7, i + 9, i + 11]
            major_scale = [NotesList[i % 12] for i in major_number]
            break
    return major_scale


# generate a minor scale from a note
def generate_minor_scale(note: str) -> list:
    minor_scale = []
    for i in range(len(NotesList)):
        if note == NotesList[i]:
            minor_number = [i, i + 2, i + 3, i + 5, i + 7, i + 8, i + 10]
            minor_scale = [NotesList[i % 12] for i in minor_number]
            break
    return minor_scale


# generate a chord from a midi number
def generate_chord(midi: int) -> list:
    chord = []
    i = numpy.random.randint(0, 9)  # choose a random chord type
    match i:
        case 0:
            chord = [midi, midi + 4, midi + 7]  # major triad
        case 1:
            chord = [midi, midi + 3, midi + 7]  # minor triad
        case 2:
            chord = [midi, midi + 3, midi + 6]  # diminished chord
        case 3:
            chord = [midi, midi + 2, midi + 7]  # suspended second chord
        case 4:
            chord = [midi, midi + 5, midi + 7]  # suspended fourth chord
        case 5:
            chord = [-1, -1, -1]  # rest
        case 6:
            # first inversion major triad
            chord = [midi + 12, midi + 4, midi + 7]
        case 7:
            # first inversion minor triad
            chord = [midi + 12, midi + 3, midi + 7]
        case 8:
            # second inversion major triad
            chord = [midi + 12, midi + 16, midi + 7]
        case 9:
            # second inversion minor triad
            chord = [midi + 12, midi + 15, midi + 7]
    return chord


# convert note to midi number
def convert(note: int) -> int:
    # let's assume the note C is 0
    for i in range(len(NotesList)):  # go through the notes in search of the needed note
        if note == NotesList[i]:
            note_number = i
            return note_number
    return -1


# calculate the average note of each quarter of a bar and return a list of the average notes
def average_note(song: list) -> list:
    arr = []
    averages = []
    total_time = 0
    for i in range(len(song)):
        chord = song[i]
        total_time += chord[1]  # add the time of the note to the total time
        avg = 0.0
        quarter_time = 0.0
        if chord[0] != 0:  # if the note is not a rest
            if total_time > 384:  # if the total time is more than quarter time
                new_time = chord[1] - total_time + 384
                averages.append([chord[0], new_time])
                # add the average note of the quarter time to the list
                for i in range(len(averages)):
                    avg += averages[i][0] * averages[i][1]
                    quarter_time += averages[i][1]
                if quarter_time != 0:
                    avg /= quarter_time
                else:
                    avg = 0
                arr.append(avg)
                total_time = chord[1] - (averages[-1][1])
                while total_time >= 384:
                    arr.append(float(chord[0]))
                    total_time -= 384
                averages = []
                if total_time != 0:
                    averages.append([chord[0], total_time])
            else:
                averages.append(chord)
                if total_time == 384:
                    for i in range(len(averages)):
                        avg += averages[i][0] * averages[i][1]  # note*time
                        quarter_time += averages[i][1]
                    if quarter_time != 0:
                        avg /= quarter_time
                    else:
                        avg = 0
                    arr.append(avg)
                    averages = []
                    total_time = 0
    # subtract 24 to get the note in the range of 0-11
    arr = [int(i - 24) for i in arr]
    return arr


# Calculate the fitness of an individual
# Fitness will depend on three criterias:
    # 1. similarity to the original melody's average note
    # 2. existence of the chord in the possible chords
    # 3. dissonance of the chords compared to the original melody
def fitness_score(individual: list, avg_note: list, chords: list) -> float:
    fitness = 0.0
    # 1. Similarity to original melody's average note of the 384
    for i in range(len(avg_note)):
        chord = individual[i]
        if avg_note[i] > 0:
            diff = max(10.0 - abs(float(avg_note[i]) - chord[0]), 0.0) * 0.5 + max(10.0 - abs(float(
                avg_note[i]) - chord[1]), 0.0) + max(10.0 - abs(float(avg_note[i]) - chord[2]), 0.0) * 0.5
            fitness += diff
    for i in range(len(individual)):
        # 2. Existence and validity of chords
        chord = individual[i]
        ton_diff = abs(chord[0] % 12 - avg_note[i])
        med_diff = abs(chord[1] % 12 - avg_note[i])
        dom_diff = abs(chord[2] % 12 - avg_note[i])
        exists = False
        for j in range(len(chords)):  # check if the chord exists
            if convert(chords[j % 7]) == (chord[0] % 12) and \
               convert(chords[(j + 2) % 7]) == (chord[1] % 12) and \
               convert(chords[(j + 4) % 7]) == (chord[2] % 12):
                fitness += 10
                exists = True
                break
        if not exists:
            fitness -= 50

        # 3. Check dissonance of chords by checking the difference between the notes of the original and the individual
        if avg_note[i] > 0:
            ton_diff = abs(chord[0] % 12 - avg_note[i])
            med_diff = abs(chord[1] % 12 - avg_note[i])
            dom_diff = abs(chord[2] % 12 - avg_note[i])
            for k in [ton_diff, med_diff, dom_diff]:
                match k:
                    case 0 | 7:  # perfect consonance
                        fitness += 10
                    case 5:  # major consonance
                        fitness += 5
                    case 2 | 10:  # minor consonance
                        pass  # no change
                    case 3 | 4 | 8 | 9:  # major dissonance
                        fitness -= 5
                    case 6:  # minor dissonance
                        fitness -= 10
                    case 1 | 11:  # perfect dissonance
                        fitness -= 15
    return fitness


# evolution algorithms function that performs selection, crossover and mutation
def evolution(population: list, avg_note: list, chords: list) -> list:
    sorted = []
    for i in range(len(population)):  # selection of best 50% of the population
        sorted.append((population[i], fitness_score(
            population[i], avg_note, chords)))  # calculate the fitness of each individual and add it to the list
    sorted.sort(key=lambda x: x[1], reverse=True)  # sort by fitness score
    population = []  # clear the population to add only the best 50% of the population
    for i in range(int(len(sorted) * 0.5)):
        population.append(sorted[i][0])

    # here starts crossover of the 50% of the population
    # shuffle the population to get random pairs of parents
    numpy.random.shuffle(population)
    for i in range(0, len(population), 2):
        if i + 1 < len(population):
            parent1 = population[i]
            parent2 = population[i + 1]
            child1 = []
            child2 = []
            for j in range(len(parent1)):
                if numpy.random.randint(0, 2) == 0:  # randomly choose a parent
                    child1.append(parent1[j])
                    child2.append(parent2[j])
                else:
                    child1.append(parent2[j])
                    child2.append(parent1[j])

            # here starts mutation of the children
            if len(child1) == len(child2):
                for i in range(len(child1)):
                    if numpy.random.randint(0, 10) == 0:
                        # generate a random chords for children in 10% of the cases
                        child1[i] = generate_chord(
                            numpy.random.randint(0, 100))
                    if numpy.random.randint(0, 10) == 0:
                        child2[i] = generate_chord(
                            numpy.random.randint(0, 100))
            # add children to the population after mutation
            population.extend([child1, child2])
    return population


def create_output(input: MidiFile, individual: list, output_file_name: str) -> MidiFile:
    track = MidiTrack()
    output = MidiFile()  # create a new midifile
    # append tracks of the input file
    output.tracks.extend([input.tracks[0], input.tracks[1]])
    track.append(input.tracks[1][0])
    rest = 0
    for x in individual:  # append the chords to the track
        if x[0] == 0:
            rest += 384
        else:
            track.extend([Message('note_on',  note=x[0], time=rest, velocity=45),
                          Message('note_on', note=x[1], velocity=45),
                          Message('note_on', note=x[2], velocity=45),
                          Message('note_off', note=x[0], time=384, velocity=0),
                          Message('note_off', note=x[1], velocity=0),
                          Message('note_off', note=x[2], velocity=0)])
            # reset the rest time
            rest = 0
    # append the last message
    track.append(input.tracks[1][-1])
    # append the generated track to the output file
    output.tracks.append(track)
    # set the same ticks per beat as in the original
    output.ticks_per_beat = input.ticks_per_beat
    output.save(output_file_name)  # save the file as a midifile
    return output


def create_accompaniment(input_file_name: str, output_file_name: str, gen_number: int, size_of_population: int):
    # generate major scales
    major_list = [[x, generate_major_scale(x)] for x in NotesList]
    # generate minor scales
    minor_list = [[x, generate_minor_scale(x)] for x in NotesList]
    start = time.time()  # start the time measurement
    input = MidiFile(input_file_name)  # read the input file
    # print(input)
    input_song = parse(input_file_name)  # parse input using music21 library
    keys = []  # list of notes and their time
    chords = []  # list of notes that we can compose valid chords from
    population = []  # list of individuals
    for track in input.tracks:  # get the notes and their time
        for message in track:
            if message.time != 0:
                if message.type == "note_on":  # if the note is pressed
                    keys.append([0, message.time])
                elif message.type == "note_off":  # if the note is released
                    keys.append([message.note, message.time])
    # get the average note of the input song
    avg_note = average_note(keys)
    print("Average note: ", avg_note)
    print("Average note: ", avg_note[0], " ",
          avg_note[1], " ", avg_note[2], " ", avg_note[3])
    input_key = input_song.analyze('key')  # get the key of the input song
    print("Input key: " + str(input_key).capitalize())
    if input_key.type.lower() == 'minor':
        for message in minor_list:
            if message[0] == str(input_key).capitalize().split()[0]:
                chords = message[1]
                break
    else:
        for message in major_list:
            if message[0] == str(input_key).capitalize().split()[0]:
                chords = message[1]
                break
    for _ in range(size_of_population):  # generate the initial population
        song = []  # list of chords
        for _ in range(len(avg_note)):
            # generate a random chord and append it to the individual
            song.append(generate_chord(numpy.random.randint(0, 100)))
        # append the individual to the population
        population.append(song)
    # run the genetic algorithms for the specified number of generations
    for i in range(gen_number):
        population = evolution(population, avg_note, chords)
        if i % 20 == 0 or i == gen_number - 1:
            minimum = 100000000.0
            maximum = 0.0
            for song in population:
                fit = fitness_score(song, avg_note, chords)
                maximum = max(maximum, fit)
                minimum = min(minimum, fit)
            if i == gen_number-1:
                print("Last Generation", "Maximum",
                      maximum, "Minimum", minimum)
            else:
                print("Generation", i, "Maximum", maximum, "Minimum", minimum)
    maximum = 0.0  # fitness score of the best individual
    for song in population:
        fit = fitness_score(song, avg_note, chords)
        if fit > maximum:
            maximum = fit
            best = song
    create_output(input, best, output_file_name)
    print("\nDone, please check", output_file_name, "for the result.")
    print("Time taken:", round(time.time() - start, 2), "seconds")
    return None


# print("Do you want to manually input the parameters or use the default ones? Type 1 for default, 2 for manual.")
# print("1. Default: 300 generations, 1000 individuals and 3 tracks: Input1.mid, Input2.mid and Input3.mid.")
# print("2. Manual")
choice = "1"  # TODO input()
if choice == "1":
    create_accompaniment("Input1.mid", "Output1.mid", 300, 1000)
    # create_accompaniment("Input2.mid", "Output2.mid", 300, 1000)
    # create_accompaniment("Input3.mid", "Output3.mid", 300, 1000)
    #create_accompaniment("Input5.mid", "Output5.mid", 300, 1000)
elif choice == "2":
    print("Enter the number of tracks:")
    tracks = int(input())
    print("Enter the number of generations:")
    number = int(input())
    print("Enter the size of the population:")
    size = int(input())
    for i in range(tracks):
        print("Enter the name of the ", i+1, " input file:")
        input_file = input()
        print("Enter the name of the ", i+1, " output file:")
        output_file = input()
    for i in range(tracks):
        create_accompaniment(input_file, output_file, number, size)
    exit()
else:
    print("Error! Invalid input, please try again.")
    exit()
