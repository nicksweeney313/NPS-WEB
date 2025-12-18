$pdf_mode = 1;
$interaction = 'nonstopmode';

# Put aux files in cv/build, keep PDF in cv/
$aux_dir = 'build';
$out_dir = '.';

# Use biber for biblatex (NOT bibtex)
$biber = 'biber';
$bibtex_use = 2;

# After a successful build, copy PDF to site/assets
$success_cmd = 'mkdir -p ../site/assets && cp -f main.pdf ../site/assets/cv.pdf';
