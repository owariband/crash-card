# B 树与 B+ 树 · 来源

- M1 · [MySQL 8.4 — Glossary / B-tree](https://dev.mysql.com/doc/refman/8.4/en/glossary.html)：官方B-tree术语是一类索引设计的泛称。

- M2 · [CMU 15-445/645 (2024) — Indexes & Filters I](https://15445.courses.cs.cmu.edu/fall2024/notes/08-indexes1.pdf)：B/B+载荷位置、同深叶层、叶链、分裂和维护成本。

- M3 · [Dave Mount (2019) — B Trees](https://www.cs.umd.edu/class/fall2019/cmsc420-0201/Lects/slides-09-btree.pdf)：B树内部命中后结束；B+紧凑内部条目与范围访问。

- M4 · [MySQL 8.4 — Physical Structure of an InnoDB Index](https://dev.mysql.com/doc/refman/8.4/en/innodb-physical-structure.html)：索引页、默认16KB、叶记录、分裂和合并；普通索引范围。

- M5 · [MySQL 8.4 — Buffer Pool](https://dev.mysql.com/doc/refman/8.4/en/innodb-buffer-pool.html)：索引页可在缓冲池命中，树高不等于磁盘读取次数。

- M6 · [MySQL mysql-8.4.0 — btr0btr.cc](https://github.com/mysql/mysql-server/blob/mysql-8.4.0/storage/innobase/btr/btr0btr.cc)：Node pointers说明内部键前缀与子页号；叶页链接及物理连续的条件性。

- M7 · [MySQL 8.4 — Clustered and Secondary Indexes](https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html)：聚簇叶记录与二级记录包含聚簇键；非覆盖查询可能需聚簇访问。

## 单元与来源

- my-structure · 结构与页访问：M1、M2、M3、M4、M5、M6
- my-range · 追踪范围扫描：M2、M6、M7
- my-performance · 性能结论的边界：M2、M3、M4、M5、M7
