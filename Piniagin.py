import time  # to calculate the execution time of the program
import numpy  # to generate random numbers
from mido import Message, MidiFile, MidiTrack  # to work with midi file
from music21.converter import parse  # to parse the midi file


# generate a scale from a note
def generate_scale(note: str, is_major: bool) -> list:
    notes_list = ["C", "C#", "D", "D#", "E",
                  "F", "F#", "G", "G#", "A", "A#", "B"]
    for i in range(len(notes_list)):
        if note == notes_list[i]:
            if is_major:
                number = [i, i + 2, i + 4, i + 5, i + 7, i + 9, i + 11]
            else:
                number = [i, i + 2, i + 3, i + 5, i + 7, i + 8, i + 10]
            scale = [notes_list[j % 12] for j in number]
            break
    return scale


# generate a chord from a midi number
def generate_chord(midi: int) -> list:
    chord = []
    # choose a random chord type
    i = numpy.random.randint(0, 9)
    match i:
        case 0:
            # major triad
            chord = [midi, midi + 4, midi + 7]
        case 1:
            # minor triad
            chord = [midi, midi + 3, midi + 7]
        case 2:
            # diminished chord
            chord = [midi, midi + 3, midi + 6]
        case 3:
            # suspended second chord
            chord = [midi, midi + 2, midi + 7]
        case 4:
            # suspended fourth chord
            chord = [midi, midi + 5, midi + 7]
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
def convert(note: str) -> int:
    notes_list = ["C", "C#", "D", "D#", "E", "F", "F#",
                  "G", "G#", "A", "A#", "B"]
    # let's assume the note C is 0
    # go through the notes list in search of the needed note
    for i in range(len(notes_list)):
        if note == notes_list[i]:
            return i
    return -1


# calculate the average note of each quarter of a bar and return a list of the average notes
def average(song: list) -> list:
    per_quarter = []
    per_second = []
    rest_time = 0
    counter = 0
    note = 0
    # go through the song to create a list of notes at each second
    for i in range(len(song)):
        for _ in range((song[i][1])):
            per_second.append(song[i][0])
    # go through the list of notes in each second to calculate average note of the quarter
    for i in range(0, len(per_second)):
        if per_second[i] == 0:
            rest_time += 1
        counter += 1
        note += per_second[i]
        if counter == 384:
            if rest_time == 384:
                per_quarter.append(0)
            else:
                per_quarter.append((note/(384-rest_time))-24)
            rest_time = 0
            counter = 0
            note = 0
    return per_quarter


# Calculate the fitness of an individual
# Fitness will depend on three criteria:
    # 1. similarity to the original melody's average note
    # 2. existence of the chord in the possible chords
    # 3. dissonance of the chords compared to the original melody
def fitness_score(individual: list, avg: list, chords: list) -> float:
    fitness = 0.0
    # 1. Similarity to original's average note of the quarter
    for i in range(len(avg)):
        chord = individual[i]
        if avg[i] >= 0:
            if abs(avg[i] - chord[0]) < 10:
                fitness += (5 - 0.5*abs(avg[i] - chord[0]))
            if abs(avg[i] - chord[1]) < 10:
                fitness += (5 - 0.5*abs(avg[i] - chord[1]))
            if abs(avg[i] - chord[2]) < 10:
                fitness += (5 - 0.5*abs(avg[i] - chord[2]))
    for i in range(len(individual)):
        # 2. Existence  of chords
        chord = individual[i]
        fitness_before = fitness
        for j in range(len(chords)):
            fitness += 10*(convert(chords[j % 7]) == (chord[0] % 12) and
                           convert(chords[(j + 2) % 7]) == (chord[1] % 12) and
                           convert(chords[(j + 4) % 7]) == (chord[2] % 12))
        if fitness == fitness_before:  # the chord doesn't exist
            fitness -= 50

        # 3. Check dissonance of chords by checking the difference between the notes of the original and the individual
        if avg[i] > 0:
            for k in [abs(chord[x] % 12 - avg[i]) for x in range(3)]:
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
    return fitness


# evolution algorithms function that performs selection, crossover and mutation
def evolution(population: list, avg_note: list, chords: list) -> list:
    sorted_populatiom = []
    # selection of best 50% of the population
    for i in range(len(population)):
        # calculate the fitness of each individual and add it to the list
        sorted_populatiom.append((population[i], fitness_score(
            population[i], avg_note, chords)))
    # sort by fitness score
    sorted_populatiom.sort(key=lambda x: x[1], reverse=True)
    # clear the population to add only the best 50% of the population
    population = []
    for i in range(int(len(sorted_populatiom) * 0.5)):
        population.append(sorted_populatiom[i][0])

    # here starts crossover of the 50% of the remaining population
    # shuffle the population to get random pairs of parents
    # each pair of parents will produce 2 children
    numpy.random.shuffle(population)
    for i in range(0, len(population), 2):
        if i + 1 < len(population):
            parent1 = population[i]
            parent2 = population[i + 1]
            child1 = []
            child2 = []
            for j in range(len(parent1)):
                # randomly choose a parent
                if numpy.random.randint(0, 2) == 0:
                    child1.append(parent1[j])
                    child2.append(parent2[j])
                else:
                    child1.append(parent2[j])
                    child2.append(parent1[j])

            # here starts mutation of the children
            if len(child1) == len(child2):
                for j in range(len(child1)):
                    if numpy.random.randint(0, 10) == 0:
                        # generate a random chords for children in 10% of the cases
                        child1[j] = generate_chord(
                            numpy.random.randint(0, 100))
                    if numpy.random.randint(0, 10) == 0:
                        child2[j] = generate_chord(
                            numpy.random.randint(0, 100))
            # add children to the population after mutation
            population.extend([child1, child2])
    return population


def create_output(input_name: MidiFile, individual: list, output_name: str) -> MidiFile:
    track = MidiTrack()
    output = MidiFile()
    track.append(input_name.tracks[1][0])
    rest = 0
    on = 'note_on'
    off = 'note_off'
    # append the chords to the track
    for x in individual:
        if x[0] == 0:
            rest += 384
        else:
            track.extend([Message(on,  note=x[0], time=rest, velocity=50),
                          Message(on, note=x[1], velocity=50),
                          Message(on, note=x[2], velocity=50),
                          Message(off, note=x[0], time=384, velocity=0),
                          Message(off, note=x[1], velocity=0),
                          Message(off, note=x[2], velocity=0)])
            # reset the rest time
            rest = 0
    # append the last message
    track.append(input_name.tracks[1][-1])
    # append tracks of the input file and the new track
    output.tracks.extend([input_name.tracks[0], input_name.tracks[1], track])
    # set the same ticks per beat as in the original
    output.ticks_per_beat = input_name.ticks_per_beat
    # save the file as a midifile
    output.save(output_name)
    return output


def create_accompaniment(input_name: str, output_name: str, gen_number: int, size: int):
    # start the time measurement
    start = time.time()
    notes = ["C", "C#", "D", "D#", "E",
                  "F", "F#", "G", "G#", "A", "A#", "B"]
    # read the input file
    input_file = MidiFile(input_name)
    # parse input using music21 library
    input_song = parse(input_name)
    keys = []  # list of notes and their time
    population = []  # list of individuals
    # get the notes and their time
    for track in input_file.tracks:
        for message in track:
            if message.time != 0:
                # if the note is pressed
                if message.type == "note_on":
                    keys.append([0, message.time])
                    # if the note is released
                elif message.type == "note_off":
                    keys.append([message.note, message.time])
    # get the average note of each quarter of the input song
    avg_note = average(keys)
    # get the key of the input song
    input_key = input_song.analyze('key')
    print("Key: " + str(input_key).capitalize())
    scale = [[x, generate_scale(x, input_key.type == 'major')]for x in notes]
    for message in scale:
        if message[0] == str(input_key).capitalize().split()[0]:
            # list of notes that we can compose valid chords from
            chords = message[1]
            break
        # create the initial population
    for _ in range(size):
        individual = []
        for _ in range(len(avg_note)):
            # generate a random chord and append it to the individual
            individual.append(generate_chord(numpy.random.randint(0, 100)))
        # append the individual to the population
        population.append(individual)
    # run the genetic algorithms for the specified number of generations
    for i in range(gen_number):
        population = evolution(population, avg_note, chords)
        if i % 20 == 0 or i == gen_number - 1:
            minimum = 100000000.0
            maximum = 0.0
            for individual in population:
                fit = fitness_score(individual, avg_note, chords)
                maximum = max(maximum, fit)
                minimum = min(minimum, fit)
            if i == gen_number-1:
                print("Last Generation", "Maximum",
                      maximum, "Minimum", minimum)
            else:
                print("Generation", i, "Maximum", maximum, "Minimum", minimum)
      # fitness score of the best individual
    maximum = 0.0
    for melody in population:
        fit = fitness_score(melody, avg_note, chords)
        if fit > maximum:
            maximum = fit
            best = melody
    create_output(input_file, best, output_name)
    print("\nDone, please check", output_name, "for the result.")
    print("Time taken:", round(time.time() - start, 2), "seconds.")
    return None


# print("Do you want to manually input the parameters or use the default ones? Type 1 for default, 2 for manual.")
# print("1. Default: 300 generations, 1000 individuals and 3 tracks: Input1.mid, Input2.mid and Input3.mid.")
# print("2. Manual")
choice = "1"  # TODO input()
if choice == "1":
    create_accompaniment("Input1.mid", "Output1.mid", 300, 1000)
    # create_accompaniment("Input2.mid", "Output2.mid", 300, 1000)
    # create_accompaniment("Input3.mid", "Output3.mid", 300, 1000)
    # create_accompaniment("Input5.mid", "Output5.mid", 300, 1000)
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
