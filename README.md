## drive cleaner

1. get duplicate md5 files sorted by size
2. some options
- group by the md5, filesize - we get duplicates
- find the most common folder 


for each duplicate group we need to decide
- first find the policy and preference from the user

the situations are:
- in a single folder, there are many duplicates
    - keep the simplest one aka lesser chars? or base name like eagle.pdf and eagle (1).pdf
- contents are duplicated in A and B
    - find the best described folder

how to rank the folders?
- how much perc of the files are duplicated in the folder
- if 100% of the files are duplicated, then we should probably keep it ?? (self isolated and grouped)

what options to do when choosing b/w folders?
- keep contents from folder A and delete from B
- ignore the suggestions and keep both
- merge the fodlers 
