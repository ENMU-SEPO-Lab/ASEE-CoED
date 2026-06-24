# ASEE-CoED
Paper submission for a special issue with ASEE Computers and Education (ASEE CoED).


To prepare the pipeline for submissions for a new assignment you need to:
    - rename the submission folder to the desired assignment id, e.g. PA02
    - make sure that you also update the dir name in the .yml script, there are 2 occurrences at the very top
    - make sure the file name of the submission matches what the unit test file expects, otherwise it will fail
    - to run the automated shell script file for multiple submissions within an assignment:
        - inside the script, modify the line where the filename for the submission is specified (line 14)
        - then, run:
            chmod +x submit.sh
            ./submit.sh
