#!/usr/bin/env bash
set -euo pipefail

test_dir='test_dir'


odd_names() (
    echo "create ${FUNCNAME[0]}"
    d="${FUNCNAME[0]}"
    mkdir "$d" && cd "$d"
    touch '.' #TODO. Create nothing, because dir with such filename already exist.
    touch '..' #TODO. Create nothing, because dir with such filename already exist.
    touch '.file_hidden_nix'
    touch $'\nfile_newline_at_begin'
)


ascii_names() (
    echo "create ${FUNCNAME[0]}"
    d="${FUNCNAME[0]}"
    mkdir "$d" && cd "$d"
    # all ASCII symbols
    for i in $(seq 1 255); do
        printf -v val %o "$i" # dec to oct
        printf -v name  '%b' "\\$val"
        if [[ $name == '/' ]]; then
            continue
        fi
        touch "$name"
    done
)


utf8_names() (
    echo "create ${FUNCNAME[0]}"
    d="${FUNCNAME[0]}"
    mkdir "$d" && cd "$d"
    # from https://github.com/noct/cutf/tree/master/bin and http://www.madore.org/~david/misc/unitest/
    touch '∀x∈ℝ: ⌈x⌉ = −⌊−x⌋, α ∧ ¬β = ¬(¬α ∨ β)'
    touch '((V⍳V)=⍳⍴V)V←,V    ⌷←⍳→⍴∆∇⊃‾⍎⍕⌈'
    touch 'Σὲ γνωρίζω ἀπὸ τὴν κόψη' # Greek
    touch 'გთხოვთ ახლავე გაიაროთ რეგისტრაცია Unicode-ის მეათე საერთაშორისო' # Georgian
    touch 'Зарегистрируйтесь сейчас на Десятую Международную Конференцию' # Russian
    touch 'ภาษาไทย' # Thai
    touch 'ሰማይ አይታረስ ንጉሥ አይከሰስ።' # Amharic
    touch 'ᚻᛖ ᚳᚹᚫᚦ ᚦᚫᛏ ᚻᛖ ᛒᚢᛞᛖ ᚩᚾ ᚦᚫᛗ ᛚᚪᚾᛞᛖ ᚾᚩᚱᚦᚹᛖᚪᚱᛞᚢᛗ ᚹᛁᚦ ᚦᚪ ᚹᛖᛥᚫ' # Runes
    touch '⡌⠁⠧⠑ ⠼⠁⠒  ⡍⠜⠇⠑⠹⠰⠎ ⡣⠕⠌' # Braille
    touch '∀∂∈ℝ∧∪≡∞ ↑↗↨↻⇣ ┐┼╔╘░►☺♀ ﬁ�⑀₂ἠḂӥẄɐː⍎אԱა'
    touch '▁▂▃▄▅▆▇█'
    touch '♈'
    touch '♜♞♝♛♚♝♞♜'
    touch 'पशुपतिरपि तान्यहानि कृच्छ्राद्' # Sanskrit
    touch '子曰：「學而時習之，不亦說乎？有朋自遠方來，不亦樂乎？' # Chinese
    touch 'ஸ்றீனிவாஸ ராமானுஜன் ஐயங்கார்' # Tamil
    touch 'بِسْمِ ٱللّٰهِ ٱلرَّحْمـَبنِ ٱلرَّحِيمِ' # Arabic
    touch '😀' # emoji face
    touch '🧠' # emoji heart
    touch '🇸🇨' # Seychelles flag

    # Sequence of continuation bytes (0x80-0x9F)
    n=''
    for i in $(seq 128 159); do
        n="$n\u$i"
    done
    printf -v n '%b' "$n"
    echo "n=$n"
    touch "$n"
)


win_reserved_names() (
    # https://learn.microsoft.com/ru-ru/windows/win32/fileio/naming-a-file
    echo "create ${FUNCNAME[0]}"
    d="${FUNCNAME[0]}"
    mkdir "$d" && cd "$d"
    touch 'CON' 'PRN' 'AUX' 'NUL'
    for i in $(seq 9); do
        touch "COM$i" "LPT$i"
    done
    touch "end_with_space "
    touch "end_with_dot."
)


long_name() (
    # most filesystems have max name length 255 bytes : https://en.wikipedia.org/wiki/Comparison_of_file_systems#Limits
    echo "create ${FUNCNAME[0]}"
    d="${FUNCNAME[0]}"
    mkdir "$d" && cd "$d"
    name='n'
    for i in $(seq 8); do
        name="$name$name"
    done
    mkdir "${name::-1}" # remove last symbol to make 255 symbols instead of 256
)


deep_hierarchy() (
    echo "create ${FUNCNAME[0]}"
    MAX_LEVEL=200 # arbitrary. ext4 seems have no limits, I can create hierarchy with >700 levels. PATH_MAX=4096 seemsnot a real restriction.
    d="${FUNCNAME[0]}"
    mkdir "$d" && cd "$d"
    level=1
    while ((level < MAX_LEVEL)); do
        d="n${level}"
        level=$((level+1))
        mkdir "$d" || break
        cd "$d"
    done
    echo "hierarchy level = ${level}"
)


big_file() (
    echo "create ${FUNCNAME[0]} $1M"
    d="${FUNCNAME[0]}_$1"
    mkdir "$d" && cd "$d"
    dd bs=1M count="$1" if=/dev/urandom of="file_$1M"
)


big_dir() (
    echo "create ${FUNCNAME[0]} $1 files"
    d="${FUNCNAME[0]}_$1"
    mkdir "$d" && cd "$d"
    for i in $(seq "$1"); do
        touch "file_$i"
    done
)


mkdir "${test_dir}" && cd "${test_dir}"

odd_names
ascii_names
utf8_names
win_reserved_names
long_name
deep_hierarchy
big_dir 501  #create dir with 501 files (see https://windowsreport.com/google-drive-zip-failed/)
big_dir 4100
big_file 100 # create dir with 100M file inside
big_file 2100


