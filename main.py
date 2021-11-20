import argparse
import sys
from sys import exit
from copy import deepcopy

def load_file(f):
    """loads the level file f and returns it as two dimensional array;
    ignores empty lines"""
    with open(f, "r") as fp:
        # only read nonempty lines
        s = [ list(l.replace("\n", "")) for l in fp if l and not l.startswith("#") ]
        s = update_lasers(s)
        return s


def to_str(s):
    """returns the level state s as string"""
    return "\n".join([ "".join(l) for l in s ])


def print_state(s):
    """print the level state s to standard output"""
    print(to_str(s))


def find_pos(s, x):
    """returns the positions at which character x is present in the level state s;
    positions are encoded as tuples of (row, col)"""
    return [ (i, j) for i, l in enumerate(s) for j, c in enumerate(l) if c == x ]


def at_pos(s, i, j):
    """get the character at row i, col j in level state s"""
    return s[i][j]


def set_at_pos(s, i, j, c):
    """set the character at row i, col j in level state s to c"""
    s[i][j] = c
    return s


def bounds(s):
    """returns a tuple of (height, width) of the level state;
    assumes all rows have the same length so it just checks the first"""
    return len(s), len(s[0])


def next_pos(row, col, dir):
    """returns the adjacent position to row, col in direction dir;
    dir is encoded as char h => left, j => down, k => up, l => right;
    does not perform bound checks (does not know the level state)"""
    if dir == "h":
        return row, col-1
    elif dir == "l":
        return row, col+1
    elif dir == "k":
        return row-1, col
    elif dir == "j":
        return row+1, col


def in_bounds(height, width, row, col):
    """returns whether the position (row, col) is within the bounds of (height, width);
    use this in conjunction with next_pos"""
    return row >= 0 and col >= 0 and row < height and col < width


_victory = 0
_invalid = 1
_unfinished = 2
_defeated = 3
_valid_chars = "G@YFMm_. xoWwv^<>|+-"


def validate_state(s):
    """returns the validity of the game state using the above exit codes;
    unequal line length => invalid
    invalid character => invalid
    no finish flag F => invalid
    no ram [G@Y] => invalid
    victorious ram @ => victory
    defeated ram Y => defeat
    default => unfinished"""
    length = len(s[0])
    n = next(( (i, len(l)) for i, l in enumerate(s) if len(l) != length ), None)
    if n:
        i, l = n
        eprint(f"len(line {i}) = {l} != len(line 0) = {length}")
        eprint("all lines must have the same length")
        return _invalid

    invalid = False
    goat_count = 0
    victory = False
    defeated = False
    finish_count = 0
    for i, l in enumerate(s):
        for j, c in enumerate(l):
            if c not in _valid_chars:
                eprint(f"invalid char {c} at row {i} col {j}")
                eprint(f"all chars must be in {str(_valid_chars)}")
                invalid = True
            if c in "G":
                goat_count += 1
            elif c in "Y":
                goat_count += 1
                defeated = True
            elif c in "@":
                goat_count += 1
                victory = True
            elif c in "F":
                finish_count += 1
    if invalid:
        return _invalid
    if not finish_count:
        eprint("found no F in file")
        eprint("file must contain at least 1")
        return _invalid
    if goat_count != 1:
        eprint(f"file contains {goat_count} of [G, @, Y]")
        eprint("file must contain exactly one of these")
        return _invalid
    if victory:
        return _victory
    if defeated:
        return _defeated
    return _unfinished


def determine_new_state(s):
    for i, l in enumerate(s):
        for j, c in enumerate(l):
            if c in "Y":
                return _defeated
            elif c in "@":
                return _victory

    return _unfinished


def update_lasers(s):
    # clear all beams
    for c in "|-+":
        for row, col in find_pos(s, c):
            set_at_pos(s, row, col, " ")

    lasers = []
    height, width = bounds(s)

    for laser_row, laser_col in find_pos(s, "<"):
        lasers.append((laser_row, laser_col, "h"))

    for laser_row, laser_col in find_pos(s, ">"):
        lasers.append((laser_row, laser_col, "l"))

    for laser_row, laser_col in find_pos(s, "^"):
        lasers.append((laser_row, laser_col, "k"))

    for laser_row, laser_col in find_pos(s, "v"):
        lasers.append((laser_row, laser_col, "j"))

    for laser_row, laser_col, dir in lasers:
        next_row, next_col = next_pos(laser_row, laser_col, dir)
        while True:
            # stop when going out of bounds
            if not in_bounds(height=height, width=width, row= next_row, col=next_col):
                break

            # laser beams cross each other
            elif at_pos(s, next_row, next_col) in "-" and dir in "jk":
                set_at_pos(s, next_row, next_col, "+")

            elif at_pos(s, next_row, next_col) in "|" and dir in "hl":
                set_at_pos(s, next_row, next_col, "+")

            # player get hit
            elif at_pos(s, next_row, next_col) == "G":
                set_at_pos(s, next_row, next_col, "Y")
                break

            # laser hits obstacle
            elif at_pos(s, next_row, next_col) in "FmMwWY<>^v":
                break

            else:
                if dir in "hl":
                    set_at_pos(s, next_row, next_col, "-")
                elif dir in "jk":
                    set_at_pos(s, next_row, next_col, "|")

            next_row, next_col = next_pos(next_row, next_col, dir)

    return s


def move(s, dir):
    """move ram in dir on level state s;
    this is the core game logic"""

    # find the initial position of the ram
    height, width = bounds(s)
    p = find_pos(s, "G")
    if not p:
        if find_pos(s, "@"):
            return _victory
        elif find_pos(s, "Y"):
            return _defeated
        else:
            return _invalid
    row, col = p[0]
    # move until obstacle is reached
    while True:
        next_row, next_col = next_pos(row, col, dir)

        # reached level bounds => stop
        if not in_bounds(height, width, next_row, next_col):
            return _unfinished
        c = at_pos(s, next_row, next_col)
        # empty field => move through
        if c in " _.":
            set_at_pos(s, next_row, next_col, "G")
            set_at_pos(s, row, col, ".")
            row, col = next_row, next_col
        # wall => damage it and stop
        elif c in "M":
            set_at_pos(s, next_row, next_col, "m")
            return _unfinished
        # damaged wall => destroy it and stop
        elif c in "m":
            set_at_pos(s, next_row, next_col, "_")
            return _unfinished
        elif c in "v^<>":
            set_at_pos(s, next_row, next_col, "_")
            return _unfinished
        # finish flag => change to victory ram and stop
        elif c in "F":
            set_at_pos(s, row, col, "@")
            return _victory
        # trap => stop and die
        elif c in "x|-":
            set_at_pos(s, row, col, "Y")
            return _defeated
        # hole => stop and implicitly remove hole
        elif c in "o":
            set_at_pos(s, next_row, next_col, "G")
            set_at_pos(s, row, col, ".")
            return _unfinished
        # heavy weight => push it one field; remove it when it moves on a hole; destroy traps on its path
        elif c in "W":
            over_row, over_col = next_pos(next_row, next_col, dir)
            if not in_bounds(height, width, over_row, over_col):
                return _unfinished
            nc = at_pos(s, over_row, over_col)
            if nc in " _.x|-+":
                set_at_pos(s, over_row, over_col, "W")
                set_at_pos(s, next_row, next_col, "G")
                set_at_pos(s, row, col, ".")
            elif nc in "o":
                set_at_pos(s, over_row, over_col, "_")
                set_at_pos(s, next_row, next_col, "G")
                set_at_pos(s, row, col, ".")
            return determine_new_state(s)

        # heavy weight => push it until it reaches an obstacle; remove it when it moves on a hole; destroy traps on its path
        elif c in "w":
            row, col = next_row, next_col
            while True:
                next_row, next_col = next_pos(row, col, dir)
                if not in_bounds(height, width, next_row, next_col):
                    break
                nc = at_pos(s, next_row, next_col)
                if nc in " _.x|-+":
                    set_at_pos(s, row, col, " ")
                    set_at_pos(s, next_row, next_col, "w")
                    row, col = next_row, next_col
                elif nc in "o":
                    set_at_pos(s, row, col, " ")
                    set_at_pos(s, next_row, next_col, "_")
                    break
                else:
                    break
            return _unfinished
        else:
            eprint(f"invalid level character {c}")
            return _invalid

        determine_new_state(s)


def print_help():
    """print in game help"""
    print("press any of the following [hjkl] to move [left, down, up, right] (confirm your choice with return)")
    print("press [rU] to restart, u to undo, q to quit and ? to display this info (confirm your choice with return)")


def init():
    """parse the command line args"""
    parser = argparse.ArgumentParser(
        prog="ramk",
        description="Ram Knight the game",
        epilog=f"Use [hjkl] to move G. Reach F. Avoid x. Push w and W. Destroy M and m. Stop on o. Error codes "
               f"are: {_victory} victory, {_invalid} invalid input, {_unfinished} unfinished, {_defeated} defeated. "
               f"Good Luck. "
        )
    parser.add_argument("file",
                        type=str,
                        help="file containing the level")
    parser.add_argument("-e",
                        type=str,
                        help="string of commands to execute, only directional commands [hjkl] are allowed. Whitespace "
                             "is ignored.")
    parser.add_argument("-f",
                        type=str,
                        help="file containing commands to execute, only directional commands [hjkl] are allowed. "
                             "Whitespace is ignored.")
    parser.add_argument("-o",
                        type=str,
                        help="destination to store the final game state")
    parser.add_argument("-i",
                        action="store_true",
                        help="overwrite level file")
    parser.add_argument("-q",
                        action="store_true",
                        help="silence output")
    return parser.parse_args()

def eprint(m):
    """prints message m to standard error unless explicitly silenced"""
    if not quiet:
        print(m, file=sys.stderr)


def tear_down(s, args):
    """saves the level state according to args"""
    if args.o:
        with open(args.o, "w") as f:
            f.write(to_str(s))
    elif args.i:
        with open(args.file, "w") as f:
            f.write(to_str(s))
    elif not args.q and (args.e or args.f):
        print_state(s)

global quiet
if __name__ == '__main__':
    args = init()
    quiet = args.q
    s = load_file(args.file)
    # s = update_lasers(s)
    e_code = validate_state(s)

    if e_code != _unfinished:
        if not quiet:
            print_state(s)
        exit(e_code)

    instr = ""
    if args.f:
        with open(args.f, "r") as f:
            instr = "".join(( l.strip() for l in f if l.strip() ))
    elif args.e:
        instr = args.e

    # non interactive mode
    if instr:
        for dir in instr:
            if dir in " \t\n":
                continue
            if dir not in "hjkl":
                eprint(f"invalid input {dir}")
                exit(_invalid)
            e_code = move(s, dir)
            if e_code != _unfinished:
                break
        tear_down(s, args)
        exit(e_code)

    state_history = [deepcopy(s)]
    command_history = ""
    # interactive mode
    print_state(s)
    while True:
        dirs = input("input [hjkl?qru]: ")
        if not dirs:
            continue
        for d in dirs:
            if d in "hjkl":
                e_code = move(s, d)
                s = update_lasers(s)
                state_history.append(deepcopy(s))
                command_history = command_history + d
            elif d == "q":
                tear_down(s, args)
                exit(e_code)
            elif d in "rU":
                s = load_file(args.file)
                state_history = [ deepcopy(s) ]
                command_history = ""
            elif d == "u":
                if command_history:
                    del state_history[-1]
                    command_history = command_history[:-1]
                    s = state_history[-1]
            else:
                print_help()
            print("-" * len(s[0]))
            print_state(s)
            print(" > " + command_history)
            print("-" * len(s[0]))
