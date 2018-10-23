Need to run the following SQL when migrating your local DB to the new name:

```sql
UPDATE django_migrations SET app = REPLACE(app, 'lsoa', 'kidviz') WHERE app = 'lsoa';

UPDATE django_content_type SET app_label = REPLACE(app_label, 'lsoa', 'kidviz') WHERE app_label = 'lsoa';

ALTER TABLE lsoa_contexttag RENAME TO kidviz_contexttag;
ALTER TABLE lsoa_course_students RENAME TO kidviz_course_students;
ALTER TABLE lsoa_course RENAME TO kidviz_course;
ALTER TABLE lsoa_learningconstructsublevel RENAME TO kidviz_learningconstructsublevel;
ALTER TABLE lsoa_studentgrouping RENAME TO kidviz_studentgrouping;
ALTER TABLE lsoa_learningconstructsublevelexample RENAME TO kidviz_learningconstructsublevelexample;
ALTER TABLE lsoa_observation_students RENAME TO kidviz_observation_students;
ALTER TABLE lsoa_observation_tags RENAME TO kidviz_observation_tags;
ALTER TABLE lsoa_studentgroup RENAME TO kidviz_studentgroup;
ALTER TABLE lsoa_studentgroup_students RENAME TO kidviz_studentgroup_students;
ALTER TABLE lsoa_studentgrouping_groups RENAME TO kidviz_studentgrouping_groups;
ALTER TABLE lsoa_observation_constructs RENAME TO kidviz_observation_constructs;
ALTER TABLE lsoa_learningconstruct RENAME TO kidviz_learningconstruct;
ALTER TABLE lsoa_learningconstructlevel RENAME TO kidviz_learningconstructlevel;
ALTER TABLE lsoa_student RENAME TO kidviz_student;
ALTER TABLE lsoa_observation RENAME TO kidviz_observation;


```
