reset
set encoding utf8
set terminal pngcairo size 2000,1000

set output 'time.png'
set size 1,1
set ylabel "Duration"
set xlabel "Number of documents (same corpus)"
set format x "%5.0s %c"
set format y "%5.3s %cs"
set key below box
plot "benchmark-add_document-1000-old.dat" u 2 t "old" linecolor rgb "#FF0000" w lines, \
     "benchmark-add_document-1000-new.dat" u 2 t "new" linecolor rgb "#0000FF" w lines
