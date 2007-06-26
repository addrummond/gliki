# Compile all cheetah templates in templates/
for f in templates/*.tmpl; do
    cheetah compile $f
done

