# 跨页后又遇到 24，接下来怎么查？

题目给出了相邻叶页的一段数据。先说清扫描路径、符合条件的记录和停止位置，再看第二张解答。

条件：20≤age<30，不去重，假定采用 age 二级索引。只讨论索引键扫描；题面片段不代表完整查询结果。背景为 MySQL 8.4 InnoDB。

#MySQL #数据库索引 #B树 #B加树 #面试复习

## 参考资料

- [CMU 15-445/645 (2024) — Indexes & Filters I](https://15445.courses.cs.cmu.edu/fall2024/notes/08-indexes1.pdf)
- [MySQL mysql-8.4.0 — btr0btr.cc](https://github.com/mysql/mysql-server/blob/mysql-8.4.0/storage/innobase/btr/btr0btr.cc)
- [MySQL 8.4 — Clustered and Secondary Indexes](https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html)
