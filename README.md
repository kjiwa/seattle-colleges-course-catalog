# Seattle Colleges Course Catalog

This script extracts courses from the Central, North, and South Seattle College class schedules and exports them to CSV. The script works by using Selenium WebDriver to interact with each college's class schedule application, expanding each department and course description. The class schedules links that the script reads from are:

* Central Seattle College: https://mycentral.seattlecolleges.edu/
* North Seattle College: https://mynorth.seattlecolleges.edu/
* South Seattle College: https://mysouth.seattlecolleges.edu/

Seattle Vocational Institute is not currently supported.

Each department's course list is analyzed for course codes, names, credits, tags, and prerequisites. The CSV has the following format:

* College
* Department
* Course Code
* Course Name
* Credits
* Tags
* Prerequisites

For example, the raw CSV may have data such as the following:

```
College,Department,Code,Name,Credits,Tags,Prerequisites
Central,ART,251,Art History-Is,5.0,"eL,VLPA,IS",
Central,ART,253,Western Art Survey Iii,5.0,"VLPA,IS",ENGL&101
North,ECE,420,Social and Emotional Foundations Early Learning,5.0,N,
North,ECE,430,Linguistically Diverse Learners,5.0,N,
South,TDR,121,Drafting Technology I,4.0,,TDR131
South,TDR,123,Drafting Technology Ii,4.0,,TDR121
```

As a table, this data has this appearance:

| College | Department | Code | Name | Credits | Tags | Prerequisites |
| ------- | ---------- | ---- | ---- | ------- | ---- | ------------- |
| Central | ART | 251 | Art History-Is | 5.0 | eL,VLPA,IS | |
| Central | ART | 253 | Western Art Survey Iii | 5.0 | VLPA,IS | ENGL&101 |
| North | ECE | 420 | Social and Emotional Foundations Early Learning | 5.0 | N | |
| North | ECE | 430 | Linguistically Diverse Learnings | 5.0 | N | |
| South | TDR | 121 | Drafting Technology I | 4.0 | | TDR131 |
| South | TDR | 122 | Drafting Technology Ii | 4.0 | | TDR121 |

The [output](sccourses.csv) has been uploaded for those not able or not interested in running the script.
