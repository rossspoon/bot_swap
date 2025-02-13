#! /bin/bash

echo "###"
echo "###"
echo "### Preparing Latex"
echo "###"

# ensure that the temp and output directories exist and are empty
[ -d Presentation/temp ] || mkdir Presentation/temp
rm -rf Presentation/temp/*

[ -d Presentation/input ] || mkdir Presentation/input
rm -rf Presentation/input/*


[ -d Presentation/output ] || mkdir Presentation/output
rm -f Presentation/output/*

#export PYTHONPATH='Analysis/code'

# Copy
cp -R Analysis/output/* Presentation/temp/

[ -d Presentation/input/data ] || mkdir Presentation/input/data
rm -f Presentation/input/data/*
cp -R Analysis/input/* Presentation/input/data



echo "###"
echo "###"
echo "###  Generating PDF"
echo "###"

#Generate PDF
if  type "pdflatex" &> /dev/null;
then
    echo "## Presenting stats for individual sessions"
    python Presentation/code/session_summary.py

    base='session_summary_'
    for FILE in Presentation/temp/$base*
    do
        echo $FILE
        (cd Presentation/temp; pdflatex --halt-on-error $(basename $FILE) > pdflatex.out)
    done    
    
    
    echo "## Presening all session stats"
    cp Presentation/template/session_summary_all.tex Presentation/temp
    (cd Presentation/temp; pdflatex --halt-on-error session_summary_all.tex > sess_summary_all.out)

else
    echo "Skipping PDF.  Please install pdflatex"
fi

# Copy to output
mv Presentation/temp/*.pdf Presentation/output/
