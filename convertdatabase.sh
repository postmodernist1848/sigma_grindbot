database_dir=database.d

[[ -e $database_dir ]] || mkdir $database_dir

while read p; do
    filename=$(echo $p | cut -d' ' -f1)
    data=$(echo $p | cut -d' ' -f2)

    echo $data > $database_dir/$filename

done <$1

