"""
A placeholder in the IGC-Adjud data is in the format: Initial-gender-case, such as "V-kk-þgf". Foreign names are represented as "C-x-x M. P-x-x".
This script matches all the most common combinations of single names, first+lastname, first+abbrev+lastname etc. and replaces them with randomly chosen names in the corresponding gender and case. Abbreviations (such as H. in "Jón H. Jónsson") are left as is. Foreign names are not declined.
This works on sentence level, independent of tokenization, and doesn't respect entity resolution (different names every time).
""" 

import re
from islenska import Bin
import random
from pathlib import Path


b = Bin()


def sort_common_names(common_names):
    # We're only using the ~500 most common first names in Iceland as determined by Hagstofan (used as names in BÍN can be very archaic). Here we sort them into male and female names using BÍN.
    kk_list = [] 
    kvk_list = []
    names = [b.lookup(i.strip())[1] for i in common_names if b.lookup(i)]
    for name in names:
        try:
            name[0].hluti == "ism"
            if name[0].ofl == "kk":
                kk_list.append(name[0].ord)
            elif name[0].ofl == "kvk":
                kvk_list.append(name[0].ord)
        except:
            pass
    return (kk_list, kvk_list)


kk_first_names = []
kvk_first_names = []
kk_last_names = []
kvk_last_names = []
kk_foreign_names = []
kvk_foreign_names = []
foreign_last_names = []
def load_names():

    global kk_first_names
    global kvk_first_names
    global kk_last_names
    global kvk_last_names
    global kk_foreign_names
    global kvk_foreign_names
    global foreign_last_names

    names_dir = Path("names/")
    kk_lastnames_p = names_dir / "is_kk_lastnames.txt"
    kvk_lastnames_p = names_dir / "is_kvk_lastnames.txt"
    kk_foreign_p = names_dir / "foreign_kk_firstnames.txt"
    kvk_foreign_p = names_dir / "foreign_kvk_firstnames.txt"
    foreign_lastnames_p = names_dir / "foreign_lastnames.txt"
    is_first_names_common_p = names_dir / "common_is_firstnames.txt"

    with open(kk_lastnames_p) as kk_lastnames, \
            open(kvk_lastnames_p) as kvk_lastnames, \
            open(kk_foreign_p) as kk_foreign, \
            open(kvk_foreign_p) as kvk_foreign, \
            open(foreign_lastnames_p) as foreign_lastnames, \
            open(is_first_names_common_p) as is_first_names_common:

        kk_last_names = [i.strip() for i in kk_lastnames]
        kvk_last_names = [i.strip() for i in kvk_lastnames]
        kk_foreign_names = [i.strip() for i in kk_foreign]
        kvk_foreign_names = [i.strip() for i in kvk_foreign]
        foreign_last_names = [i.strip() for i in foreign_lastnames]
        common_first_names = [i.strip() for i in is_first_names_common]

    kk_first_names, kvk_first_names = sort_common_names(common_first_names)

load_names()


def get_random_name(gender, is_last):
    """very gender-binary random name generator for first and last names. """

    if gender == "kk":
        if is_last:
            return random.choice(kk_last_names)
        return random.choice(kk_first_names)
    if gender == "kvk":
        if is_last:
            return random.choice(kvk_last_names)
        return random.choice(kvk_first_names)
    
    elif is_last:
        return random.choice(foreign_last_names)
    else:
        return random.choice(kvk_foreign_names + kk_foreign_names)


def inflect_name(gender, case, is_last):
    name = get_random_name(gender, is_last)
    try:
        return b.lookup_variants(name, cat="no", to_inflection=case)[0].bmynd
    except:
        return name


def placeholder_to_inflected_name(placeholder):
    ph_list = placeholder.split()
    initial, gender, case = ph_list[0].split("-")
    if len(ph_list) > 1:
        first, middle, last = ph_list[0], ph_list[1:-1], ph_list[-1] 
        name_list = []
        name_list.append(inflect_name(gender, case, False))
        if len(middle) > 0:
            for n in middle:
                if len(n) < 4:
                    name_list.append(n)
                else:
                    name_list.append(inflect_name(gender, case, False))

        name_list.append(inflect_name(gender, case, True))
        return " ".join(name_list)
        #initial, gender, case=ph_list[0].split("-")
        #initial, gender, case = i.split("-")

    elif len(ph_list) == 1:
        #initial, gender, case = ph_list[0].split("-")
        return inflect_name(gender, case, False)

    else:
        return placeholder


def replace_name_placeholders(line):
    """ Find and replace the name placeholders in a line """
    # regex monster for finding the different name patterns
    placeholder_pattern =r"[A-ZÁÆÖÝÓÚÉÍÞ](-[\wáæöýéíúþð]{1,3}){2}(( [\wÁÆÖÝÓÚÉÍÞ+]\.){0,2} [A-ZÁÆÖÝÓÚÉÍÞ](-[\wáæöýéíúþð]{1,3}){2}){0,2}"

    match = re.search(placeholder_pattern, line)
    if match:
        edited_line = line.replace(match.group(0), placeholder_to_inflected_name(match.group(0))).strip()
        while re.search(placeholder_pattern, edited_line):
            match = re.search(placeholder_pattern, edited_line)
            new_line = edited_line.replace(match.group(0), placeholder_to_inflected_name(match.group(0))).strip()
            edited_line = new_line
        return edited_line
    else:
        return line.strip()


if __name__ == "__main__":
    testdata = "Varnaraðilar, A-x-x S-x-x B-x-x, C-x-x M. P-x-x, Ó-kk-nf P-kk-nf, R-x-x D-x-x S-x-x, B-kvk-nf H-kvk-nf K-kvk-nf, B-kk-nf Þ-kk-nf H-kk-nf og G-kk-nf V-kk-nf G-kk-nf, greiði óskipt sóknaraðilum, A-kk-þgf V-kk-þgf, B-kvk-þgf G-kvk-þgf, C-x-x W-x-x, D-kk-þgf K-kk-þgf, E-kk-þgf M-kk-þgf A-kk-þgf, G-kk-þgf V-kk-þgf, G-kvk-þgf E-kvk-þgf G-kvk-þgf, H-kk-þgf H-kk-þgf, J-kk-þgf S-kk-þgf S-kk-þgf, J-x-x S-x-x, M-kvk-þgf B-kvk-þgf S-kvk-þgf, M-kk-þgf E. M-kk-þgf, P-kk-þgf Þ-kk-þgf S-kk-þgf, R-kk-þgf S-kk-þgf, S-kk-þgf K-kk-þgf, S-kk-þgf Á-kk-þgf L-kk-þgf og M-kk-þgf S-kk-þgf, N-x-x, hverju um sig 30.000 krónur í kærumálskostnað."
    print(replace_name_placeholders(testdata))

