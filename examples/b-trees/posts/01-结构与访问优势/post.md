# B 树与 B+ 树，差别如何影响查询？

先看记录载荷放在哪里，再把结构差异连到页容量、扇出和范围扫描。两张图讲清这条因果链，也保留性能比较的前提。

这里讨论教科书 B/B+ 树与 MySQL 8.4 InnoDB 普通 BTREE 索引；不能推广成所有 MySQL 索引都采用同一种结构。

#MySQL #数据库索引 #B树 #B加树 #面试复习

## 参考资料

- [CMU 15-445/645 (2024) — Indexes & Filters I](https://15445.courses.cs.cmu.edu/fall2024/notes/08-indexes1.pdf)
- [Dave Mount (2019) — B Trees](https://www.cs.umd.edu/class/fall2019/cmsc420-0201/Lects/slides-09-btree.pdf)
- [MySQL 8.4 — Physical Structure of an InnoDB Index](https://dev.mysql.com/doc/refman/8.4/en/innodb-physical-structure.html)
- [MySQL mysql-8.4.0 — btr0btr.cc](https://github.com/mysql/mysql-server/blob/mysql-8.4.0/storage/innobase/btr/btr0btr.cc)
